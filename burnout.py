import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config import DATA_DIR


class BurnoutLevel:
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class BurnoutPredictor:
    def __init__(self):
        self._history_file = DATA_DIR / "burnout_history.json"
        self._history: list[dict] = []
        self._load()

    def _load(self):
        if self._history_file.exists():
            try:
                self._history = json.loads(self._history_file.read_text())
            except Exception:
                self._history = []

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._history_file.write_text(json.dumps(self._history[-365:], indent=2))

    def analyze(self, activity_data: dict, task_data: dict) -> dict:
        factors = {}

        total_active = activity_data.get("total_active_minutes", 0)
        if total_active > 600:
            factors["overwork"] = {"score": 0.9, "detail": f"{total_active}min active today (>{600}min)"}
        elif total_active > 480:
            factors["overwork"] = {"score": 0.6, "detail": f"{total_active}min active today (>{480}min)"}
        elif total_active > 360:
            factors["overwork"] = {"score": 0.3, "detail": f"{total_active}min active today"}
        else:
            factors["overwork"] = {"score": 0.0, "detail": f"{total_active}min active today"}

        total_tasks = task_data.get("total", 0)
        completed = task_data.get("completed", 0)
        if total_tasks > 0:
            completion_rate = completed / total_tasks
            if completion_rate < 0.3:
                factors["task_overload"] = {"score": 0.8, "detail": f"Only {completed}/{total_tasks} tasks completed"}
            elif completion_rate < 0.6:
                factors["task_overload"] = {"score": 0.4, "detail": f"{completed}/{total_tasks} tasks completed"}
            else:
                factors["task_overload"] = {"score": 0.1, "detail": f"{completed}/{total_tasks} tasks completed"}

        activity_breakdown = activity_data.get("activity_breakdown", {})
        coding_pct = activity_breakdown.get("coding", 0)
        total_entries = sum(activity_breakdown.values()) or 1
        coding_ratio = coding_pct / total_entries
        if coding_ratio > 0.7:
            factors["monotony"] = {"score": 0.7, "detail": f"Coding {int(coding_ratio*100)}% of time"}
        else:
            factors["monotony"] = {"score": 0.1, "detail": f"Good activity variety"}

        break_entries = activity_breakdown.get("break", 0)
        break_ratio = break_entries / total_entries
        if break_ratio < 0.05:
            factors["no_breaks"] = {"score": 0.8, "detail": "Very few breaks taken"}
        elif break_ratio < 0.1:
            factors["no_breaks"] = {"score": 0.4, "detail": "Some breaks taken"}
        else:
            factors["no_breaks"] = {"score": 0.1, "detail": "Taking regular breaks"}

        meeting_entries = activity_breakdown.get("meeting", 0)
        meeting_ratio = meeting_entries / total_entries
        if meeting_ratio > 0.4:
            factors["meeting_heavy"] = {"score": 0.7, "detail": f"Meetings {int(meeting_ratio*100)}% of day"}
        else:
            factors["meeting_heavy"] = {"score": 0.1, "detail": "Normal meeting load"}

        social_entries = activity_breakdown.get("social", 0) + activity_breakdown.get("streaming", 0)
        social_ratio = social_entries / total_entries
        if social_ratio > 0.3:
            factors["distraction"] = {"score": 0.6, "detail": "High social/media usage"}
        else:
            factors["distraction"] = {"score": 0.1, "detail": "Normal media usage"}

        scores = [f["score"] for f in factors.values()]
        avg_score = sum(scores) / len(scores) if scores else 0

        if avg_score > 0.7:
            level = BurnoutLevel.CRITICAL
            recommendation = "Consider taking a break or reducing workload today."
        elif avg_score > 0.5:
            level = BurnoutLevel.HIGH
            recommendation = "Your workload is heavy. Schedule some break time."
        elif avg_score > 0.3:
            level = BurnoutLevel.MODERATE
            recommendation = "You're doing okay, but watch for signs of fatigue."
        else:
            level = BurnoutLevel.LOW
            recommendation = "Great balance! Keep up the healthy habits."

        result = {
            "level": level,
            "score": round(avg_score, 2),
            "factors": factors,
            "recommendation": recommendation,
            "analyzed_at": datetime.now().isoformat(),
        }

        self._history.append(result)
        self._save()
        return result

    def get_trend(self, days: int = 7) -> dict:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [h for h in self._history if h.get("analyzed_at", "") >= cutoff]
        if not recent:
            return {"trend": "insufficient_data", "data_points": 0}

        scores = [h["score"] for h in recent]
        avg = sum(scores) / len(scores)
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        if second_avg > first_avg + 0.1:
            direction = "worsening"
        elif second_avg < first_avg - 0.1:
            direction = "improving"
        else:
            direction = "stable"

        return {
            "trend": direction,
            "avg_score": round(avg, 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "data_points": len(scores),
            "days": days,
        }

    def get_weekly_burnout(self) -> list[dict]:
        days = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = [h for h in self._history if h.get("analyzed_at", "").startswith(date)]
            avg_score = sum(h["score"] for h in day_data) / len(day_data) if day_data else 0
            days.append({
                "date": date,
                "score": round(avg_score, 2),
                "level": self._score_to_level(avg_score),
                "data_points": len(day_data),
            })
        return days

    def _score_to_level(self, score: float) -> str:
        if score > 0.7:
            return BurnoutLevel.CRITICAL
        elif score > 0.5:
            return BurnoutLevel.HIGH
        elif score > 0.3:
            return BurnoutLevel.MODERATE
        return BurnoutLevel.LOW

    def get_insights(self) -> list[str]:
        insights = []
        trend = self.get_trend()
        if trend["trend"] == "worsening":
            insights.append("Your burnout risk has been increasing. Consider reducing workload.")
        elif trend["trend"] == "improving":
            insights.append("Great news! Your burnout risk is decreasing.")

        if trend["data_points"] > 3:
            if trend["avg_score"] > 0.6:
                insights.append(f"Average burnout score is {trend['avg_score']:.0%} over the last {trend['days']} days.")
            elif trend["avg_score"] < 0.3:
                insights.append(f"You're maintaining healthy levels (avg {trend['avg_score']:.0%}).")

        weekly = self.get_weekly_burnout()
        high_days = [d for d in weekly if d["score"] > 0.5]
        if len(high_days) > 3:
            insights.append(f"{len(high_days)} of the last 7 days had high burnout risk.")

        return insights
