"""
task.py
Data models for the Enhanced Task Manager: Task, DueDateTask, PriorityTask.
Every task supports a list of tags.
"""
import datetime


class Task:
    """Base class for all tasks. Includes a 'tags' attribute for categorization."""

    def __init__(self, id, description, completed=False, tags=None):
        self.id = id
        self.description = description
        self.completed = completed
        # Normalise tags: always a list of lowercase, stripped, unique strings
        self.tags = []
        for tag in (tags or []):
            self.add_tag(tag)

    def mark_complete(self):
        """Marks the task as completed."""
        self.completed = True

    def add_tag(self, tag):
        """Adds a tag to the task, preventing duplicates (case-insensitive)."""
        tag = str(tag).strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        """Removes a tag from the task. Returns True if a tag was removed."""
        tag = str(tag).strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False

    def to_dict(self):
        """Converts the Task to a dict for JSON serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "completed": self.completed,
            "tags": list(self.tags),
            "_type": "Task",
        }

    def _extra_info(self):
        """Hook for subclasses to add fields (e.g. due date, priority) before tags."""
        return ""

    def __str__(self):
        status = "Completed" if self.completed else "Pending"
        tags_str = f" | Tags: {', '.join(self.tags)}" if self.tags else ""
        return (f"ID: {self.id} | Description: {self.description} | "
                f"Status: {status}{self._extra_info()}{tags_str}")

    def __repr__(self):
        return (f"Task(id={self.id}, description='{self.description}', "
                f"completed={self.completed}, tags={self.tags})")


class DueDateTask(Task):
    """A task with a due date stored as a datetime.date object."""

    def __init__(self, id, description, due_date, completed=False, tags=None):
        super().__init__(id, description, completed, tags)
        if isinstance(due_date, datetime.datetime):
            self.due_date = due_date.date()
        elif isinstance(due_date, datetime.date):
            self.due_date = due_date
        elif isinstance(due_date, str):
            # Raises ValueError for a bad format
            self.due_date = datetime.datetime.strptime(due_date.strip(), "%Y-%m-%d").date()
        else:
            raise TypeError("due_date must be a 'YYYY-MM-DD' string or a datetime.date object")

    def to_dict(self):
        data = super().to_dict()
        data["due_date"] = self.due_date.strftime("%Y-%m-%d")
        data["_type"] = "DueDateTask"
        return data

    def _extra_info(self):
        return f" | Due: {self.due_date.strftime('%Y-%m-%d')}"

    def __repr__(self):
        return (f"DueDateTask(id={self.id}, description='{self.description}', "
                f"due_date='{self.due_date:%Y-%m-%d}', completed={self.completed}, "
                f"tags={self.tags})")


class PriorityTask(Task):
    """A task with a priority level: High, Medium or Low."""

    ALLOWED_PRIORITIES = ["High", "Medium", "Low"]

    def __init__(self, id, description, priority, completed=False, tags=None):
        super().__init__(id, description, completed, tags)
        priority = str(priority).strip().capitalize()
        if priority not in self.ALLOWED_PRIORITIES:
            raise ValueError(f"Priority must be one of {self.ALLOWED_PRIORITIES}")
        self.priority = priority

    def to_dict(self):
        data = super().to_dict()
        data["priority"] = self.priority
        data["_type"] = "PriorityTask"
        return data

    def _extra_info(self):
        return f" | Priority: {self.priority}"

    def __repr__(self):
        return (f"PriorityTask(id={self.id}, description='{self.description}', "
                f"priority='{self.priority}', completed={self.completed}, tags={self.tags})")
