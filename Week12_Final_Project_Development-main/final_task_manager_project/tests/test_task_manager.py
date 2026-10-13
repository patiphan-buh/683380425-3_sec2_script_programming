"""
Unit tests for the Enhanced Task Manager.
Run from the final_task_manager_project folder:
    python -m unittest discover -s tests -v
"""
import datetime
import json
import os
import tempfile
import unittest

from src.task import Task, DueDateTask, PriorityTask
from src.task_manager import TaskManager


class TaskModelTests(unittest.TestCase):
    def test_tags_are_normalised_and_unique(self):
        t = Task(1, "x", tags=["Work", " work ", "Home"])
        self.assertEqual(t.tags, ["work", "home"])

    def test_add_and_remove_tag(self):
        t = Task(1, "x")
        t.add_tag("Urgent")
        self.assertIn("urgent", t.tags)
        self.assertTrue(t.remove_tag("URGENT"))
        self.assertEqual(t.tags, [])

    def test_due_date_parsing(self):
        t = DueDateTask(1, "x", "2026-12-31")
        self.assertEqual(t.due_date, datetime.date(2026, 12, 31))
        with self.assertRaises(ValueError):
            DueDateTask(2, "y", "31-12-2026")

    def test_priority_validation(self):
        self.assertEqual(PriorityTask(1, "x", "high").priority, "High")
        with self.assertRaises(ValueError):
            PriorityTask(2, "y", "urgent")

    def test_str_shows_tags_last(self):
        t = PriorityTask(1, "x", "Low", tags=["a"])
        self.assertTrue(str(t).endswith("Priority: Low | Tags: a"))


class TaskManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "tasks.json")
        self.m = TaskManager(self.path)
        self.m.add_normal_task("Buy milk", tags=["home"])
        self.m.add_due_date_task("Write report", "2026-11-01", tags=["work", "urgent"])
        self.m.add_priority_task("Fix bug", "High", tags=["work"])
        self.m.add_due_date_task("Pay bills", "2026-10-15", tags=["home", "urgent"])
        self.m.add_priority_task("Read book", "Low")

    def tearDown(self):
        self.tmp.cleanup()

    def test_ids_and_persistence(self):
        self.assertEqual([t.id for t in self.m.tasks], [1, 2, 3, 4, 5])
        reloaded = TaskManager(self.path)
        self.assertEqual(len(reloaded.tasks), 5)
        self.assertIsInstance(reloaded.get_task_by_id(2), DueDateTask)
        self.assertIsInstance(reloaded.get_task_by_id(3), PriorityTask)
        self.assertEqual(reloaded.get_task_by_id(2).tags, ["work", "urgent"])
        self.assertEqual(reloaded.next_id, 6)

    def test_invalid_inputs_return_none(self):
        self.assertIsNone(self.m.add_due_date_task("bad", "not-a-date"))
        self.assertIsNone(self.m.add_priority_task("bad", "Critical"))
        self.assertEqual(len(self.m.tasks), 5)

    def test_complete_and_delete(self):
        self.assertTrue(self.m.complete_task(1)[0])
        self.assertFalse(self.m.complete_task(1)[0])
        self.assertFalse(self.m.complete_task(99)[0])
        self.assertTrue(self.m.delete_task(5)[0])
        self.assertFalse(self.m.delete_task(5)[0])

    def test_search_case_insensitive_partial(self):
        self.assertEqual([t.id for t in self.m.search_tasks("REP")], [2])
        self.assertEqual([t.id for t in self.m.search_tasks("urg")], [2, 4])
        self.assertEqual(self.m.search_tasks(""), [])

    def test_filter_combined(self):
        self.m.complete_task(4)
        r = self.m.filter_tasks(status=False, contains_tags=["work"])
        self.assertEqual([t.id for t in r], [2, 3])
        r = self.m.filter_tasks(due_date_before=datetime.date(2026, 10, 31))
        self.assertEqual([t.id for t in r], [4])
        r = self.m.filter_tasks(due_date_after=datetime.date(2026, 10, 1),
                                contains_tags=["URGENT"], status=False)
        self.assertEqual([t.id for t in r], [2])
        self.assertEqual([t.id for t in self.m.filter_tasks(priority_level="high")], [3])

    def test_sort_due_date_missing_last(self):
        asc = [t.id for t in self.m.sort_tasks("due_date")]
        desc = [t.id for t in self.m.sort_tasks("due_date", reverse=True)]
        self.assertEqual(asc, [4, 2, 1, 3, 5])
        self.assertEqual(desc, [2, 4, 1, 3, 5])

    def test_sort_priority(self):
        self.assertEqual([t.id for t in self.m.sort_tasks("priority")], [3, 5, 1, 2, 4])

    def test_sort_description_and_unknown(self):
        self.assertEqual([t.id for t in self.m.sort_tasks("description")], [1, 3, 4, 5, 2])
        self.assertEqual([t.id for t in self.m.sort_tasks("nope", reverse=True)], [5, 4, 3, 2, 1])

    def test_corrupted_file(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{ not json")
        self.assertEqual(TaskManager(self.path).tasks, [])

    def test_old_file_without_tags(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([{"id": 1, "description": "old", "completed": False, "_type": "Task"}], f)
        self.assertEqual(TaskManager(self.path).tasks[0].tags, [])


if __name__ == "__main__":
    unittest.main()
