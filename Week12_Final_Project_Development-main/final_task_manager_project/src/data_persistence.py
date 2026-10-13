"""
data_persistence.py
Handles loading and saving tasks to/from a JSON file.
"""
import json
import logging
import os

from .task import Task, DueDateTask, PriorityTask

logger = logging.getLogger(__name__)

# Project root = folder that contains 'src' and 'data'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

TASK_TYPES = {
    "Task": Task,
    "DueDateTask": DueDateTask,
    "PriorityTask": PriorityTask,
}


class DataPersistence:
    """Centralizes all file I/O and (de)serialization of Task objects."""

    def __init__(self, data_file="data/tasks.json"):
        self.data_file = data_file
        if os.path.isabs(data_file):
            self._data_file_path = data_file
        else:
            self._data_file_path = os.path.join(PROJECT_ROOT, data_file)

    @property
    def path(self):
        return self._data_file_path

    def load_tasks(self):
        """Loads tasks from JSON and rebuilds the correct Task subclass for each."""
        if not os.path.exists(self._data_file_path):
            os.makedirs(os.path.dirname(self._data_file_path), exist_ok=True)
            return []

        try:
            with open(self._data_file_path, "r", encoding="utf-8") as f:
                raw_tasks = json.load(f)
        except json.JSONDecodeError:
            print("[Warning] tasks.json is empty or corrupted. Starting with an empty task list.")
            return []
        except OSError as e:
            print(f"[Warning] Could not read tasks file: {e}. Starting with an empty task list.")
            return []

        if not isinstance(raw_tasks, list):
            print("[Warning] tasks.json has an unexpected format. Starting with an empty task list.")
            return []

        loaded_tasks = []
        for t_dict in raw_tasks:
            t_dict = dict(t_dict)
            task_type = t_dict.pop("_type", "Task")
            t_dict.setdefault("tags", [])  # backwards compatible with old files
            cls = TASK_TYPES.get(task_type)
            if cls is None:
                print(f"[Warning] Unknown task type '{task_type}'. "
                      f"Skipping task ID {t_dict.get('id', 'N/A')}.")
                continue
            try:
                loaded_tasks.append(cls(**t_dict))
            except (TypeError, ValueError) as e:
                print(f"[Warning] Skipping invalid task ID {t_dict.get('id', 'N/A')}: {e}")
        logger.info("Loaded %d tasks", len(loaded_tasks))
        return loaded_tasks

    def save_tasks(self, tasks):
        """Saves a list of Task objects to the JSON file (uses to_dict polymorphically)."""
        tasks_as_dicts = [task.to_dict() for task in tasks]
        os.makedirs(os.path.dirname(self._data_file_path), exist_ok=True)
        with open(self._data_file_path, "w", encoding="utf-8") as f:
            json.dump(tasks_as_dicts, f, indent=4, ensure_ascii=False)
        logger.info("Saved %d tasks", len(tasks_as_dicts))
