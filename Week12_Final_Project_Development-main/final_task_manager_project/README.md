# Week 12 Final Project: Enhanced Task Manager CLI

A command-line task manager written in Python that applies OOP, modular design,
JSON data persistence, `datetime`, error handling, and search / filter / sort logic.

**Student:** _(your name / student ID)_  
**Course:** Script Programming 1/2569

## Implemented Features

- **3 task types** – `Task`, `DueDateTask` (due date), `PriorityTask` (High / Medium / Low)
- **Tags** – every task can have many tags (normalised to lowercase, no duplicates)
- **CRUD** – add, list, complete, delete (with confirmation)
- **Search** – case-insensitive, partial match in description **and** tags
- **Filter** – combine criteria with AND: status, due before / after, priority, tags (must contain ALL)
- **Sort** – by `id`, `description`, `completed`, `due_date`, `priority`
  (ascending/descending; tasks without the attribute always go last)
- **Persistence** – auto-save to `data/tasks.json`, correct class restored on load;
  handles missing / corrupted files and old data without tags
- **Unit tests** – 15 tests with `unittest` in `tests/`

## How to Run

```bash
git clone https://github.com/<YOUR_USERNAME>/Week12_Final_Project_Development.git
cd Week12_Final_Project_Development/final_task_manager_project
python main.py
```

Run the tests:

```bash
cd final_task_manager_project
python -m unittest discover -s tests -v
```

Requires Python 3.8+ (no external packages).

## Menu

```
1. Add Normal Task     4. List All Tasks    7. Search Tasks
2. Add Due Date Task   5. Complete Task     8. Filter Tasks
3. Add Priority Task   6. Delete Task       9. Sort Tasks
0. Exit
```

## Project Structure

```
Week12_Final_Project_Development/
├── final_task_manager_project/
│   ├── data/
│   │   └── tasks.json            # pre-seeded demo tasks
│   ├── src/
│   │   ├── __init__.py
│   │   ├── task.py               # Task, DueDateTask, PriorityTask (models + tags)
│   │   ├── data_persistence.py   # JSON load / save
│   │   ├── task_manager.py       # business logic: CRUD, search, filter, sort
│   │   └── cli_interface.py      # menus, input validation, output
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_task_manager.py  # unit tests
│   ├── .gitignore
│   └── main.py                   # entry point
├── PLAN.md
├── README.md
└── SUBMISSION_CHECKLIST.md
```

## Architecture (Separation of Concerns)

`main.py` → creates `TaskManager` and `CLIInterface`  
`CLIInterface` (UI only) → calls `TaskManager` (logic only) → uses `DataPersistence` (file I/O only) → stores `Task` objects (models).

## Future Work

GUI (Tkinter), SQLite database, reminders for due tasks, recurring tasks,
CSV export, editing existing tasks, web interface (Flask).
