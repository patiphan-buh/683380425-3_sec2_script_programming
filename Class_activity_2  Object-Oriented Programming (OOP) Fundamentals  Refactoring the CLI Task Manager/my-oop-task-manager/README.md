# Week 8 – Class Activity 2: OOP Fundamentals & Refactoring the CLI Task Manager

Refactors the procedural CLI Task Manager into an object-oriented design with a `Task` class and a `TaskManager` class, with JSON persistence.

| Folder | What's inside |
|---|---|
| [`solution/`](solution/) | VS Code version: `src/task.py`, `src/task_manager.py`, `main.py`, unit tests |
| [`colab/`](colab/) | `Week8_OOP_TaskManager_Lab.ipynb` – the same project as a Colab notebook (open it and choose **Runtime → Run all**) |

## Quick start

```bash
cd solution
python main.py                                  # run the CLI
python -m unittest discover -s tests -t . -v    # run the tests (11 tests)
```

## Result

```
--- Your Tasks ---
ID: 1 | Description: Task 1 | Status: Pending
ID: 2 | Description: Task 2 | Status: Completed
------------------
```
