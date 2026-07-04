import json
import time
import psutil
from datetime import datetime
from pathlib import Path
from config import ACTIVITY_LOG, DATA_DIR


class ActivityMonitor:
    def __init__(self):
        self._running = False
        self._log_file = ACTIVITY_LOG
        self._current_window = ""
        self._window_start = 0
        self._task_matches = []

    def get_active_window_title(self) -> str:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value
        except Exception:
            return "Unknown"

    def get_browser_url(self) -> str:
        try:
            import ctypes
            import ctypes.wintypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc = psutil.Process(pid.value)
            name = proc.name().lower()
            if any(b in name for b in ["chrome", "firefox", "edge", "brave", "opera"]):
                return f"[Browser: {name}]"
            return name
        except Exception:
            return "Unknown"

    def get_screen_time_apps(self) -> dict:
        apps = {}
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_path = DATA_DIR / f"screen_time_{today}.json"
            if log_path.exists():
                apps = json.loads(log_path.read_text())
        except Exception:
            pass
        return apps

    def log_activity(self, window_title: str, app_name: str):
        activity_type = self.get_detected_activity_type(window_title, app_name)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "window": window_title[:200],
            "app": app_name,
            "activity_type": activity_type,
        }
        with open(self._log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        today = datetime.now().strftime("%Y-%m-%d")
        log_path = DATA_DIR / f"screen_time_{today}.json"
        apps = {}
        if log_path.exists():
            apps = json.loads(log_path.read_text())
        if app_name not in apps:
            apps[app_name] = 0
        apps[app_name] += 5
        log_path.write_text(json.dumps(apps, indent=2))

        activity_log = DATA_DIR / f"activity_{today}.jsonl"
        with open(activity_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def check_task_match(self, tasks: list, window_title: str, app_name: str) -> list:
        matches = []
        combined = (window_title + " " + app_name).lower()
        keywords_map = {
            "coding": ["visual studio", "code", "ide", "pycharm", "intellij", "sublime", "notepad++", "terminal", "powershell", "cmd"],
            "email": ["outlook", "gmail", "mail", "thunderbird"],
            "meeting": ["teams", "zoom", "meet", "skype", "webex", "discord"],
            "design": ["figma", "photoshop", "illustrator", "canva", "sketch", "blender"],
            "browsing": ["chrome", "firefox", "edge", "brave", "opera"],
            "document": ["word", "excel", "powerpoint", "docs", "sheets", "notion", "obsidian"],
            "gaming": ["steam", "epic games", "roblox", "minecraft", "league of legends", "valorant", "fortnite"],
            "social": ["twitter", "x.com", "reddit", "facebook", "instagram", "linkedin", "tiktok"],
            "streaming": ["youtube", "netflix", "twitch", "spotify", "disney+", "prime video"],
            "focus": ["deep work", "focus", "pomodoro", "timer"],
            "creative": ["blender", "unity", "unreal", "after effects", "premiere", "davinci"],
            "communication": ["slack", "telegram", "whatsapp", "discord", "signal"],
        }
        detected_type = "other"
        for category, keywords in keywords_map.items():
            for kw in keywords:
                if kw in combined:
                    detected_type = category
                    break
            if detected_type != "other":
                break

        for task in tasks:
            task_text = task.get("task", "").lower()
            category = task.get("category", "").lower()
            if category in keywords_map:
                for kw in keywords_map[category]:
                    if kw in combined:
                        matches.append(task)
                        break
            for word in task_text.split():
                if len(word) > 3 and word in combined:
                    matches.append(task)
                    break
        return list({json.dumps(t, sort_keys=True): t for t in matches}.values())

    def get_detected_activity_type(self, window_title: str, app_name: str) -> str:
        combined = (window_title + " " + app_name).lower()
        keywords_map = {
            "coding": ["visual studio", "code", "ide", "pycharm", "intellij", "sublime", "notepad++", "terminal", "powershell", "cmd"],
            "email": ["outlook", "gmail", "mail", "thunderbird"],
            "meeting": ["teams", "zoom", "meet", "skype", "webex", "discord"],
            "design": ["figma", "photoshop", "illustrator", "canva", "sketch", "blender"],
            "browsing": ["chrome", "firefox", "edge", "brave", "opera"],
            "document": ["word", "excel", "powerpoint", "docs", "sheets", "notion", "obsidian"],
            "gaming": ["steam", "epic games", "roblox", "minecraft", "league of legends", "valorant", "fortnite"],
            "social": ["twitter", "x.com", "reddit", "facebook", "instagram", "linkedin", "tiktok"],
            "streaming": ["youtube", "netflix", "twitch", "spotify", "disney+", "prime video"],
            "focus": ["deep work", "focus", "pomodoro", "timer"],
            "creative": ["blender", "unity", "unreal", "after effects", "premiere", "davinci"],
            "communication": ["slack", "telegram", "whatsapp", "discord", "signal"],
        }
        for category, keywords in keywords_map.items():
            for kw in keywords:
                if kw in combined:
                    return category
        return "other"

    def get_daily_summary(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = DATA_DIR / f"screen_time_{today}.json"
        apps = {}
        if log_path.exists():
            apps = json.loads(log_path.read_text())
        total_time = sum(apps.values())

        activity_counts = {}
        activity_log = DATA_DIR / f"activity_{today}.jsonl"
        if activity_log.exists():
            for line in activity_log.read_text().strip().split("\n"):
                if line:
                    entry = json.loads(line)
                    act_type = entry.get("activity_type", "other")
                    activity_counts[act_type] = activity_counts.get(act_type, 0) + 1

        top_activity = max(activity_counts, key=activity_counts.get) if activity_counts else "unknown"

        return {
            "total_active_minutes": total_time,
            "apps": apps,
            "top_app": max(apps, key=apps.get) if apps else "None",
            "activity_breakdown": activity_counts,
            "top_activity": top_activity,
            "total_activity_entries": sum(activity_counts.values()),
        }
