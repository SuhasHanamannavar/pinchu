import sys
import json
from datetime import datetime
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("Install API deps: pip install fastapi uvicorn")
    print("Or: pip install pinchu[api]")
    sys.exit(1)

from task_manager import TaskManager
from activity_monitor import ActivityMonitor
from memory import MemoryManager
from memory_nodes import MemoryNodeStore, MemoryNodeType, MemoryNode
from agent import Agent, ActionType
from burnout import BurnoutPredictor
from config import DATA_DIR

app = FastAPI(
    title="Pinchu API",
    description="AI Productivity Buddy REST API",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

task_manager = TaskManager()
activity_monitor = ActivityMonitor()
memory = MemoryManager()
node_store = MemoryNodeStore()
agent = Agent()
burnout = BurnoutPredictor()


class TaskSubmit(BaseModel):
    tasks: str

class ChatMessage(BaseModel):
    message: str
    context: str = ""

class MemoryStore(BaseModel):
    content: str
    node_type: str = "context"
    metadata: dict = {}

class ActionRequest(BaseModel):
    action_type: str
    params: dict = {}

class WebhookConfig(BaseModel):
    url: str
    events: list[str] = []
    secret: str = ""


@app.get("/")
def root():
    return {
        "name": "Pinchu API",
        "version": "1.1.0",
        "status": "running",
        "endpoints": {
            "tasks": "/tasks",
            "activity": "/activity",
            "memory": "/memory",
            "nodes": "/nodes",
            "agent": "/agent",
            "burnout": "/burnout",
            "health": "/health",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/tasks")
def get_tasks():
    return {
        "today": task_manager.get_today_tasks(),
        "pending": task_manager.get_pending_tasks(),
        "completed": task_manager.get_completed_tasks(),
    }


@app.post("/tasks")
def submit_tasks(body: TaskSubmit):
    task_manager.set_today_tasks(body.tasks)
    return {"status": "ok", "message": "Tasks submitted"}


@app.put("/tasks/{index}/done")
def complete_task(index: int):
    task_manager.mark_task_done(str(index))
    return {"status": "ok", "message": f"Task {index} completed"}


@app.put("/tasks/{index}/progress")
def update_progress(index: int, progress: float):
    task_manager.mark_task_progress(str(index), progress)
    return {"status": "ok", "message": f"Task {index} progress updated"}


@app.get("/activity")
def get_activity():
    return activity_monitor.get_daily_summary()


@app.get("/activity/types")
def get_activity_types():
    return {
        "types": [
            "coding", "email", "meeting", "design", "browsing",
            "document", "gaming", "social", "streaming", "focus",
            "creative", "communication", "other"
        ]
    }


@app.post("/memory")
def store_memory(body: MemoryStore):
    node_type = MemoryNodeType(body.node_type)
    node = MemoryNode(
        node_type=node_type,
        content=body.content,
        metadata=body.metadata,
    )
    node_store.add(node)
    return {"status": "ok", "node_id": node.id}


@app.get("/memory")
def get_memory(limit: int = 20):
    nodes = node_store.get_recent(limit)
    return {"nodes": [n.to_dict() for n in nodes], "total": node_store.count()}


@app.get("/memory/search")
def search_memory(q: str):
    nodes = node_store.search(q)
    return {"nodes": [n.to_dict() for n in nodes], "count": len(nodes)}


@app.get("/memory/types")
def get_memory_types():
    return {"types": node_store.get_type_stats(), "total": node_store.count()}


@app.get("/nodes")
def get_nodes():
    return {"nodes": [n.to_dict() for n in node_store.all()], "total": node_store.count()}


@app.get("/nodes/{node_type}")
def get_nodes_by_type(node_type: str):
    nodes = node_store.get_by_type(MemoryNodeType(node_type))
    return {"nodes": [n.to_dict() for n in nodes], "count": len(nodes)}


@app.get("/nodes/{node_id}/connections")
def get_node_connections(node_id: str):
    connected = node_store.get_connected(node_id)
    return {"nodes": [n.to_dict() for n in connected], "count": len(connected)}


@app.post("/agent/execute")
def execute_action(body: ActionRequest):
    action_type = ActionType(body.action_type)
    action = agent.parse_action(body.action_type) or __import__("agent").AgentAction(
        action_type=action_type, params=body.params
    )
    result = agent.execute(action)
    return result.to_dict()


@app.post("/agent/parse")
def parse_action(body: ChatMessage):
    action = agent.parse_action(body.message)
    if action:
        return {"parsed": True, "action": action.to_dict()}
    return {"parsed": False, "message": "No action detected"}


@app.get("/agent/actions")
def get_action_history(limit: int = 20):
    return {"actions": agent.get_history(limit)}


@app.get("/agent/available")
def get_available_actions():
    return agent.get_available_actions()


@app.post("/burnout/analyze")
def analyze_burnout():
    activity = activity_monitor.get_daily_summary()
    tasks = {
        "total": len(task_manager.get_today_tasks().split("\n")) if task_manager.get_today_tasks() else 0,
        "completed": len(task_manager.get_completed_tasks()),
    }
    result = burnout.analyze(activity, tasks)
    return result


@app.get("/burnout/trend")
def get_burnout_trend(days: int = 7):
    return burnout.get_trend(days)


@app.get("/burnout/weekly")
def get_weekly_burnout():
    return burnout.get_weekly_burnout()


@app.get("/burnout/insights")
def get_burnout_insights():
    return {"insights": burnout.get_insights()}


@app.get("/webhooks")
def get_webhooks():
    webhook_file = DATA_DIR / "webhooks.json"
    if webhook_file.exists():
        return json.loads(webhook_file.read_text())
    return {"webhooks": []}


@app.post("/webhooks")
def add_webhook(body: WebhookConfig):
    webhook_file = DATA_DIR / "webhooks.json"
    webhooks = json.loads(webhook_file.read_text()) if webhook_file.exists() else {"webhooks": []}
    webhook = {
        "id": f"wh_{int(datetime.now().timestamp())}",
        "url": body.url,
        "events": body.events,
        "secret": body.secret,
        "created_at": datetime.now().isoformat(),
    }
    webhooks["webhooks"].append(webhook)
    webhook_file.write_text(json.dumps(webhooks, indent=2))
    return {"status": "ok", "webhook": webhook}


@app.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: str):
    webhook_file = DATA_DIR / "webhooks.json"
    if webhook_file.exists():
        webhooks = json.loads(webhook_file.read_text())
        webhooks["webhooks"] = [w for w in webhooks["webhooks"] if w["id"] != webhook_id]
        webhook_file.write_text(json.dumps(webhooks, indent=2))
    return {"status": "ok"}


def main():
    print("Starting Pinchu API on http://0.0.0.0:8000")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
