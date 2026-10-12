# my-task-manager/src/task_data.py
"""Data Layer: handles loading/saving tasks to data/tasks.json (persistence)."""
import json
import os

TASKS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'tasks.json'
)


def load_tasks():
    """Loads tasks from the JSON file. Returns [] if missing or corrupted."""
    if not os.path.exists(TASKS_FILE):
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
        return []
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        print("Warning: tasks.json is empty or corrupted. Starting with an empty task list.")
        return []
    except FileNotFoundError:
        return []


def save_tasks(tasks):
    """Saves tasks to the JSON file."""
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    try:
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=4, ensure_ascii=False)
    except OSError as e:
        print(f"Error: could not save tasks ({e}).")
