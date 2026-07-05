import os
import subprocess
import platform
import webbrowser
from datetime import datetime
from enum import Enum
from typing import Optional
import json
from pathlib import Path
from config import DATA_DIR


class ActionType(Enum):
    OPEN_APP = "open_app"
    OPEN_URL = "open_url"
    OPEN_FILE = "open_file"
    CREATE_FILE = "create_file"
    SET_REMINDER = "set_reminder"
    RUN_COMMAND = "run_command"
    SEARCH_WEB = "search_web"
    SEND_NOTIFICATION = "send_notification"
    BLOCK_APP = "block_app"
    FOCUS_MODE = "focus_mode"
    TAKE_BREAK = "take_break"
    LOG_TIME = "log_time"


ACTION_DESCRIPTIONS = {
    ActionType.OPEN_APP: "Open an application on your computer",
    ActionType.OPEN_URL: "Open a URL in your browser",
    ActionType.OPEN_FILE: "Open a file with its default application",
    ActionType.CREATE_FILE: "Create a new file with content",
    ActionType.SET_REMINDER: "Set a timed reminder",
    ActionType.RUN_COMMAND: "Run a system command",
    ActionType.SEARCH_WEB: "Search the web for a query",
    ActionType.SEND_NOTIFICATION: "Send a desktop notification",
    ActionType.BLOCK_APP: "Block an app during focus time",
    ActionType.FOCUS_MODE: "Enable focus mode (silence notifications)",
    ActionType.TAKE_BREAK: "Suggest a break with timer",
    ActionType.LOG_TIME: "Log time spent on a task",
}


class AgentAction:
    def __init__(self, action_type: ActionType, params: dict, auto_execute: bool = False):
        self.id = f"action_{int(datetime.now().timestamp() * 1000)}"
        self.action_type = action_type
        self.params = params
        self.auto_execute = auto_execute
        self.status = "pending"
        self.result = None
        self.created_at = datetime.now().isoformat()
        self.executed_at = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.action_type.value,
            "params": self.params,
            "auto_execute": self.auto_execute,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at,
            "executed_at": self.executed_at,
        }


class Agent:
    def __init__(self):
        self._actions_file = DATA_DIR / "agent_actions.json"
        self._action_history: list[dict] = []
        self._is_windows = platform.system() == "Windows"
        self._is_macos = platform.system() == "Darwin"
        self._load_history()

    def _load_history(self):
        if self._actions_file.exists():
            try:
                self._action_history = json.loads(self._actions_file.read_text())
            except Exception:
                self._action_history = []

    def _save_history(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._actions_file.write_text(json.dumps(self._action_history[-100:], indent=2))

    def execute(self, action: AgentAction) -> AgentAction:
        try:
            if action.action_type == ActionType.OPEN_APP:
                result = self._open_app(action.params.get("app", ""))
            elif action.action_type == ActionType.OPEN_URL:
                result = self._open_url(action.params.get("url", ""))
            elif action.action_type == ActionType.OPEN_FILE:
                result = self._open_file(action.params.get("path", ""))
            elif action.action_type == ActionType.CREATE_FILE:
                result = self._create_file(
                    action.params.get("path", ""),
                    action.params.get("content", "")
                )
            elif action.action_type == ActionType.RUN_COMMAND:
                result = self._run_command(action.params.get("command", ""))
            elif action.action_type == ActionType.SEARCH_WEB:
                result = self._search_web(action.params.get("query", ""))
            elif action.action_type == ActionType.SEND_NOTIFICATION:
                result = self._send_notification(
                    action.params.get("title", "Pinchu"),
                    action.params.get("message", "")
                )
            elif action.action_type == ActionType.LOG_TIME:
                result = self._log_time(
                    action.params.get("task", ""),
                    action.params.get("minutes", 0)
                )
            else:
                result = {"status": "unsupported", "message": f"Action {action.action_type.value} not yet implemented"}

            action.status = "completed"
            action.result = result
            action.executed_at = datetime.now().isoformat()
        except Exception as e:
            action.status = "failed"
            action.result = {"error": str(e)}

        self._action_history.append(action.to_dict())
        self._save_history()
        return action

    def _open_app(self, app_name: str) -> dict:
        try:
            if self._is_windows:
                os.startfile(app_name)
            elif self._is_macos:
                subprocess.run(["open", "-a", app_name], check=True)
            else:
                subprocess.run([app_name], check=True)
            return {"status": "success", "message": f"Opened {app_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _open_url(self, url: str) -> dict:
        try:
            webbrowser.open(url)
            return {"status": "success", "message": f"Opened {url}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _open_file(self, path: str) -> dict:
        try:
            if self._is_windows:
                os.startfile(path)
            elif self._is_macos:
                subprocess.run(["open", path], check=True)
            else:
                subprocess.run(["xdg-open", path], check=True)
            return {"status": "success", "message": f"Opened {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _create_file(self, path: str, content: str) -> dict:
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(content)
            return {"status": "success", "message": f"Created {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _run_command(self, command: str) -> dict:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            return {
                "status": "success",
                "stdout": result.stdout[:500],
                "stderr": result.stderr[:200],
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _search_web(self, query: str) -> dict:
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return {"status": "success", "message": f"Searching for: {query}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _send_notification(self, title: str, message: str) -> dict:
        try:
            if self._is_windows:
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5)
                except ImportError:
                    pass
            elif self._is_macos:
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ])
            return {"status": "success", "message": f"Notification: {title}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _log_time(self, task: str, minutes: int) -> dict:
        try:
            log_file = DATA_DIR / "time_log.jsonl"
            entry = {
                "timestamp": datetime.now().isoformat(),
                "task": task,
                "minutes": minutes,
            }
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return {"status": "success", "message": f"Logged {minutes}min for {task}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def parse_action(self, text: str) -> Optional[AgentAction]:
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["open ", "launch ", "start "]):
            app = text.split("open ", 1)[-1].split("launch ", 1)[-1].split("start ", 1)[-1].strip()
            if "." in app or "/" in app:
                return AgentAction(ActionType.OPEN_URL, {"url": app})
            return AgentAction(ActionType.OPEN_APP, {"app": app})

        if any(kw in text_lower for kw in ["go to ", "visit ", "browse "]):
            url = text.split("go to ", 1)[-1].split("visit ", 1)[-1].split("browse ", 1)[-1].strip()
            if not url.startswith("http"):
                url = f"https://{url}"
            return AgentAction(ActionType.OPEN_URL, {"url": url})

        if "search" in text_lower or "google" in text_lower:
            query = text.split("search ", 1)[-1].split("google ", 1)[-1].strip()
            return AgentAction(ActionType.SEARCH_WEB, {"query": query})

        if "create file" in text_lower or "write file" in text_lower:
            parts = text.split("create file ", 1)[-1].split("write file ", 1)[-1].strip()
            return AgentAction(ActionType.CREATE_FILE, {"path": parts, "content": ""})

        if "run " in text_lower or "execute " in text_lower:
            cmd = text.split("run ", 1)[-1].split("execute ", 1)[-1].strip()
            return AgentAction(ActionType.RUN_COMMAND, {"command": cmd})

        return None

    def get_history(self, limit: int = 20) -> list[dict]:
        return self._action_history[-limit:]

    def get_available_actions(self) -> dict:
        return {k.value: v for k, v in ACTION_DESCRIPTIONS.items()}
