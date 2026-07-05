# Pinchu

Your AI productivity buddy. Plans your day, tracks your progress, keeps you focused.

![Pinchu](https://img.shields.io/badge/version-1.1.0-purple) ![License](https://img.shields.io/badge/license-MIT-green) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-blue) ![Python](https://img.shields.io/badge/python-3.10+-yellow)

## What is Pinchu?

Pinchu is an AI productivity desktop buddy that manages your tasks, monitors your activity, and keeps you focused. It sits on your desktop as an animated companion that reacts to what you're doing.

## Features

- **AI Task Management** — Natural language input with auto-classification, priority, and deadline detection
- **Activity Monitoring** — 12 activity types from foreground window analysis
- **Desktop Overlay** — Animated character that reacts to your activity with emotion
- **AI Chat** — Ask anything about tasks, schedule, or past activity
- **Voice Interaction** — Push-to-talk with speech recognition and text-to-speech
- **Daily Summaries** — Productivity scores, completed/missed tasks, AI insights
- **Weekly Stats** — 7-day task completion tracking
- **Knowledge Graph** — Visualize how Pinchu connects your tasks, activities, and context
- **Multi-Session Context** — Pinchu remembers context across sessions
- **Cognee Cloud Memory** — Learns patterns, preferences, and context over time
- **Memory Management** — Optimize memory (improve), clear memory (forget)
- **13+ Typed Memory Nodes** — task, activity, chat, insight, pattern, preference, schedule, project, person, goal, habit, context, summary, emotion, environment
- **Agent Mode** — Execute actions: open apps, URLs, files, run commands, search web
- **Burnout Prediction** — Analyze activity patterns and predict burnout risk
- **REST API** — Full API with FastAPI, webhooks support
- **Team Analytics** — Leaderboard, activity heatmap, team insights
- **Team/Collaborative Memory** — Share context with team members
- **CLI Tool** — 14 commands from the terminal
- **Cross-Platform** — Works on Windows and macOS
- **Privacy-First** — Local JSON storage with optional cloud sync

## Quick Start

### Download

Download the latest release for your platform:

- **Windows**: [Pinchu.zip](https://github.com/SuhasHanamannavar/pinchu/releases/download/v1.0.0/Pinchu.zip)
- **macOS**: Build from source (see below)

### Run

1. Extract the zip
2. Run `Pinchu.exe` (Windows) or `Pinchu.app` (macOS)
3. Enter your LLM API key when prompted

### pip Install

```bash
pip install pinchu
pip install pinchu[api]  # with REST API support
```

## CLI Usage

```bash
# Task management
pinchu add "task description"
pinchu list
pinchu done <index>
pinchu summary

# Memory
pinchu remember "text"
pinchu recall "query"
pinchu improve
pinchu forget

# Knowledge graph
pinchu graph
pinchu nodes [type]
pinchu history

# Agent mode
pinchu agent "open chrome"
pinchu agent "go to github.com"
pinchu agent "search python docs"

# Burnout prediction
pinchu burnout

# REST API
pinchu api
```

## REST API

Start the API server:

```bash
pinchu-api
# or
python api_server.py
```

API docs at `http://localhost:8000/docs`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | Get today's tasks |
| POST | `/tasks` | Submit tasks |
| PUT | `/tasks/{index}/done` | Mark task complete |
| GET | `/activity` | Get activity summary |
| POST | `/memory` | Store memory node |
| GET | `/memory` | Get recent memories |
| GET | `/memory/search?q=` | Search memories |
| GET | `/nodes` | Get all memory nodes |
| POST | `/agent/execute` | Execute agent action |
| POST | `/burnout/analyze` | Analyze burnout risk |
| GET | `/burnout/trend` | Get burnout trend |
| POST | `/webhooks` | Add webhook |
| GET | `/health` | Health check |

## Build from Source

### Windows

```bash
git clone https://github.com/SuhasHanamannavar/pinchu.git
cd pinchu
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --name Pinchu --onedir --windowed --icon=NONE --add-data "ui;ui" main.py
```

### macOS

```bash
git clone https://github.com/SuhasHanamannavar/pinchu.git
cd pinchu
pip install -r requirements.txt
pip install pyinstaller
bash build_macos.sh
```

## Architecture

```
pinchu/
├── main.py              # App entry point
├── config.py            # Configuration, API keys
├── task_manager.py      # Task CRUD, JSON storage
├── activity_monitor.py  # Window tracking, 12 activity types
├── ai_client.py         # LLM API calls, model rotation
├── memory.py            # Cognee cloud memory integration
├── memory_nodes.py      # 13+ typed memory nodes
├── context_chain.py     # Multi-session context chaining
├── agent.py             # Agent mode, action execution
├── burnout.py           # Burnout prediction
├── team_analytics.py    # Team analytics dashboard
├── api_server.py        # REST API (FastAPI)
├── voice.py             # Speech recognition + TTS
├── overlay.py           # Desktop overlay widget
├── tray.py              # System tray icon
├── cli.py               # CLI tool
├── setup.py             # pip package setup
├── ui/
│   ├── design.py        # Colors, fonts, styles
│   ├── character.py     # Animated character widget
│   └── views/
│       ├── dashboard.py
│       ├── task_input.py
│       ├── summary.py
│       ├── chat.py
│       └── knowledge_graph.py
└── data/                # User data (gitignored)
```

## Tech Stack

- **GUI**: PyQt5
- **AI**: OpenAI, Anthropic, or compatible LLM APIs
- **Memory**: Cognee cloud + local JSON
- **Voice**: SpeechRecognition + pyttsx3
- **API**: FastAPI + uvicorn
- **Build**: PyInstaller
- **Platform**: Windows 10/11, macOS 10.15+

## Privacy

- All data stored locally in JSON files
- Optional Cognee cloud sync (encrypted)
- No telemetry, no tracking, no subscriptions
- Your data stays yours

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Suhas Hanamannavar - [GitHub](https://github.com/SuhasHanamannavar)
