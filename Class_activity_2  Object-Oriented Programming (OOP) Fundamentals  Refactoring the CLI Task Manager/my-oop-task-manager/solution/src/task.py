# my-oop-task-manager/src/task.py


class Task:
    """
    Represents a single task in the task manager.
    """

    def __init__(self, id, description, completed=False):
        """
        Initializes a new Task object.

        Args:
            id (int): A unique identifier for the task.
            description (str): A brief description of the task.
            completed (bool, optional): The completion status of the task. Defaults to False.
        """
        self.id = id
        self.description = description
        self.completed = completed

    def mark_complete(self):
        """Marks the task as completed."""
        self.completed = True

    def to_dict(self):
        """Converts the Task object to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "completed": self.completed,
        }

    def __str__(self):
        """Returns a human-readable string representation of the task."""
        status = "Completed" if self.completed else "Pending"
        return f"ID: {self.id} | Description: {self.description} | Status: {status}"

    def __repr__(self):
        """Returns an official string representation of the task object for debugging."""
        return f"Task(id={self.id}, description='{self.description}', completed={self.completed})"
