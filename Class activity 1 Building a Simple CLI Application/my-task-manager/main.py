# my-task-manager/main.py
"""Presentation Layer: CLI menu & defensive input handling."""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import task_data
import task_logic


def display_menu():
    print("\n" + "=" * 34)
    print("         TASK MANAGER CLI")
    print("=" * 34)
    print("  1. Add New Task")
    print("  2. List All Tasks")
    print("  3. List Pending Tasks")
    print("  4. List Completed Tasks")
    print("  5. Search Tasks by Keyword")
    print("  6. Mark Task as Completed")
    print("  7. Delete Task")
    print("  8. Save and Exit")
    print("=" * 34)


def ask_task_id(prompt):
    """Asks for a task ID; returns int or None on invalid input."""
    try:
        return int(input(prompt).strip())
    except ValueError:
        print("Invalid input. Please enter a number for Task ID.")
        return None


def ask_priority():
    choice = input("Priority (1=High, 2=Medium, 3=Low) [2]: ").strip() or "2"
    if choice not in task_logic.PRIORITIES:
        print("Invalid priority. Using Medium.")
        choice = "2"
    return task_logic.PRIORITIES[choice]


def main():
    tasks = task_data.load_tasks()
    try:
        while True:
            display_menu()
            choice = input("Enter choice (1-8): ").strip()

            if choice == '1':
                description = input("Enter task description: ").strip()
                if description:
                    tasks = task_logic.add_task(tasks, description, ask_priority())
                    task_data.save_tasks(tasks)
                else:
                    print("Task description cannot be empty.")
            elif choice == '2':
                task_logic.list_tasks(tasks)
            elif choice == '3':
                task_logic.list_pending(tasks)
            elif choice == '4':
                task_logic.list_completed(tasks)
            elif choice == '5':
                keyword = input("Enter keyword: ").strip()
                if keyword:
                    task_logic.search_tasks(tasks, keyword)
                else:
                    print("Keyword cannot be empty.")
            elif choice == '6':
                task_id = ask_task_id("Enter ID of task to complete: ")
                if task_id is not None:
                    tasks = task_logic.complete_task(tasks, task_id)
                    task_data.save_tasks(tasks)
            elif choice == '7':
                task_id = ask_task_id("Enter ID of task to delete: ")
                if task_id is not None:
                    tasks = task_logic.delete_task(tasks, task_id)
                    task_data.save_tasks(tasks)
            elif choice == '8':
                print("Saving tasks and exiting. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 8.")
    except (KeyboardInterrupt, EOFError):
        print("\nInterrupted. Saving tasks...")
    finally:
        task_data.save_tasks(tasks)


if __name__ == "__main__":
    main()
