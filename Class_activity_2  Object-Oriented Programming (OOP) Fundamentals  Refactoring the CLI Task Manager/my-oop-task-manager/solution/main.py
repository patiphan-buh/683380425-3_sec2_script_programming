# my-oop-task-manager/main.py
import os
import sys

# Make sure the project root is on the path so 'src' can be imported as a package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.task_manager import TaskManager  # noqa: E402


def display_menu():
    """Displays the main menu options to the user."""
    print("\n--- OOP Task Manager Menu ---")
    print("1. Add Task")
    print("2. List Tasks")
    print("3. Complete Task")
    print("4. Delete Task")
    print("5. Exit")
    print("-------------------------")


def read_task_id(prompt):
    """Reads an integer task ID from the user, or returns None if invalid."""
    try:
        return int(input(prompt).strip())
    except ValueError:
        print("Invalid input. Please enter a number for Task ID.")
        return None


def main():
    """Main function to run the Task Manager application."""
    manager = TaskManager()  # Create an instance of the TaskManager

    while True:
        display_menu()
        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            description = input("Enter task description: ").strip()
            if description:
                manager.add_task(description)
            else:
                print("Task description cannot be empty.")
        elif choice == "2":
            manager.list_tasks()
        elif choice == "3":
            task_id = read_task_id("Enter ID of task to complete: ")
            if task_id is not None:
                manager.complete_task(task_id)
        elif choice == "4":
            task_id = read_task_id("Enter ID of task to delete: ")
            if task_id is not None:
                manager.delete_task(task_id)
        elif choice == "5":
            print("Exiting Task Manager. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    main()
