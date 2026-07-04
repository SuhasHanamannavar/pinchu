import json
from datetime import datetime, timedelta
from pathlib import Path
from config import TASKS_FILE, DAILY_SUMMARIES


class TaskManager:
    def __init__(self):
        self.tasks = self._load()

    def _load(self) -> dict:
        if TASKS_FILE.exists():
            return json.loads(TASKS_FILE.read_text())
        return {"days": {}, "current_day": ""}

    def _save(self):
        TASKS_FILE.write_text(json.dumps(self.tasks, indent=2))

    def get_today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def set_today_tasks(self, raw_input: str):
        day = self.get_today()
        self.tasks["current_day"] = day
        self.tasks["days"][day] = {
            "raw_input": raw_input,
            "classified": None,
            "task_status": {},
            "created_at": datetime.now().isoformat(),
        }
        self._save()

    def set_classified_tasks(self, classified: dict):
        day = self.get_today()
        if day not in self.tasks["days"]:
            self.tasks["days"][day] = {"raw_input": "", "classified": None, "task_status": {}, "created_at": datetime.now().isoformat()}
        self.tasks["days"][day]["classified"] = classified
        for i, task in enumerate(classified.get("classified_tasks", [])):
            key = str(i)
            if key not in self.tasks["days"][day]["task_status"]:
                self.tasks["days"][day]["task_status"][key] = {
                    "completed": False,
                    "progress": 0.0,
                    "started_at": None,
                    "completed_at": None,
                }
        self._save()

    def get_today_tasks(self) -> dict:
        day = self.get_today()
        return self.tasks["days"].get(day, {})

    def mark_task_progress(self, task_idx: str, progress: float):
        day = self.get_today()
        if day in self.tasks["days"]:
            status = self.tasks["days"][day]["task_status"]
            if task_idx in status:
                status[task_idx]["progress"] = min(1.0, progress)
                if status[task_idx]["started_at"] is None:
                    status[task_idx]["started_at"] = datetime.now().isoformat()
                if progress >= 1.0:
                    status[task_idx]["completed"] = True
                    status[task_idx]["completed_at"] = datetime.now().isoformat()
                self._save()

    def complete_task(self, task_idx: str):
        self.mark_task_progress(task_idx, 1.0)

    def get_completed_tasks(self) -> list:
        day = self.get_today()
        data = self.tasks["days"].get(day, {})
        classified = data.get("classified") or {}
        status = data.get("task_status", {})
        completed = []
        for i, task in enumerate(classified.get("classified_tasks", [])):
            if status.get(str(i), {}).get("completed"):
                completed.append(task["task"])
        return completed

    def get_pending_tasks(self) -> list:
        day = self.get_today()
        data = self.tasks["days"].get(day, {})
        classified = data.get("classified") or {}
        status = data.get("task_status", {})
        pending = []
        for i, task in enumerate(classified.get("classified_tasks", [])):
            if not status.get(str(i), {}).get("completed"):
                pending.append({**task, "index": i, "progress": status.get(str(i), {}).get("progress", 0)})
        return pending

    def get_incomplete_yesterday(self) -> list:
        today = datetime.now()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        data = self.tasks["days"].get(yesterday, {})
        classified = data.get("classified") or {}
        status = data.get("task_status", {})
        incomplete = []
        for i, task in enumerate(classified.get("classified_tasks", [])):
            if not status.get(str(i), {}).get("completed"):
                incomplete.append(task["task"])
        return incomplete

    def save_daily_summary(self, summary: dict):
        day = self.get_today()
        if DAILY_SUMMARIES.exists():
            summaries = json.loads(DAILY_SUMMARIES.read_text())
        else:
            summaries = {}
        summaries[day] = summary
        DAILY_SUMMARIES.write_text(json.dumps(summaries, indent=2))

    def get_week_stats(self) -> dict:
        stats = {}
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            data = self.tasks["days"].get(day, {})
            classified = data.get("classified") or {}
            status = data.get("task_status", {})
            total = len(classified.get("classified_tasks", []))
            done = sum(1 for k, v in status.items() if v.get("completed"))
            stats[day] = {"total": total, "completed": done}
        return stats
