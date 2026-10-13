# enhanced-task-manager-design/src/data_persistence.py
"""Data Layer: จัดการโหลด/บันทึกงานกับไฟล์ JSON ทั้งหมดไว้ที่เดียว"""
import json
import os

from .task import Task, DueDateTask, PriorityTask

TASK_TYPES = {
    "Task": Task,
    "DueDateTask": DueDateTask,
    "PriorityTask": PriorityTask,
}


class DataPersistence:
    def __init__(self, data_file="data/tasks.json"):
        self.data_file = data_file
        project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        self._data_file_path = os.path.normpath(os.path.join(project_root, data_file))

    def load_tasks(self):
        """โหลดงานจาก JSON และสร้าง object ตาม '_type'"""
        if not os.path.exists(self._data_file_path):
            os.makedirs(os.path.dirname(self._data_file_path), exist_ok=True)
            return []
        try:
            with open(self._data_file_path, "r", encoding="utf-8") as f:
                raw_tasks = json.load(f)
        except json.JSONDecodeError:
            print("Warning: tasks.json ว่างหรือเสียหาย เริ่มต้นด้วยรายการว่าง")
            return []

        loaded = []
        for t_dict in raw_tasks:
            task_type = t_dict.pop("_type", "Task")
            t_dict.setdefault("tags", [])
            cls = TASK_TYPES.get(task_type)
            if cls is None:
                print(f"Warning: ไม่รู้จักประเภทงาน '{task_type}' ข้าม ID {t_dict.get('id', 'N/A')}")
                continue
            try:
                loaded.append(cls(**t_dict))
            except (TypeError, ValueError) as e:
                print(f"Warning: ข้อมูลงาน ID {t_dict.get('id', 'N/A')} ไม่ถูกต้อง ({e})")
        return loaded

    def save_tasks(self, tasks):
        """บันทึกงานทั้งหมดลง JSON (ใช้ to_dict แบบ polymorphic)"""
        os.makedirs(os.path.dirname(self._data_file_path), exist_ok=True)
        with open(self._data_file_path, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in tasks], f, indent=4, ensure_ascii=False)
