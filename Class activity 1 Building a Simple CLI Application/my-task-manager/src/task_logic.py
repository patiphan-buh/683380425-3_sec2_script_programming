# my-task-manager/src/task_logic.py
"""Business Logic Layer: add, list, complete, delete, search tasks."""

PRIORITIES = {"1": "High", "2": "Medium", "3": "Low"}


def get_next_task_id(tasks):
    """Generates a unique ID for a new task."""
    if not tasks:
        return 1
    return max(task['id'] for task in tasks) + 1


def add_task(tasks, description, priority="Medium"):
    """Adds a new task to the list."""
    task_id = get_next_task_id(tasks)
    tasks.append({
        "id": task_id,
        "description": description,
        "priority": priority,
        "completed": False,
    })
    print(f"Task '{description}' added with ID {task_id}.")
    return tasks


def print_table(tasks, title=None):
    """Prints tasks as a formatted table."""
    line = "=" * 64
    if title:
        print(f"\n{title}")
    if not tasks:
        print("No tasks found.")
        return
    print("\n" + line)
    print(f"{'ID':<8}| {'Status':<12}| {'Priority':<10}| Description")
    print("-" * 64)
    for task in tasks:
        status = "[DONE]" if task.get('completed') else "[PENDING]"
        print(f"{'#' + str(task['id']):<8}| {status:<12}| "
              f"{task.get('priority', 'Medium'):<10}| {task['description']}")
    print(line)


def list_tasks(tasks):
    """Lists all tasks with a completion summary."""
    print_table(tasks)
    if tasks:
        done = sum(1 for t in tasks if t.get('completed'))
        print(f"Summary: {done}/{len(tasks)} task(s) completed.")


def list_pending(tasks):
    print_table([t for t in tasks if not t.get('completed')], "Pending Tasks")


def list_completed(tasks):
    print_table([t for t in tasks if t.get('completed')], "Completed Tasks")


def search_tasks(tasks, keyword):
    """Finds tasks whose description contains the keyword (case-insensitive)."""
    kw = keyword.lower()
    print_table([t for t in tasks if kw in t['description'].lower()],
                f"Search results for '{keyword}'")


def complete_task(tasks, task_id):
    """Marks a task as completed."""
    for task in tasks:
        if task['id'] == task_id:
            if task['completed']:
                print(f"Task ID {task_id} is already completed.")
            else:
                task['completed'] = True
                print(f"Task ID {task_id} marked as completed.")
            return tasks
    print(f"Error: Task with ID {task_id} not found.")
    return tasks


def delete_task(tasks, task_id):
    """Deletes a task from the list."""
    original_len = len(tasks)
    tasks[:] = [task for task in tasks if task['id'] != task_id]
    if len(tasks) < original_len:
        print(f"Task ID {task_id} deleted successfully.")
    else:
        print(f"Error: Task with ID {task_id} not found.")
    return tasks
