import json
from datetime import datetime
from pathlib import Path
from config import DATA_DIR, COGNEE_API_KEY, COGNEE_API_BASE_URL


MEMORY_DIR = DATA_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)


class MemoryManager:
    def __init__(self):
        self._cognee = None
        self._initialized = False

    async def init_cognee(self):
        if self._initialized:
            return
        try:
            import cognee
            self._cognee = cognee
            if COGNEE_API_KEY and COGNEE_API_BASE_URL:
                cognee.config.set_api_key(COGNEE_API_KEY)
                cognee.config.set_api_base_url(COGNEE_API_BASE_URL)
            else:
                await cognee.configurator.add_graph_db_config({
                    "provider": "postgres",
                    "db_name": "pinchu_db",
                })
            self._initialized = True
        except Exception:
            self._initialized = False

    async def remember(self, text: str, metadata: dict = None):
        entry = {
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        day_file = MEMORY_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        entries = []
        if day_file.exists():
            entries = json.loads(day_file.read_text())
        entries.append(entry)
        day_file.write_text(json.dumps(entries, indent=2))

        if self._initialized and self._cognee:
            try:
                await self._cognee.remember(text)
            except Exception:
                pass

    async def recall(self, query: str, limit: int = 5) -> list:
        results = []
        if self._initialized and self._cognee:
            try:
                cognee_results = await self._cognee.recall(query)
                results.extend(cognee_results[:limit])
            except Exception:
                pass

        for day_file in sorted(MEMORY_DIR.glob("*.json"), reverse=True)[:7]:
            entries = json.loads(day_file.read_text())
            for e in entries:
                if query.lower() in e.get("text", "").lower():
                    results.append(e)
        return results[:limit]

    async def forget(self, dataset: str = None):
        if self._initialized and self._cognee:
            try:
                await self._cognee.forget(dataset=dataset)
            except Exception:
                pass

    async def improve(self):
        if self._initialized and self._cognee:
            try:
                await self._cognee.improve()
            except Exception:
                pass

    async def get_history(self, days: int = 30) -> list:
        history = []
        for day_file in sorted(MEMORY_DIR.glob("*.json"), reverse=True)[:days]:
            date_str = day_file.stem
            entries = json.loads(day_file.read_text())
            history.append({"date": date_str, "entries": entries})
        return history

    async def get_unfinished_tasks(self) -> list:
        tasks_file = DATA_DIR.parent / "tasks.json"
        if not tasks_file.exists():
            return []
        tasks = json.loads(tasks_file.read_text())
        unfinished = []
        for day_data in sorted(MEMORY_DIR.glob("*.json"), reverse=True)[:3]:
            entries = json.loads(day_data.read_text())
            for e in entries:
                meta = e.get("metadata", {})
                if meta.get("type") == "task" and not meta.get("completed"):
                    unfinished.append(e)
        return unfinished
