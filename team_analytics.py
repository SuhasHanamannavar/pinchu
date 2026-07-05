import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config import DATA_DIR


class TeamAnalytics:
    def __init__(self):
        self._team_file = DATA_DIR / "team_data.json"
        self._data: dict = {"members": {}, "shared_memory": [], "stats": {}}
        self._load()

    def _load(self):
        if self._team_file.exists():
            try:
                self._data = json.loads(self._team_file.read_text())
            except Exception:
                pass

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._team_file.write_text(json.dumps(self._data, indent=2))

    def add_member(self, user_id: str, name: str, role: str = "member"):
        self._data["members"][user_id] = {
            "name": name,
            "role": role,
            "joined_at": datetime.now().isoformat(),
            "tasks_completed": 0,
            "tasks_assigned": 0,
            "activity_minutes": 0,
            "memory_shared": 0,
            "last_active": None,
        }
        self._save()

    def remove_member(self, user_id: str):
        self._data["members"].pop(user_id, None)
        self._save()

    def log_member_activity(self, user_id: str, activity_type: str, minutes: int):
        if user_id not in self._data["members"]:
            return
        member = self._data["members"][user_id]
        member["activity_minutes"] += minutes
        member["last_active"] = datetime.now().isoformat()
        self._save()

    def log_member_task(self, user_id: str, completed: bool = False):
        if user_id not in self._data["members"]:
            return
        member = self._data["members"][user_id]
        if completed:
            member["tasks_completed"] += 1
        member["tasks_assigned"] += 1
        self._save()

    def share_memory(self, user_id: str, content: str, metadata: dict = {}):
        entry = {
            "id": f"shared_{int(datetime.now().timestamp() * 1000)}",
            "user_id": user_id,
            "content": content,
            "metadata": metadata,
            "shared_at": datetime.now().isoformat(),
        }
        self._data["shared_memory"].append(entry)
        if user_id in self._data["members"]:
            self._data["members"][user_id]["memory_shared"] += 1
        self._save()
        return entry

    def get_team_stats(self) -> dict:
        members = self._data["members"]
        if not members:
            return {"member_count": 0, "total_tasks": 0, "total_activity_hours": 0}

        total_completed = sum(m["tasks_completed"] for m in members.values())
        total_assigned = sum(m["tasks_assigned"] for m in members.values())
        total_minutes = sum(m["activity_minutes"] for m in members.values())
        total_shared = sum(m["memory_shared"] for m in members.values())

        completion_rate = total_completed / total_assigned if total_assigned > 0 else 0

        return {
            "member_count": len(members),
            "total_tasks_completed": total_completed,
            "total_tasks_assigned": total_assigned,
            "completion_rate": round(completion_rate, 2),
            "total_activity_hours": round(total_minutes / 60, 1),
            "total_memory_shared": total_shared,
            "avg_tasks_per_member": round(total_completed / len(members), 1) if members else 0,
            "avg_hours_per_member": round(total_minutes / 60 / len(members), 1) if members else 0,
        }

    def get_member_leaderboard(self) -> list[dict]:
        members = self._data["members"]
        leaderboard = []
        for uid, m in members.items():
            leaderboard.append({
                "user_id": uid,
                "name": m["name"],
                "tasks_completed": m["tasks_completed"],
                "activity_hours": round(m["activity_minutes"] / 60, 1),
                "memory_shared": m["memory_shared"],
                "completion_rate": round(m["tasks_completed"] / m["tasks_assigned"], 2) if m["tasks_assigned"] > 0 else 0,
            })
        leaderboard.sort(key=lambda x: x["tasks_completed"], reverse=True)
        return leaderboard

    def get_activity_heatmap(self, days: int = 7) -> list[dict]:
        shared = self._data["shared_memory"]
        daily = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily[date] = {"count": 0, "users": set()}

        for entry in shared:
            date = entry["shared_at"][:10]
            if date in daily:
                daily[date]["count"] += 1
                daily[date]["users"].add(entry["user_id"])

        result = []
        for date in sorted(daily.keys()):
            result.append({
                "date": date,
                "memory_shares": daily[date]["count"],
                "active_users": len(daily[date]["users"]),
            })
        return result

    def get_shared_memory(self, limit: int = 50) -> list[dict]:
        return self._data["shared_memory"][-limit:]

    def get_member(self, user_id: str) -> Optional[dict]:
        return self._data["members"].get(user_id)

    def get_members(self) -> dict:
        return self._data["members"]

    def get_team_insights(self) -> list[str]:
        insights = []
        stats = self.get_team_stats()

        if stats["member_count"] == 0:
            return ["No team members yet. Add members to start tracking."]

        if stats["completion_rate"] > 0.8:
            insights.append(f"Team completion rate is excellent at {stats['completion_rate']:.0%}!")
        elif stats["completion_rate"] < 0.5:
            insights.append(f"Team completion rate is low at {stats['completion_rate']:.0%}. Consider workload distribution.")

        if stats["total_activity_hours"] > 0:
            avg_hours = stats["avg_hours_per_member"]
            if avg_hours > 8:
                insights.append(f"Average {avg_hours}h activity per member. Watch for overwork.")
            elif avg_hours < 2:
                insights.append(f"Average {avg_hours}h activity per member. Engagement could improve.")

        if stats["total_memory_shared"] > 10:
            insights.append(f"Team has shared {stats['total_memory_shared']} memory entries. Good collaboration!")

        leaderboard = self.get_member_leaderboard()
        if len(leaderboard) >= 2:
            top = leaderboard[0]
            insights.append(f"Top contributor: {top['name']} with {top['tasks_completed']} tasks completed.")

        return insights
