"""
cli_interface.py
User interface layer: menus, input validation and output.
Contains no business logic; it calls TaskManager methods.
"""
import datetime

LINE = "=" * 34
DASH = "-" * 34


class CLIInterface:
    def __init__(self, task_manager):
        self.manager = task_manager

    # ---------- display ----------
    def display_menu(self):
        print("\n" + LINE)
        print("--- Enhanced Task Manager Menu ---")
        print(LINE)
        print("1. Add Normal Task")
        print("2. Add Due Date Task")
        print("3. Add Priority Task")
        print("4. List All Tasks")
        print("5. Complete Task")
        print("6. Delete Task")
        print("7. Search Tasks")
        print("8. Filter Tasks")
        print("9. Sort Tasks")
        print("0. Exit")
        print(DASH)

    def _display_tasks(self, tasks, title="Tasks"):
        print()
        if not tasks:
            print(f"--- {title} ---")
            print("  (no tasks found)")
            print(DASH)
            return
        print(f"--- {title} (Total: {len(tasks)}) ---")
        for task in tasks:
            print(f"  * {task}")
        print(DASH)

    # ---------- input helpers ----------
    def get_user_choice(self):
        return input("Enter your choice (0-9): ").strip()

    def get_task_description(self):
        while True:
            description = input("Enter task description: ").strip()
            if description:
                return description
            print("[Error] Task description cannot be empty. Please try again.")

    def get_due_date_input(self):
        while True:
            value = input("Enter due date (YYYY-MM-DD): ").strip()
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
                return value
            except ValueError:
                print("[Error] Invalid date format. Please use YYYY-MM-DD (e.g., 2026-12-31).")

    def get_priority_input(self):
        while True:
            priority = input("Enter priority (High/Medium/Low): ").strip().capitalize()
            if priority in ("High", "Medium", "Low"):
                return priority
            print("[Error] Invalid priority. Please enter 'High', 'Medium', or 'Low'.")

    @staticmethod
    def _parse_tags(text):
        return [t.strip().lower() for t in text.split(",") if t.strip()]

    def get_tags_input(self):
        text = input("Enter tags (comma-separated, e.g., study,project,urgent - optional): ").strip()
        return self._parse_tags(text)

    def _get_task_id(self, action):
        raw = input(f"Enter ID of task to {action}: ").strip()
        try:
            return int(raw)
        except ValueError:
            print("[Error] Invalid input. Please enter a number for Task ID.")
            return None

    def _optional_date(self, prompt):
        while True:
            raw = input(prompt).strip()
            if not raw:
                return None
            try:
                return datetime.datetime.strptime(raw, "%Y-%m-%d").date()
            except ValueError:
                print("[Error] Invalid date format. Use YYYY-MM-DD or leave blank.")

    # ---------- actions ----------
    def _add_normal(self):
        description = self.get_task_description()
        tags = self.get_tags_input()
        task = self.manager.add_normal_task(description, tags=tags)
        print(f"[Success] Normal Task '{task.description}' added with ID {task.id}.")

    def _add_due_date(self):
        description = self.get_task_description()
        due = self.get_due_date_input()
        tags = self.get_tags_input()
        task = self.manager.add_due_date_task(description, due, tags=tags)
        if task:
            print(f"[Success] Due Date Task '{task.description}' "
                  f"(Due: {task.due_date:%Y-%m-%d}) added with ID {task.id}.")
        else:
            print("[Error] Failed to add Due Date Task. Please check your input.")

    def _add_priority(self):
        description = self.get_task_description()
        priority = self.get_priority_input()
        tags = self.get_tags_input()
        task = self.manager.add_priority_task(description, priority, tags=tags)
        if task:
            print(f"[Success] Priority Task '{task.description}' "
                  f"(Priority: {task.priority}) added with ID {task.id}.")
        else:
            print("[Error] Failed to add Priority Task. Please check your input.")

    def _complete(self):
        task_id = self._get_task_id("complete")
        if task_id is not None:
            ok, msg = self.manager.complete_task(task_id)
            print(f"[{'Success' if ok else 'Info'}] {msg}")

    def _delete(self):
        task_id = self._get_task_id("delete")
        if task_id is None:
            return
        task = self.manager.get_task_by_id(task_id)
        if task is None:
            print(f"[Info] Task ID {task_id} not found.")
            return
        confirm = input(f"Delete '{task.description}'? (y/n): ").strip().lower()
        if confirm in ("y", "yes"):
            ok, msg = self.manager.delete_task(task_id)
            print(f"[{'Success' if ok else 'Info'}] {msg}")
        else:
            print("[Info] Delete cancelled.")

    def _search(self):
        keyword = input("Enter search keyword (in description or tags): ").strip()
        if not keyword:
            print("[Error] Keyword cannot be empty.")
            return
        self._display_tasks(self.manager.search_tasks(keyword),
                            f"Search Results for '{keyword}'")

    def _filter(self):
        print("\n--- Filter Tasks (leave blank to skip a criterion) ---")
        raw = input("Filter by completed status (yes/no): ").strip().lower()
        status = True if raw in ("yes", "y") else False if raw in ("no", "n") else None
        before = self._optional_date("Due on or before (YYYY-MM-DD): ")
        after = self._optional_date("Due on or after (YYYY-MM-DD): ")
        raw = input("Priority (High/Medium/Low): ").strip().capitalize()
        priority = raw if raw in ("High", "Medium", "Low") else None
        tags = self._parse_tags(input("Tags (comma-separated, must have ALL): ")) or None
        result = self.manager.filter_tasks(status=status, due_date_before=before,
                                           due_date_after=after, priority_level=priority,
                                           contains_tags=tags)
        self._display_tasks(result, "Filtered Tasks")

    def _sort(self):
        print("\n--- Sort Tasks ---")
        print("Available criteria: " + ", ".join(self.manager.SORT_CRITERIA))
        criterion = input("Sort by (default: id): ").strip().lower() or "id"
        if criterion not in self.manager.SORT_CRITERIA:
            print(f"[Info] Unknown criterion '{criterion}'. Sorting by id.")
            criterion = "id"
        reverse = input("Reverse order (yes/no, default: no): ").strip().lower() in ("yes", "y")
        result = self.manager.sort_tasks(criterion, reverse)
        order = "Descending" if reverse else "Ascending"
        self._display_tasks(result, f"Sorted by {criterion} ({order})")

    def run(self):
        actions = {
            "1": self._add_normal,
            "2": self._add_due_date,
            "3": self._add_priority,
            "4": lambda: self._display_tasks(self.manager.get_all_tasks(), "Your Tasks"),
            "5": self._complete,
            "6": self._delete,
            "7": self._search,
            "8": self._filter,
            "9": self._sort,
        }
        while True:
            self.display_menu()
            try:
                choice = self.get_user_choice()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting Task Manager. Goodbye!")
                break
            if choice == "0":
                print("Exiting Task Manager. Goodbye!")
                break
            action = actions.get(choice)
            if action is None:
                print("[Error] Invalid choice. Please enter a number between 0 and 9.")
                continue
            try:
                action()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting Task Manager. Goodbye!")
                break
