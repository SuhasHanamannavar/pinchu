import json
from datetime import datetime, timedelta
from pathlib import Path
from config import DATA_DIR


CONTEXT_DIR = DATA_DIR / "context"
CONTEXT_DIR.mkdir(exist_ok=True)


class SessionContext:
    def __init__(self):
        self._current_session = None
        self._session_file = CONTEXT_DIR / "current_session.json"
        self._history_dir = CONTEXT_DIR / "sessions"
        self._history_dir.mkdir(exist_ok=True)

    def start_session(self) -> dict:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        prev_context = self._load_previous_context()
        self._current_session = {
            "id": session_id,
            "started_at": datetime.now().isoformat(),
            "context_chain": prev_context.get("context_chain", []),
            "tasks_from_yesterday": prev_context.get("pending_tasks", []),
            "mood": "ready",
            "notes": [],
        }
        self._save_current()
        return self._current_session

    def add_context(self, text: str, source: str = "user"):
        if not self._current_session:
            self.start_session()
        self._current_session["context_chain"].append({
            "text": text,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_current()

    def add_note(self, note: str):
        if not self._current_session:
            self.start_session()
        self._current_session["notes"].append({
            "text": note,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_current()

    def get_context_for_ai(self, max_items: int = 20) -> str:
        if not self._current_session:
            self.start_session()
        lines = []
        yesterday_tasks = self._current_session.get("tasks_from_yesterday", [])
        if yesterday_tasks:
            lines.append("Yesterday's unfinished tasks:")
            for t in yesterday_tasks[:5]:
                lines.append(f"  - {t}")
            lines.append("")
        chain = self._current_session.get("context_chain", [])
        for item in chain[-max_items:]:
            source = item.get("source", "unknown")
            text = item.get("text", "")
            lines.append(f"[{source}] {text}")
        notes = self._current_session.get("notes", [])
        if notes:
            lines.append("")
            lines.append("Notes:")
            for n in notes[-5:]:
                lines.append(f"  - {n['text']}")
        return "\n".join(lines)

    def end_session(self):
        if not self._current_session:
            return
        self._current_session["ended_at"] = datetime.now().isoformat()
        pending = self._get_pending_tasks()
        self._current_session["pending_tasks"] = pending
        session_file = self._history_dir / f"{self._current_session['id']}.json"
        session_file.write_text(json.dumps(self._current_session, indent=2))
        self._session_file.write_text(json.dumps(self._current_session, indent=2))
        self._current_session = None

    def get_session_chain(self) -> list:
        sessions = []
        for f in sorted(self._history_dir.glob("*.json"), reverse=True)[:10]:
            session = json.loads(f.read_text())
            sessions.append({
                "id": session.get("id", ""),
                "started": session.get("started_at", "")[:10],
                "ended": session.get("ended_at", "")[:10],
                "context_count": len(session.get("context_chain", [])),
                "notes_count": len(session.get("notes", [])),
            })
        return sessions

    def _load_previous_context(self) -> dict:
        if self._session_file.exists():
            return json.loads(self._session_file.read_text())
        sessions = sorted(self._history_dir.glob("*.json"), reverse=True)
        if sessions:
            return json.loads(sessions[0].read_text())
        return {}

    def _get_pending_tasks(self) -> list:
        tasks_file = DATA_DIR / "tasks.json"
        if not tasks_file.exists():
            return []
        tasks = json.loads(tasks_file.read_text())
        today = datetime.now().strftime("%Y-%m-%d")
        day_data = tasks.get("days", {}).get(today, {})
        classified = day_data.get("classified") or {}
        tasks_list = classified.get("classified_tasks", [])
        status = day_data.get("task_status", {})
        pending = []
        for i, task in enumerate(tasks_list):
            if not status.get(str(i), {}).get("completed"):
                pending.append(task.get("task", ""))
        return pending

    def _save_current(self):
        if self._current_session:
            self._session_file.write_text(json.dumps(self._current_session, indent=2))
