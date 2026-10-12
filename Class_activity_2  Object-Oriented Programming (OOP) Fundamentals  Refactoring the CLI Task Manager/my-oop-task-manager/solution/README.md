# My OOP Task Manager CLI

A command-line task manager built with Object-Oriented Programming (OOP). This version refactors the earlier procedural Task Manager into two classes: `Task` and `TaskManager`.

## Features

* **Add Tasks** – add a new task with a description
* **List Tasks** – show every task with its ID, description and status (Pending / Completed)
* **Complete Tasks** – mark a task as completed by ID
* **Delete Tasks** – remove a task by ID
* **Persistence** – tasks are saved to `data/tasks.json` and loaded automatically on startup

## OOP Design

| Class | Attributes | Methods |
|---|---|---|
| `Task` | `id`, `description`, `completed` | `mark_complete()`, `to_dict()`, `__str__()`, `__repr__()` |
| `TaskManager` | `tasks` (list of `Task`), `next_id`, `data_file` | `add_task()`, `list_tasks()`, `complete_task()`, `delete_task()`, `_load_tasks()`, `_save_tasks()` |

* **Encapsulation** – each `Task` bundles its own data and behaviour; `TaskManager` hides file I/O behind the private helpers `_load_tasks()` / `_save_tasks()`.
* **JSON integration** – `Task.to_dict()` turns objects into dictionaries before saving; loading turns dictionaries back into `Task` objects.

## How to Run

```bash
git clone https://github.com/YOUR_USERNAME/my-oop-task-manager.git
cd my-oop-task-manager/solution
python main.py
```

## Run the Tests

```bash
cd solution
python -m unittest discover -s tests -t . -v
```

## Example Output

```
--- Your Tasks ---
ID: 1 | Description: Task 1 | Status: Pending
ID: 2 | Description: Task 2 | Status: Completed
------------------
```

## Project Structure

```
solution/
├── src/
│   ├── __init__.py        # Makes 'src' a Python package
│   ├── task.py            # Task class
│   └── task_manager.py    # TaskManager class (logic + persistence)
├── tests/
│   ├── __init__.py
│   ├── test_task.py
│   └── test_task_manager.py
├── data/
│   └── tasks.json         # Created/managed by the app
├── main.py                # CLI entry point
├── .gitignore
└── README.md
```

## License

MIT
