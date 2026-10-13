# enhanced-task-manager-design/src/task.py
"""Data models: Task, DueDateTask, PriorityTask (รองรับ tags)"""
import datetime


class Task:
    """Base class ของงานทุกประเภท มี tags เป็น list ของ string"""

    def __init__(self, id, description, completed=False, tags=None):
        self.id = id
        self.description = description
        self.completed = completed
        self.tags = list(tags) if tags is not None else []

    def mark_complete(self):
        self.completed = True

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)

    def _extra_str(self):
        """ส่วนเพิ่มเติมเฉพาะของแต่ละประเภท (subclass override)"""
        return ""

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "completed": self.completed,
            "tags": self.tags,
            "_type": "Task",
        }

    def __str__(self):
        status = "Completed" if self.completed else "Pending"
        tags_str = f" | Tags: {', '.join(self.tags)}" if self.tags else ""
        return (f"ID: {self.id} | Description: {self.description} | "
                f"Status: {status}{self._extra_str()}{tags_str}")

    def __repr__(self):
        return (f"Task(id={self.id}, description='{self.description}', "
                f"completed={self.completed}, tags={self.tags})")


class DueDateTask(Task):
    """งานที่มีวันครบกำหนด (datetime.date)"""

    def __init__(self, id, description, due_date, completed=False, tags=None):
        super().__init__(id, description, completed, tags)
        if isinstance(due_date, str):
            self.due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
        elif isinstance(due_date, datetime.date):
            self.due_date = due_date
        else:
            raise TypeError("due_date must be 'YYYY-MM-DD' string or datetime.date")

    def is_overdue(self):
        return not self.completed and self.due_date < datetime.date.today()

    def _extra_str(self):
        return f" | Due: {self.due_date.strftime('%Y-%m-%d')}"

    def to_dict(self):
        d = super().to_dict()
        d["due_date"] = self.due_date.strftime("%Y-%m-%d")
        d["_type"] = "DueDateTask"
        return d

    def __repr__(self):
        return (f"DueDateTask(id={self.id}, description='{self.description}', "
                f"due_date='{self.due_date}', completed={self.completed}, tags={self.tags})")


class PriorityTask(Task):
    """งานที่มีระดับความสำคัญ High / Medium / Low"""

    PRIORITY_ORDER = {"High": 1, "Medium": 2, "Low": 3}

    def __init__(self, id, description, priority, completed=False, tags=None):
        super().__init__(id, description, completed, tags)
        self.priority = priority

    def _extra_str(self):
        return f" | Priority: {self.priority}"

    def to_dict(self):
        d = super().to_dict()
        d["priority"] = self.priority
        d["_type"] = "PriorityTask"
        return d

    def __repr__(self):
        return (f"PriorityTask(id={self.id}, description='{self.description}', "
                f"priority='{self.priority}', completed={self.completed}, tags={self.tags})")
