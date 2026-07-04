import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient
from ui.design import COLORS, SIZES, make_card


CATEGORY_COLORS = {
    "task_plan": "#8e6ce4",
    "task": "#22c55e",
    "activity": "#eab308",
    "chat": "#8960f0",
    "summary": "#ab8ff1",
    "general": "#62626f",
}


class GraphCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph_data = {"nodes": [], "edges": []}
        self._node_positions = {}
        self._node_sizes = {}
        self.setMinimumHeight(400)
        self.setStyleSheet("background: transparent;")

    def set_graph(self, data: dict):
        self.graph_data = data
        self._layout_nodes()
        self.update()

    def _layout_nodes(self):
        self._node_positions = {}
        self._node_sizes = {}
        nodes = self.graph_data.get("nodes", [])
        if not nodes:
            return
        w = max(self.width(), 600)
        h = max(self.height(), 400)
        cx, cy = w / 2, h / 2
        radius = min(w, h) * 0.35
        for i, node in enumerate(nodes):
            angle = (2 * math.pi * i) / len(nodes) - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            self._node_positions[node["id"]] = QPointF(x, y)
            self._node_sizes[node["id"]] = 12 + min(8, len(node.get("label", "")) / 5)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        grad = QColor(8, 8, 10)
        painter.fillRect(self.rect(), grad)
        edges = self.graph_data.get("edges", [])
        for edge in edges:
            src = self._node_positions.get(edge["source"])
            tgt = self._node_positions.get(edge["target"])
            if src and tgt:
                painter.setPen(QPen(QColor(60, 60, 80, 120), 1))
                painter.drawLine(src, tgt)
        nodes = self.graph_data.get("nodes", [])
        for node in nodes:
            pos = self._node_positions.get(node["id"])
            if not pos:
                continue
            size = self._node_sizes.get(node["id"], 12)
            color_hex = CATEGORY_COLORS.get(node.get("category", "general"), "#62626f")
            color = QColor(color_hex)
            glow = QRadialGradient(pos.x(), pos.y(), size * 2)
            glow.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 60))
            glow.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(pos, size * 2, size * 2)
            painter.setBrush(color)
            painter.drawEllipse(pos, size, size)
            painter.setPen(QColor(220, 215, 222))
            font = QFont("Segoe UI", 8)
            painter.setFont(font)
            label = node.get("label", "")[:25]
            text_rect = QPointF(pos.x() - 60, pos.y() + size + 4)
            painter.drawText(text_rect.x(), text_rect.y(), 120, 20, Qt.AlignCenter, label)
        if not nodes:
            painter.setPen(QColor(100, 100, 120))
            font = QFont("Segoe UI", 12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "No memory graph yet.\nAdd tasks and interact with Pinchu to build your knowledge graph.")


class KnowledgeGraphView(QWidget):
    back_clicked = pyqtSignal()

    def __init__(self, memory_manager, parent=None):
        super().__init__(parent)
        self.memory_manager = memory_manager
        self.setStyleSheet("background: transparent;")
        self._setup_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_graph)
        self._timer.start(3000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        back_btn = QPushButton("\u2190 Back")
        back_btn.setStyleSheet(f"QPushButton {{ color: {COLORS['text_secondary']}; background: transparent; border: none; font-size: {SIZES['body_size']}px; padding: 8px; }} QPushButton:hover {{ color: {COLORS['accent_secondary']}; }}")
        back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(back_btn)
        header.addStretch()
        layout.addLayout(header)

        title = QLabel("Knowledge Graph")
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 26px; font-weight: 700; background: transparent; border: none;")
        layout.addWidget(title)

        subtitle = QLabel("Visualize how Pinchu connects your tasks, activities, and context")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.cluster_combo = QComboBox()
        self.cluster_combo.setFixedWidth(200)
        self.cluster_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: {SIZES['small_size']}px;
            }}
        """)
        self.cluster_combo.addItem("All Clusters")
        controls.addWidget(self.cluster_combo)

        traverse_btn = QPushButton("Show Traversal")
        traverse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: {SIZES['small_size']}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS['accent_secondary']};
            }}
        """)
        traverse_btn.clicked.connect(self._show_traversal)
        controls.addWidget(traverse_btn)
        controls.addStretch()
        layout.addLayout(controls)

        main_content = QHBoxLayout()
        main_content.setSpacing(16)

        self.canvas = GraphCanvas()
        main_content.addWidget(self.canvas, 3)

        side_panel = QFrame()
        side_panel.setFixedWidth(280)
        side_panel.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(16, 16, 16, 16)
        side_layout.setSpacing(12)

        stats_title = QLabel("Graph Stats")
        stats_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        side_layout.addWidget(stats_title)

        self.stats_label = QLabel("Nodes: 0 | Edges: 0")
        self.stats_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
        side_layout.addWidget(self.stats_label)

        clusters_title = QLabel("Clusters")
        clusters_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        side_layout.addWidget(clusters_title)

        self.clusters_text = QLabel("No clusters yet")
        self.clusters_text.setWordWrap(True)
        self.clusters_text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {SIZES['small_size']}px; background: transparent; border: none;")
        side_layout.addWidget(self.clusters_text)

        traversal_title = QLabel("Traversal")
        traversal_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        side_layout.addWidget(traversal_title)

        self.traversal_text = QTextEdit()
        self.traversal_text.setReadOnly(True)
        self.traversal_text.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['bg_primary']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
                font-size: {SIZES['small_size']}px;
            }}
        """)
        self.traversal_text.setPlaceholderText("Click 'Show Traversal' to explore connections...")
        side_layout.addWidget(self.traversal_text)

        side_layout.addStretch()
        main_content.addWidget(side_panel)
        layout.addLayout(main_content, 1)

    def _refresh_graph(self):
        graph = self.memory_manager.get_graph_traversal()
        self.canvas.set_graph(graph)
        stats = self.memory_manager.get_memory_stats()
        self.stats_label.setText(f"Nodes: {stats['graph_nodes']} | Edges: {stats['graph_edges']}")
        clusters = self.memory_manager.get_knowledge_clusters()
        if clusters:
            cluster_text = "\n".join([f"  {c['name']}: {c['count']} nodes" for c in clusters])
            self.clusters_text.setText(cluster_text)
            self.cluster_combo.clear()
            self.cluster_combo.addItem("All Clusters")
            for c in clusters:
                self.cluster_combo.addItem(f"{c['name']} ({c['count']})")

    def _show_traversal(self):
        selected = self.cluster_combo.currentText()
        if selected == "All Clusters":
            traversal = self.memory_manager.get_graph_traversal(depth=3)
        else:
            cluster_name = selected.split(" (")[0]
            nodes_in_cluster = [n for n in self.memory_manager._graph_data["nodes"] if n.get("category") == cluster_name]
            if nodes_in_cluster:
                traversal = self.memory_manager.get_graph_traversal(start_node=nodes_in_cluster[0]["id"], depth=2)
            else:
                traversal = {"nodes": [], "edges": []}
        self.canvas.set_graph(traversal)
        text_lines = []
        for node in traversal.get("nodes", [])[:10]:
            text_lines.append(f"  [{node.get('category', '?')}] {node.get('label', '')}")
        for edge in traversal.get("edges", [])[:8]:
            text_lines.append(f"  {edge['source']} --{edge['relation']}--> {edge['target']}")
        self.traversal_text.setText("\n".join(text_lines) if text_lines else "No connections found")

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QColor, QLinearGradient
        p = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(COLORS['bg_primary']))
        grad.setColorAt(1, QColor(COLORS['gradient_end']))
        p.fillRect(self.rect(), grad)
        p.end()
