# my-oop-task-manager/src/task_manager.py
import json
import os

from .task import Task  # Import the Task class from the same package


class TaskManager:
    """
    Manages the collection of Task objects, including loading, saving,
    and performing operations like add, list, complete, and delete.
    """

    def __init__(self, data_file="data/tasks.json"):
        """
        Initializes the TaskManager.
        Loads tasks from the specified data file or starts with an empty list.
        """
        self.data_file = data_file
        # Resolve relative paths against the project root (one level above src/)
        if os.path.isabs(data_file):
            self._data_file_path = data_file
        else:
            project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
            self._data_file_path = os.path.normpath(os.path.join(project_root, data_file))
        self.tasks = self._load_tasks()
        self.next_id = self._get_next_task_id()

    def _get_next_task_id(self):
        """Generates the next unique ID for a new task."""
        if not self.tasks:
            return 1
        return max(task.id for task in self.tasks) + 1

    def _load_tasks(self):
        """
        Internal method to load tasks from the JSON file.
        Converts dictionaries from JSON back into Task objects.
        """
        if not os.path.exists(self._data_file_path):
            os.makedirs(os.path.dirname(self._data_file_path), exist_ok=True)
            return []
        try:
            with open(self._data_file_path, "r", encoding="utf-8") as f:
                raw_tasks = json.load(f)
            # Convert raw dictionaries back into Task objects
            return [Task(t["id"], t["description"], t["completed"]) for t in raw_tasks]
        except json.JSONDecodeError:
            print("Warning: tasks.json is empty or corrupted. Starting with an empty task list.")
            return []
        except FileNotFoundError:
            return []

    def _save_tasks(self):
        """
        Internal method to save tasks to the JSON file.
        Converts Task objects to dictionaries before saving.
        """
        tasks_as_dicts = [task.to_dict() for task in self.tasks]
        os.makedirs(os.path.dirname(self._data_file_path), exist_ok=True)
        with open(self._data_file_path, "w", encoding="utf-8") as f:
            json.dump(tasks_as_dicts, f, indent=4, ensure_ascii=False)

    def add_task(self, description):
        """Adds a new task."""
        new_task = Task(self.next_id, description)
        self.tasks.append(new_task)
        self.next_id += 1  # Increment for the next task
        self._save_tasks()
        print(f"Task '{description}' added with ID {new_task.id}.")
        return new_task

    def list_tasks(self):
        """Lists all current tasks."""
        if not self.tasks:
            print("No tasks found.")
            return
        print("\n--- Your Tasks ---")
        for task in self.tasks:
            print(task)  # Task.__str__ is called automatically
        print("------------------")

    def find_task(self, task_id):
        """Returns the Task with the given ID, or None if not found."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def complete_task(self, task_id):
        """Marks a specific task as completed."""
        task = self.find_task(task_id)
        if task is None:
            print(f"Error: Task with ID {task_id} not found.")
            return False
        if task.completed:
            print(f"Task ID {task_id} is already completed.")
            return False
        task.mark_complete()  # Use the Task object's method
        self._save_tasks()
        print(f"Task ID {task_id} marked as completed.")
        return True

    def delete_task(self, task_id):
        """Deletes a task by its ID."""
        original_len = len(self.tasks)
        self.tasks = [task for task in self.tasks if task.id != task_id]
        if len(self.tasks) < original_len:
            self._save_tasks()
            print(f"Task ID {task_id} deleted successfully.")
            return True
        print(f"Error: Task with ID {task_id} not found.")
        return False
