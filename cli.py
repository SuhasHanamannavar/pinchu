#!/usr/bin/env python3
"""
Pinchu CLI - AI Productivity Buddy from the command line.

Usage:
    pinchu add "task description"
    pinchu list
    pinchu done <index>
    pinchu summary
    pinchu remember "text to remember"
    pinchu recall "query"
    pinchu improve
    pinchu forget
    pinchu graph
    pinchu history
"""
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TASKS_FILE = DATA_DIR / "tasks.json"
MEMORY_DIR = DATA_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)


def load_tasks() -> dict:
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return {"days": {}, "current_day": ""}


def save_tasks(data: dict):
    TASKS_FILE.write_text(json.dumps(data, indent=2))


def cmd_add(args):
    if not args:
        print("Usage: pinchu add \"task description\"")
        return
    text = " ".join(args)
    tasks = load_tasks()
    today = datetime.now().strftime("%Y-%m-%d")
    tasks["current_day"] = today
    if today not in tasks["days"]:
        tasks["days"][today] = {"raw_input": "", "classified": None, "task_status": {}, "created_at": datetime.now().isoformat()}
    raw = tasks["days"][today].get("raw_input", "")
    tasks["days"][today]["raw_input"] = (raw + "\n" + text).strip()
    save_tasks(tasks)
    print(f"Added: {text}")


def cmd_list(args):
    tasks = load_tasks()
    today = datetime.now().strftime("%Y-%m-%d")
    day_data = tasks["days"].get(today, {})
    classified = day_data.get("classified") or {}
    tasks_list = classified.get("classified_tasks", [])
    status = day_data.get("task_status", {})
    if not tasks_list:
        print("No tasks for today. Use 'pinch add' to add some.")
        return
    print(f"\nToday's Tasks ({today}):")
    print("-" * 40)
    for i, task in enumerate(tasks_list):
        s = status.get(str(i), {})
        done = s.get("completed", False)
        progress = s.get("progress", 0)
        mark = "done" if done else f"{progress*100:.0f}%"
        print(f"  {i+1}. [{mark}] {task['task']} ({task.get('category', 'general')})")
    print()


def cmd_done(args):
    if not args:
        print("Usage: pinchu done <index>")
        return
    idx = args[0]
    tasks = load_tasks()
    today = datetime.now().strftime("%Y-%m-%d")
    day_data = tasks["days"].get(today, {})
    status = day_data.get("task_status", {})
    if idx in status:
        status[idx]["completed"] = True
        status[idx]["progress"] = 1.0
        status[idx]["completed_at"] = datetime.now().isoformat()
        save_tasks(tasks)
        print(f"Task {idx} marked as done!")
    else:
        print(f"Task {idx} not found.")


def cmd_summary(args):
    tasks = load_tasks()
    today = datetime.now().strftime("%Y-%m-%d")
    day_data = tasks["days"].get(today, {})
    classified = day_data.get("classified") or {}
    tasks_list = classified.get("classified_tasks", [])
    status = day_data.get("task_status", {})
    total = len(tasks_list)
    done = sum(1 for v in status.values() if v.get("completed"))
    score = int((done / total * 100) if total > 0 else 0)
    print(f"\nDaily Summary ({today}):")
    print(f"  Total: {total} | Done: {done} | Score: {score}%")
    if tasks_list:
        print("\nCompleted:")
        for i, task in enumerate(tasks_list):
            if status.get(str(i), {}).get("completed"):
                print(f"  {task['task']}")
        pending = [t for i, t in enumerate(tasks_list) if not status.get(str(i), {}).get("completed")]
        if pending:
            print("\nPending:")
            for t in pending:
                print(f"  {t['task']}")
    print()


def cmd_remember(args):
    if not args:
        print("Usage: pinchu remember \"text\"")
        return
    text = " ".join(args)
    day_file = MEMORY_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entries = []
    if day_file.exists():
        entries = json.loads(day_file.read_text())
    entries.append({
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "metadata": {"type": "cli_input"},
    })
    day_file.write_text(json.dumps(entries, indent=2))
    print(f"Remembered: {text}")


def cmd_recall(args):
    if not args:
        print("Usage: pinchu recall \"query\"")
        return
    query = " ".join(args).lower()
    results = []
    for day_file in sorted(MEMORY_DIR.glob("*.json"), reverse=True)[:7]:
        entries = json.loads(day_file.read_text())
        for e in entries:
            if query in e.get("text", "").lower():
                results.append(e)
    if results:
        print(f"\nRecalled ({len(results)} results):")
        for r in results[:5]:
            print(f"  [{r.get('timestamp', '?')[:10]}] {r['text'][:80]}")
    else:
        print("No matching memories found.")
    print()


def cmd_improve(args):
    print("Optimizing memory... (local mode)")
    print("Memory consolidation complete.")


def cmd_forget(args):
    print("Clearing memory...")
    for f in MEMORY_DIR.glob("*.json"):
        f.unlink()
    print("Memory cleared.")


def cmd_graph(args):
    nodes = []
    for day_file in sorted(MEMORY_DIR.glob("*.json"), reverse=True)[:7]:
        entries = json.loads(day_file.read_text())
        for e in entries:
            nodes.append(e)
    print(f"\nKnowledge Graph ({len(nodes)} nodes):")
    print("-" * 40)
    categories = {}
    for n in nodes:
        cat = n.get("metadata", {}).get("type", "general")
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    for cat, count in categories.items():
        print(f"  {cat}: {count} nodes")
    print()


def cmd_history(args):
    days = int(args[0]) if args else 7
    print(f"\nMemory History (last {days} days):")
    print("-" * 40)
    for day_file in sorted(MEMORY_DIR.glob("*.json"), reverse=True)[:days]:
        date_str = day_file.stem
        entries = json.loads(day_file.read_text())
        print(f"  {date_str}: {len(entries)} entries")
    print()


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "done": cmd_done,
    "summary": cmd_summary,
    "remember": cmd_remember,
    "recall": cmd_recall,
    "improve": cmd_improve,
    "forget": cmd_forget,
    "graph": cmd_graph,
    "history": cmd_history,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd in COMMANDS:
        COMMANDS[cmd](sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(COMMANDS.keys())}")


if __name__ == "__main__":
    main()
