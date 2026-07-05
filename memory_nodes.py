from enum import Enum
from datetime import datetime
from typing import Optional
import json
from pathlib import Path
from config import DATA_DIR


class MemoryNodeType(Enum):
    TASK = "task"
    ACTIVITY = "activity"
    CHAT = "chat"
    INSIGHT = "insight"
    PATTERN = "pattern"
    PREFERENCE = "preference"
    SCHEDULE = "schedule"
    PROJECT = "project"
    PERSON = "person"
    GOAL = "goal"
    HABIT = "habit"
    CONTEXT = "context"
    SUMMARY = "summary"
    EMOTION = "emotion"
    ENVIRONMENT = "environment"


NODE_DESCRIPTIONS = {
    MemoryNodeType.TASK: "Tasks you've set, completed, or missed",
    MemoryNodeType.ACTIVITY: "Apps you've used and what you were doing",
    MemoryNodeType.CHAT: "Conversations with Pinchu",
    MemoryNodeType.INSIGHT: "AI-discovered insights about your work",
    MemoryNodeType.PATTERN: "Repeated behaviors Pinchu has detected",
    MemoryNodeType.PREFERENCE: "Your likes, dislikes, and working style",
    MemoryNodeType.SCHEDULE: "Meetings, deadlines, and time patterns",
    MemoryNodeType.PROJECT: "Projects you're working on",
    MemoryNodeType.PERSON: "People you collaborate with",
    MemoryNodeType.GOAL: "Short and long-term goals",
    MemoryNodeType.HABIT: "Daily/weekly habits tracked over time",
    MemoryNodeType.CONTEXT: "Situational context (location, time, mood)",
    MemoryNodeType.SUMMARY: "Periodic summaries of your activity",
    MemoryNodeType.EMOTION: "Emotional state patterns",
    MemoryNodeType.ENVIRONMENT: "Work environment details",
}


class MemoryNode:
    def __init__(
        self,
        node_type: MemoryNodeType,
        content: str,
        metadata: Optional[dict] = None,
        confidence: float = 1.0,
        connections: Optional[list] = None,
    ):
        self.id = f"{node_type.value}_{int(datetime.now().timestamp() * 1000)}"
        self.node_type = node_type
        self.content = content
        self.metadata = metadata or {}
        self.confidence = confidence
        self.connections = connections or []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.access_count = 0
        self.relevance = 1.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.node_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "connections": self.connections,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "relevance": self.relevance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryNode":
        node = cls(
            node_type=MemoryNodeType(data["type"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            confidence=data.get("confidence", 1.0),
            connections=data.get("connections", []),
        )
        node.id = data.get("id", node.id)
        node.created_at = data.get("created_at", node.created_at)
        node.updated_at = data.get("updated_at", node.updated_at)
        node.access_count = data.get("access_count", 0)
        node.relevance = data.get("relevance", 1.0)
        return node

    def connect(self, other_id: str, relation: str = "related"):
        self.connections.append({"target": other_id, "relation": relation})

    def touch(self):
        self.access_count += 1
        self.updated_at = datetime.now().isoformat()
        self.relevance = min(1.0, self.relevance + 0.05)


class MemoryNodeStore:
    def __init__(self):
        self._store_file = DATA_DIR / "memory_nodes.json"
        self._nodes: dict[str, MemoryNode] = {}
        self._load()

    def _load(self):
        if self._store_file.exists():
            try:
                data = json.loads(self._store_file.read_text())
                for nd in data:
                    node = MemoryNode.from_dict(nd)
                    self._nodes[node.id] = node
            except Exception:
                pass

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = [n.to_dict() for n in self._nodes.values()]
        self._store_file.write_text(json.dumps(data, indent=2))

    def add(self, node: MemoryNode) -> MemoryNode:
        self._nodes[node.id] = node
        self._save()
        return node

    def get(self, node_id: str) -> Optional[MemoryNode]:
        node = self._nodes.get(node_id)
        if node:
            node.touch()
            self._save()
        return node

    def get_by_type(self, node_type: MemoryNodeType) -> list[MemoryNode]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def search(self, query: str) -> list[MemoryNode]:
        query_lower = query.lower()
        results = []
        for node in self._nodes.values():
            if query_lower in node.content.lower():
                results.append(node)
            elif any(query_lower in str(v).lower() for v in node.metadata.values()):
                results.append(node)
        results.sort(key=lambda n: n.relevance, reverse=True)
        return results

    def get_recent(self, limit: int = 20) -> list[MemoryNode]:
        nodes = sorted(self._nodes.values(), key=lambda n: n.created_at, reverse=True)
        return nodes[:limit]

    def get_connected(self, node_id: str) -> list[MemoryNode]:
        node = self._nodes.get(node_id)
        if not node:
            return []
        connected = []
        for conn in node.connections:
            target = self._nodes.get(conn["target"])
            if target:
                connected.append(target)
        return connected

    def get_type_stats(self) -> dict:
        stats = {}
        for node_type in MemoryNodeType:
            count = len(self.get_by_type(node_type))
            if count > 0:
                stats[node_type.value] = count
        return stats

    def decay(self, days: int = 30):
        for node in self._nodes.values():
            node.relevance *= 0.95
        self._save()

    def clear(self):
        self._nodes.clear()
        self._save()

    def count(self) -> int:
        return len(self._nodes)

    def all(self) -> list[MemoryNode]:
        return list(self._nodes.values())
