# enhanced-task-manager-design/src/task_manager.py
"""Business Logic Layer: จัดการรายการงาน (ไม่มี I/O กับไฟล์หรือผู้ใช้โดยตรง)"""
import datetime

from .task import Task, DueDateTask, PriorityTask
from .data_persistence import DataPersistence


class TaskManager:
    def __init__(self, data_file="data/tasks.json"):
        self.persistence = DataPersistence(data_file)
        self.tasks = self.persistence.load_tasks()
        self.next_id = self._get_next_task_id()

    # ---------- helpers ----------
    def _get_next_task_id(self):
        return max((t.id for t in self.tasks), default=0) + 1

    def _save_changes(self):
        self.persistence.save_tasks(self.tasks)

    def _add(self, task):
        self.tasks.append(task)
        self.next_id += 1
        self._save_changes()
        return task

    # ---------- CRUD ----------
    def add_normal_task(self, description, tags=None):
        return self._add(Task(self.next_id, description, tags=tags))

    def add_due_date_task(self, description, due_date_str, tags=None):
        return self._add(DueDateTask(self.next_id, description, due_date_str, tags=tags))

    def add_priority_task(self, description, priority, tags=None):
        return self._add(PriorityTask(self.next_id, description, priority, tags=tags))

    def get_task_by_id(self, task_id):
        return next((t for t in self.tasks if t.id == task_id), None)

    def get_all_tasks(self):
        return list(self.tasks)

    def complete_task(self, task_id):
        task = self.get_task_by_id(task_id)
        if not task:
            return False, "ไม่พบงาน (Task not found)"
        if task.completed:
            return False, "งานนี้เสร็จสิ้นไปแล้ว (Task is already completed)"
        task.mark_complete()
        self._save_changes()
        return True, f"งาน ID {task_id} เปลี่ยนสถานะเป็นเสร็จสิ้นแล้ว"

    def delete_task(self, task_id):
        task = self.get_task_by_id(task_id)
        if not task:
            return False, "ไม่พบงาน (Task not found)"
        self.tasks.remove(task)
        self._save_changes()
        return True, f"ลบงาน ID {task_id} เรียบร้อยแล้ว"

    # ---------- Search / Filter / Sort ----------
    def search_tasks(self, keyword):
        """ค้นหา keyword (ไม่สนตัวพิมพ์เล็ก/ใหญ่) ใน description หรือ tags"""
        kw = keyword.strip().lower()
        if not kw:
            return []
        return [
            t for t in self.tasks
            if kw in t.description.lower() or any(kw in tag.lower() for tag in t.tags)
        ]

    def filter_tasks(self, status=None, due_date_before=None, due_date_after=None,
                     priority=None, tags=None):
        """
        กรองงานตามเงื่อนไข (ทุกเงื่อนไขเป็น AND, ค่า None = ไม่กรอง)
        status: True=เสร็จแล้ว, False=ยังไม่เสร็จ
        due_date_before / due_date_after: 'YYYY-MM-DD' (รวมวันนั้นด้วย)
        priority: 'High' / 'Medium' / 'Low'
        tags: list ของ tag ที่งานต้องมีครบทุกตัว
        """
        result = list(self.tasks)

        if status is not None:
            result = [t for t in result if t.completed == status]

        if due_date_before or due_date_after:
            result = [t for t in result if isinstance(t, DueDateTask)]
            if due_date_before:
                before = datetime.datetime.strptime(due_date_before, "%Y-%m-%d").date()
                result = [t for t in result if t.due_date <= before]
            if due_date_after:
                after = datetime.datetime.strptime(due_date_after, "%Y-%m-%d").date()
                result = [t for t in result if t.due_date >= after]

        if priority:
            result = [t for t in result
                      if isinstance(t, PriorityTask) and t.priority.lower() == priority.lower()]

        if tags:
            wanted = {tag.lower() for tag in tags}
            result = [t for t in result if wanted.issubset({tg.lower() for tg in t.tags})]

        return result

    def sort_tasks(self, criterion="id", reverse=False):
        """
        เรียงงานตาม id / due_date / priority / description / status
        งานที่ไม่มีค่าที่ใช้เรียง (เช่น Task ธรรมดาเมื่อเรียงตาม due_date)
        จะอยู่ท้ายรายการเสมอ ไม่ว่าจะ reverse หรือไม่
        """
        if criterion == "due_date":
            has = [t for t in self.tasks if isinstance(t, DueDateTask)]
            rest = [t for t in self.tasks if not isinstance(t, DueDateTask)]
            return sorted(has, key=lambda t: t.due_date, reverse=reverse) + rest

        if criterion == "priority":
            order = PriorityTask.PRIORITY_ORDER
            has = [t for t in self.tasks if isinstance(t, PriorityTask)]
            rest = [t for t in self.tasks if not isinstance(t, PriorityTask)]
            return sorted(has, key=lambda t: order.get(t.priority, 99), reverse=reverse) + rest

        if criterion == "description":
            return sorted(self.tasks, key=lambda t: t.description.lower(), reverse=reverse)

        if criterion == "status":
            return sorted(self.tasks, key=lambda t: (t.completed, t.id), reverse=reverse)

        # default: id (= ลำดับการสร้าง)
        return sorted(self.tasks, key=lambda t: t.id, reverse=reverse)
