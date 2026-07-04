import json
import asyncio
import aiohttp
from config import OPENCODE_API_KEY, OPENCODE_API_KEY_BACKUP, OPENCODE_AUX_KEY, OPENCODE_BASE_URL, FREE_MODELS


def _get_or_create_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    return loop


class AIClient:
    def __init__(self):
        self.api_keys = [k for k in [OPENCODE_API_KEY, OPENCODE_API_KEY_BACKUP, OPENCODE_AUX_KEY] if k]
        self.current_key_idx = 0
        self.base_url = OPENCODE_BASE_URL
        self.model = FREE_MODELS[0]
        self._model_idx = 0

    @property
    def api_key(self):
        if not self.api_keys:
            return ""
        return self.api_keys[self.current_key_idx % len(self.api_keys)]

    def rotate_key(self):
        self.current_key_idx += 1

    def next_model(self):
        self._model_idx = (self._model_idx + 1) % len(FREE_MODELS)
        self.model = FREE_MODELS[self._model_idx]

    async def chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }
        last_error = None
        for attempt in range(len(self.api_keys) * len(FREE_MODELS)):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data["choices"][0]["message"]["content"]
                        elif resp.status == 429:
                            self.rotate_key()
                            headers["Authorization"] = f"Bearer {self.api_key}"
                            continue
                        elif resp.status == 401:
                            self.rotate_key()
                            headers["Authorization"] = f"Bearer {self.api_key}"
                            continue
                        else:
                            text = await resp.text()
                            last_error = f"API error {resp.status}: {text}"
                            self.next_model()
                            payload["model"] = self.model
                            continue
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = str(e)
                if attempt % 3 == 2:
                    self.rotate_key()
                    headers["Authorization"] = f"Bearer {self.api_key}"
                continue
        raise Exception(f"All models/keys exhausted. Last error: {last_error}")

    async def classify_tasks(self, tasks: list[str]) -> dict:
        prompt = f"""Analyze these tasks and classify each one. Return ONLY valid JSON, no extra text.

Tasks:
{json.dumps(tasks, indent=2)}

Return this exact JSON structure:
{{
  "classified_tasks": [
    {{
      "task": "original task text",
      "category": "work|health|learning|personal|creative",
      "priority": "high|medium|low",
      "estimated_minutes": 30,
      "best_time": "morning|afternoon|evening",
      "dependencies": [],
      "suggestion": "brief tip"
    }}
  ],
  "daily_plan": "brief summary",
  "motivation": "motivational message"
}}"""
        messages = [
            {"role": "system", "content": "You are a productivity assistant. Return only valid JSON, no markdown."},
            {"role": "user", "content": prompt},
        ]
        result = await self.chat(messages, temperature=0.3)
        result = result.strip()
        if "```" in result:
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()
        return json.loads(result)

    async def generate_reminder(self, task: str, progress: float, current_activity: str = "") -> str:
        ctx = f"User is currently: {current_activity}" if current_activity else ""
        prompt = f"""Generate a short, friendly reminder about this task. Be encouraging, not nagging.
Task: {task}
Progress: {progress*100:.0f}%
{ctx}
Keep it under 15 words. Be warm and motivating."""
        messages = [
            {"role": "system", "content": "You are Pinchu, a friendly productivity companion."},
            {"role": "user", "content": prompt},
        ]
        return await self.chat(messages, temperature=0.8)

    async def generate_daily_summary(self, completed: list, missed: list, partial: list) -> dict:
        prompt = f"""Summarize this day's productivity. Return ONLY valid JSON.

Completed: {json.dumps(completed)}
Missed: {json.dumps(missed)}
Partially done: {json.dumps(partial)}

Return:
{{
  "score": 0-100,
  "summary": "one paragraph",
  "highlights": ["top 3 achievements"],
  "tomorrow_focus": ["suggested priorities"],
  "motivation": "end of day message"
}}"""
        messages = [
            {"role": "system", "content": "You are a productivity analyst. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ]
        result = await self.chat(messages, temperature=0.4)
        result = result.strip()
        if "```" in result:
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()
        return json.loads(result)

    async def generate_motivation(self, activity: str, task: str) -> str:
        prompt = f"""The user is doing: {activity}
Their task is: {task}
Generate a short motivational message (under 20 words). Be specific."""
        messages = [
            {"role": "system", "content": "You are Pinchu, a cheerful productivity companion."},
            {"role": "user", "content": prompt},
        ]
        return await self.chat(messages, temperature=0.9)

    async def chat_conversational(self, user_message: str, context: str = "") -> str:
        system = "You are Pinchu, a friendly desktop productivity companion. Be warm, concise, and helpful. Max 3 sentences."
        if context:
            system += f"\nContext: {context}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, temperature=0.7)
