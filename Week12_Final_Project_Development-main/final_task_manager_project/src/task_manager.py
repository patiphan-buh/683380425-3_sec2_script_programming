"""
task_manager.py
Business logic layer: add, list, complete, delete, search, filter, sort.
"""
import datetime
import logging

from .task import Task, DueDateTask, PriorityTask
from .data_persistence import DataPersistence

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages the collection of Task objects."""

    PRIORITY_MAP = {"High": 1, "Medium": 2, "Low": 3}
    REVERSE_PRIORITY_MAP = {1: "High", 2: "Medium", 3: "Low"}
    SORT_CRITERIA = ["id", "description", "completed", "due_date", "priority"]

    def __init__(self, data_file="data/tasks.json"):
        self.persistence = DataPersistence(data_file)
        self.tasks = self.persistence.load_tasks()
        self.next_id = self._get_next_task_id()

    def _get_next_task_id(self):
        """Generates the next unique ID for a new task."""
        if not self.tasks:
            return 1
        return max(task.id for task in self.tasks) + 1

    def _save_changes(self):
        self.persistence.save_tasks(self.tasks)

    def _add(self, task):
        self.tasks.append(task)
        self.next_id += 1
        self._save_changes()
        logger.info("Task added: %r", task)
        return task

    # --- Basic CRUD Operations ---
    def add_normal_task(self, description, tags=None):
        return self._add(Task(self.next_id, description, tags=tags))

    def add_due_date_task(self, description, due_date, tags=None):
        """Returns the new task, or None if the date is invalid."""
        try:
            task = DueDateTask(self.next_id, description, due_date, tags=tags)
        except (ValueError, TypeError):
            logger.error("Invalid due date: %s", due_date)
            return None
        return self._add(task)

    def add_priority_task(self, description, priority, tags=None):
        """Returns the new task, or None if the priority is invalid."""
        try:
            task = PriorityTask(self.next_id, description, priority, tags=tags)
        except ValueError:
            logger.error("Invalid priority: %s", priority)
            return None
        return self._add(task)

    def get_task_by_id(self, task_id):
        return next((task for task in self.tasks if task.id == task_id), None)

    def complete_task(self, task_id):
        task = self.get_task_by_id(task_id)
        if task is None:
            return False, f"Task ID {task_id} not found."
        if task.completed:
            return False, f"Task ID {task_id} is already completed."
        task.mark_complete()
        self._save_changes()
        return True, f"Task ID {task_id} marked as completed."

    def delete_task(self, task_id):
        original_len = len(self.tasks)
        self.tasks = [task for task in self.tasks if task.id != task_id]
        if len(self.tasks) < original_len:
            self._save_changes()
            return True, f"Task ID {task_id} deleted successfully."
        return False, f"Task ID {task_id} not found."

    def get_all_tasks(self):
        return list(self.tasks)

    # --- Search / Filter / Sort ---
    def search_tasks(self, keyword):
        """Case-insensitive partial-match search in description and tags."""
        if not keyword or not keyword.strip():
            return []
        kw = keyword.strip().lower()
        return [t for t in self.tasks
                if kw in t.description.lower() or any(kw in tag for tag in t.tags)]

    def filter_tasks(self, status=None, due_date_before=None, due_date_after=None,
                     priority_level=None, contains_tags=None):
        """
        Filters tasks; all given criteria are combined with AND.

        Args:
            status (bool|None): True = completed, False = pending.
            due_date_before (datetime.date|None): due on or before this date (DueDateTask only).
            due_date_after (datetime.date|None): due on or after this date (DueDateTask only).
            priority_level (str|None): "High", "Medium" or "Low" (PriorityTask only).
            contains_tags (list|None): task must contain ALL of these tags.
        """
        result = list(self.tasks)

        if status is not None:
            result = [t for t in result if t.completed == status]
        if due_date_before is not None:
            result = [t for t in result
                      if isinstance(t, DueDateTask) and t.due_date <= due_date_before]
        if due_date_after is not None:
            result = [t for t in result
                      if isinstance(t, DueDateTask) and t.due_date >= due_date_after]
        if priority_level:
            level = priority_level.strip().capitalize()
            result = [t for t in result
                      if isinstance(t, PriorityTask) and t.priority == level]
        if contains_tags:
            wanted = [tag.strip().lower() for tag in contains_tags if tag.strip()]
            result = [t for t in result if all(tag in t.tags for tag in wanted)]
        return result

    def sort_tasks(self, criterion="id", reverse=False, tasks=None):
        """
        Returns a new sorted list. Tasks without the sort attribute (e.g. no due date)
        are always placed LAST, in both ascending and descending order.
        """
        tasks = list(self.tasks if tasks is None else tasks)

        if criterion == "description":
            return sorted(tasks, key=lambda t: (t.description.lower(), t.id), reverse=reverse)
        if criterion == "completed":
            return sorted(tasks, key=lambda t: (t.completed, t.id), reverse=reverse)
        if criterion == "due_date":
            with_attr = [t for t in tasks if isinstance(t, DueDateTask)]
            without = [t for t in tasks if not isinstance(t, DueDateTask)]
            with_attr.sort(key=lambda t: (t.due_date, t.id), reverse=reverse)
            return with_attr + sorted(without, key=lambda t: t.id)
        if criterion == "priority":
            with_attr = [t for t in tasks if isinstance(t, PriorityTask)]
            without = [t for t in tasks if not isinstance(t, PriorityTask)]
            with_attr.sort(key=lambda t: (self.PRIORITY_MAP[t.priority], t.id), reverse=reverse)
            return with_attr + sorted(without, key=lambda t: t.id)
        # default / unknown criterion -> sort by id
        return sorted(tasks, key=lambda t: t.id, reverse=reverse)
