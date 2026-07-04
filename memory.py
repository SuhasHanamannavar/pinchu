import json
from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from config import DATA_DIR, COGNEE_API_KEY, COGNEE_API_BASE_URL


MEMORY_DIR = DATA_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

SHARED_DIR = DATA_DIR / "shared"
SHARED_DIR.mkdir(exist_ok=True)


class MemoryManager(QObject):
    memory_improved = pyqtSignal(str)
    memory_cleared = pyqtSignal(str)
    memory_error = pyqtSignal(str)
    memory_logged = pyqtSignal(str)
    graph_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._cognee = None
        self._initialized = False
        self._entry_count = 0
        self._last_improve = None
        self._graph_data = {"nodes": [], "edges": []}

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
        self._entry_count += 1
        self.memory_logged.emit(f"Remembered: {text[:50]}...")

        if self._initialized and self._cognee:
            try:
                await self._cognee.remember(text)
            except Exception:
                pass

        self._update_graph(entry)
        self.graph_updated.emit(self._graph_data)

        if self._entry_count % 10 == 0:
            await self.improve()

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
                self.memory_cleared.emit("Cloud memory cleared")
            except Exception as e:
                self.memory_error.emit(f"Failed to clear cloud memory: {e}")
        else:
            self.memory_cleared.emit("Local memory only (cloud not connected)")
        self._graph_data = {"nodes": [], "edges": []}
        self.graph_updated.emit(self._graph_data)

    async def improve(self):
        if self._initialized and self._cognee:
            try:
                await self._cognee.improve()
                self._last_improve = datetime.now()
                self.memory_improved.emit("Memory optimized — patterns consolidated")
            except Exception as e:
                self.memory_error.emit(f"Improve failed: {e}")

    def get_graph_traversal(self, start_node: str = None, depth: int = 3) -> dict:
        if not start_node:
            all_nodes = set()
            for edge in self._graph_data["edges"]:
                all_nodes.add(edge["source"])
                all_nodes.add(edge["target"])
            if all_nodes:
                start_node = list(all_nodes)[0]
            else:
                return self._graph_data

        visited = set()
        result_nodes = []
        result_edges = []

        def dfs(node_id, current_depth):
            if current_depth > depth or node_id in visited:
                return
            visited.add(node_id)
            for node in self._graph_data["nodes"]:
                if node["id"] == node_id:
                    result_nodes.append(node)
                    break
            for edge in self._graph_data["edges"]:
                if edge["source"] == node_id or edge["target"] == node_id:
                    result_edges.append(edge)
                    next_node = edge["target"] if edge["source"] == node_id else edge["source"]
                    dfs(next_node, current_depth + 1)

        if start_node:
            dfs(start_node, 0)

        return {"nodes": result_nodes, "edges": result_edges}

    def get_knowledge_clusters(self) -> list:
        categories = {}
        for node in self._graph_data["nodes"]:
            cat = node.get("category", "general")
            if cat not in categories:
                categories[cat] = {"name": cat, "nodes": [], "count": 0}
            categories[cat]["nodes"].append(node["id"])
            categories[cat]["count"] += 1
        return list(categories.values())

    def _update_graph(self, entry: dict):
        text = entry.get("text", "")
        metadata = entry.get("metadata", {})
        entry_type = metadata.get("type", "general")
        timestamp = entry.get("timestamp", "")

        node_id = f"entry_{len(self._graph_data['nodes'])}"
        node = {
            "id": node_id,
            "label": text[:40] + "..." if len(text) > 40 else text,
            "category": entry_type,
            "timestamp": timestamp,
        }
        self._graph_data["nodes"].append(node)

        keywords = [w.lower() for w in text.split() if len(w) > 3]
        for existing_node in self._graph_data["nodes"][:-1]:
            if existing_node["id"] == node_id:
                continue
            existing_label = existing_node["label"].lower()
            for kw in keywords[:3]:
                if kw in existing_label:
                    edge = {
                        "source": node_id,
                        "target": existing_node["id"],
                        "relation": "related_to",
                    }
                    self._graph_data["edges"].append(edge)
                    break

        if len(self._graph_data["nodes"]) > 1:
            prev_node = self._graph_data["nodes"][-2]
            self._graph_data["edges"].append({
                "source": prev_node["id"],
                "target": node_id,
                "relation": "followed_by",
            })

    def get_memory_stats(self) -> dict:
        total_entries = 0
        total_days = 0
        categories = {}
        for day_file in sorted(MEMORY_DIR.glob("*.json"), reverse=True):
            entries = json.loads(day_file.read_text())
            total_days += 1
            for e in entries:
                total_entries += 1
                meta = e.get("metadata", {})
                cat = meta.get("type", "general")
                categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_entries": total_entries,
            "total_days": total_days,
            "categories": categories,
            "last_improve": self._last_improve.isoformat() if self._last_improve else None,
            "cognee_connected": self._initialized,
            "graph_nodes": len(self._graph_data["nodes"]),
            "graph_edges": len(self._graph_data["edges"]),
        }

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

    def share_memory(self, user_id: str, entry: dict):
        shared_file = SHARED_DIR / f"{user_id}.json"
        shared_entries = []
        if shared_file.exists():
            shared_entries = json.loads(shared_file.read_text())
        shared_entries.append({
            "text": entry.get("text", ""),
            "timestamp": datetime.now().isoformat(),
            "from_user": entry.get("from_user", "unknown"),
        })
        shared_file.write_text(json.dumps(shared_entries, indent=2))

    def load_shared_memory(self, user_id: str) -> list:
        shared_file = SHARED_DIR / f"{user_id}.json"
        if shared_file.exists():
            return json.loads(shared_file.read_text())
        return []

    def get_all_shared_entries(self) -> list:
        all_entries = []
        for f in SHARED_DIR.glob("*.json"):
            entries = json.loads(f.read_text())
            all_entries.extend(entries)
        all_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_entries[:50]
