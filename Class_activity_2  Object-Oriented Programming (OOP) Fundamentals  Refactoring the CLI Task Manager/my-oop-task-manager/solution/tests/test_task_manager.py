import json
import os
import tempfile
import unittest

from src.task_manager import TaskManager


class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "tasks.json")
        self.manager = TaskManager(data_file=self.path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_starts_empty(self):
        self.assertEqual(self.manager.tasks, [])
        self.assertEqual(self.manager.next_id, 1)

    def test_add_task_saves_to_json(self):
        self.manager.add_task("Task 1")
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, [{"id": 1, "description": "Task 1", "completed": False}])
        self.assertEqual(self.manager.next_id, 2)

    def test_complete_task(self):
        self.manager.add_task("Task 1")
        self.assertTrue(self.manager.complete_task(1))
        self.assertTrue(self.manager.tasks[0].completed)
        self.assertFalse(self.manager.complete_task(1))   # already completed
        self.assertFalse(self.manager.complete_task(99))  # not found

    def test_delete_task(self):
        self.manager.add_task("Task 1")
        self.manager.add_task("Task 2")
        self.assertTrue(self.manager.delete_task(1))
        self.assertEqual([t.id for t in self.manager.tasks], [2])
        self.assertFalse(self.manager.delete_task(1))

    def test_reload_restores_task_objects(self):
        self.manager.add_task("Task 1")
        self.manager.add_task("Task 2")
        self.manager.complete_task(2)
        reloaded = TaskManager(data_file=self.path)
        self.assertEqual(len(reloaded.tasks), 2)
        self.assertFalse(reloaded.tasks[0].completed)
        self.assertTrue(reloaded.tasks[1].completed)
        self.assertEqual(reloaded.next_id, 3)

    def test_corrupted_file(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        self.assertEqual(TaskManager(data_file=self.path).tasks, [])


if __name__ == "__main__":
    unittest.main()
