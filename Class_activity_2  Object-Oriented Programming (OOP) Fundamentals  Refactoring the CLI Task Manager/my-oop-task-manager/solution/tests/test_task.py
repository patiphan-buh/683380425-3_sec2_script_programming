import unittest

from src.task import Task


class TestTask(unittest.TestCase):
    def test_init_defaults(self):
        t = Task(1, "Read book")
        self.assertEqual(t.id, 1)
        self.assertEqual(t.description, "Read book")
        self.assertFalse(t.completed)

    def test_mark_complete(self):
        t = Task(1, "Read book")
        t.mark_complete()
        self.assertTrue(t.completed)

    def test_to_dict(self):
        t = Task(2, "Write code", True)
        self.assertEqual(t.to_dict(), {"id": 2, "description": "Write code", "completed": True})

    def test_str(self):
        self.assertEqual(str(Task(1, "A")), "ID: 1 | Description: A | Status: Pending")
        self.assertEqual(str(Task(2, "B", True)), "ID: 2 | Description: B | Status: Completed")

    def test_repr(self):
        self.assertEqual(repr(Task(1, "A")), "Task(id=1, description='A', completed=False)")


if __name__ == "__main__":
    unittest.main()
