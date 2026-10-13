# enhanced-task-manager-design/src/cli_interface.py
"""User Interface Layer: รับ input / แสดงผล เท่านั้น ไม่มี business logic"""
import datetime


class CLIInterface:
    SORT_OPTIONS = ["id", "due_date", "priority", "description", "status"]

    def __init__(self, task_manager):
        self.manager = task_manager

    # ---------- display ----------
    def display_menu(self):
        print("\n" + "=" * 50)
        print("       Enhanced Task Manager (Week 11)")
        print("=" * 50)
        print("1. เพิ่มงานทั่วไป (Add Normal Task)")
        print("2. เพิ่มงานที่มีวันครบกำหนด (Add Due Date Task)")
        print("3. เพิ่มงานที่มีระดับความสำคัญ (Add Priority Task)")
        print("4. แสดงรายการงานทั้งหมด (List All Tasks)")
        print("5. เปลี่ยนสถานะงานเป็นเสร็จสิ้น (Complete Task)")
        print("6. ลบงาน (Delete Task)")
        print("7. ค้นหางาน (Search Tasks)")
        print("8. กรองงาน (Filter Tasks)")
        print("9. เรียงลำดับงาน (Sort Tasks)")
        print("0. ออกจากโปรแกรม (Exit)")
        print("-" * 50)

    def show_tasks(self, tasks, title):
        print(f"\n--- {title} ({len(tasks)} รายการ) ---")
        if not tasks:
            print("(ไม่พบงาน)")
        for t in tasks:
            print(f"- {t}")
        print("-" * 50)

    # ---------- inputs ----------
    def get_user_choice(self):
        return input("เลือกเมนู (0-9): ").strip()

    def get_task_description(self):
        while True:
            desc = input("กรอกรายละเอียดงาน (Description): ").strip()
            if desc:
                return desc
            print("ข้อผิดพลาด: รายละเอียดงานต้องไม่เป็นค่าว่าง กรุณาลองใหม่อีกครั้ง")

    def get_date_input(self, prompt, optional=False):
        while True:
            s = input(prompt).strip()
            if optional and not s:
                return None
            try:
                datetime.datetime.strptime(s, "%Y-%m-%d")
                return s
            except ValueError:
                print("รูปแบบวันที่ไม่ถูกต้อง กรุณาใช้ YYYY-MM-DD (เช่น 2026-12-31)")

    def get_priority_input(self, optional=False):
        while True:
            p = input("กรอกระดับความสำคัญ (High/Medium/Low): ").strip().capitalize()
            if optional and not p:
                return None
            if p in ("High", "Medium", "Low"):
                return p
            print("ระดับความสำคัญไม่ถูกต้อง กรุณากรอก High, Medium หรือ Low")

    def get_tags_input(self, prompt=None):
        prompt = prompt or "กรอกป้ายกำกับ (Tags คั่นด้วยจุลภาค เช่น work,urgent - หรือเว้นว่างได้): "
        s = input(prompt).strip()
        return [t.strip() for t in s.split(",") if t.strip()]

    def get_task_id(self, prompt):
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("ข้อผิดพลาด: กรุณากรอก ID เป็นตัวเลข")
            return None

    # ---------- menu handlers ----------
    def handle_add_normal(self):
        desc = self.get_task_description()
        tags = self.get_tags_input()
        t = self.manager.add_normal_task(desc, tags=tags)
        print(f"[สำเร็จ]: เพิ่มงานทั่วไป ID {t.id} เรียบร้อยแล้ว")

    def handle_add_due(self):
        desc = self.get_task_description()
        due = self.get_date_input("กรอกวันครบกำหนด (YYYY-MM-DD): ")
        tags = self.get_tags_input()
        t = self.manager.add_due_date_task(desc, due, tags=tags)
        print(f"[สำเร็จ]: เพิ่มงานครบกำหนด ID {t.id} (ครบกำหนด: {due}) เรียบร้อยแล้ว")

    def handle_add_priority(self):
        desc = self.get_task_description()
        pr = self.get_priority_input()
        tags = self.get_tags_input()
        t = self.manager.add_priority_task(desc, pr, tags=tags)
        print(f"[สำเร็จ]: เพิ่มงานสำคัญ ID {t.id} (Priority: {pr}) เรียบร้อยแล้ว")

    def handle_list(self):
        self.show_tasks(self.manager.get_all_tasks(), "รายการงานทั้งหมด")

    def handle_complete(self):
        tid = self.get_task_id("กรอก ID งานที่ต้องการทำเครื่องหมายว่าเสร็จ: ")
        if tid is not None:
            ok, msg = self.manager.complete_task(tid)
            print(f"[{'สำเร็จ' if ok else 'แจ้งเตือน'}]: {msg}")

    def handle_delete(self):
        tid = self.get_task_id("กรอก ID งานที่ต้องการลบ: ")
        if tid is not None:
            ok, msg = self.manager.delete_task(tid)
            print(f"[{'สำเร็จ' if ok else 'แจ้งเตือน'}]: {msg}")

    def handle_search(self):
        kw = input("กรอกคำค้นหา (ค้นใน Description และ Tags): ").strip()
        if not kw:
            print("ข้อผิดพลาด: คำค้นหาต้องไม่เป็นค่าว่าง")
            return
        self.show_tasks(self.manager.search_tasks(kw), f"ผลการค้นหา '{kw}'")

    def handle_filter(self):
        print("\nกรองงาน (เว้นว่างข้อใดก็ได้ = ไม่ใช้เงื่อนไขนั้น)")
        s = input("สถานะ (done = เสร็จแล้ว / pending = ยังไม่เสร็จ): ").strip().lower()
        status = {"done": True, "completed": True, "pending": False}.get(s)
        before = self.get_date_input("ครบกำหนดก่อนหรือในวันที่ (YYYY-MM-DD): ", optional=True)
        after = self.get_date_input("ครบกำหนดหลังหรือในวันที่ (YYYY-MM-DD): ", optional=True)
        priority = self.get_priority_input(optional=True)
        tags = self.get_tags_input("ต้องมี Tags (คั่นด้วยจุลภาค): ")

        result = self.manager.filter_tasks(status=status, due_date_before=before,
                                           due_date_after=after, priority=priority,
                                           tags=tags or None)
        self.show_tasks(result, "ผลการกรองงาน")

    def handle_sort(self):
        print(f"เรียงตาม: {', '.join(self.SORT_OPTIONS)}")
        c = input("เลือกเกณฑ์ (ค่าเริ่มต้น: id): ").strip().lower() or "id"
        if c not in self.SORT_OPTIONS:
            print(f"เกณฑ์ '{c}' ไม่ถูกต้อง ใช้ 'id' แทน")
            c = "id"
        rev = input("เรียงจากมากไปน้อย? (y/n, ค่าเริ่มต้น: n): ").strip().lower() in ("y", "yes")
        self.show_tasks(self.manager.sort_tasks(c, rev),
                        f"เรียงตาม {c} ({'มาก→น้อย' if rev else 'น้อย→มาก'})")

    # ---------- main loop ----------
    def run(self):
        actions = {
            "1": self.handle_add_normal,
            "2": self.handle_add_due,
            "3": self.handle_add_priority,
            "4": self.handle_list,
            "5": self.handle_complete,
            "6": self.handle_delete,
            "7": self.handle_search,
            "8": self.handle_filter,
            "9": self.handle_sort,
        }
        while True:
            self.display_menu()
            choice = self.get_user_choice()
            if choice == "0":
                print("ออกจากโปรแกรม ขอบคุณที่ใช้งาน!")
                break
            action = actions.get(choice)
            if action:
                action()
            else:
                print("ข้อผิดพลาด: กรุณาเลือกเมนู 0-9")
