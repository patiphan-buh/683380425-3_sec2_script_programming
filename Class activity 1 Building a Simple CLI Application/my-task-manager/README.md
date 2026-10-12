# Week 7: Building a Simple CLI Application, Error Handling & Project Structure

A command-line Task Manager written in Python. Add, list, search, complete and delete tasks; everything is saved to `data/tasks.json` automatically.

## Features
- **Add Task** – description + priority (High / Medium / Low), unique ID assigned automatically
- **List All / Pending / Completed** – formatted table with `[DONE]` / `[PENDING]` status and a summary
- **Search** – find tasks by keyword (case-insensitive)
- **Mark as Completed** / **Delete** – by task ID
- **Persistence** – JSON file I/O, saved after every change and on exit
- **Error handling** – `try-except` for invalid IDs (`ValueError`), corrupted JSON (`JSONDecodeError`), missing file, Ctrl+C

## How to Run
```bash
git clone https://github.com/YOUR_USERNAME/my-task-manager.git
cd my-task-manager
python main.py
```

## โครงสร้างภายในคลังข้อมูล (Directory Overview)
```
my-task-manager/
├── src/
│   ├── __init__.py      # ทำให้ src เป็น Python package
│   ├── task_data.py     # Data Layer (Load/Save JSON)
│   └── task_logic.py    # Business Logic Layer (Add, List, Complete, Delete, Search)
├── data/
│   └── tasks.json       # Persistent JSON storage (สร้างอัตโนมัติ)
├── main.py              # Presentation Layer (CLI Menu & Defensive Input)
├── .gitignore           # Gitignore สำหรับโปรเจกต์ย่อย
└── README.md
```

## Example Output (menu 2)
```
================================================================
ID      | Status      | Priority  | Description
----------------------------------------------------------------
#1      | [DONE]      | Medium    | 101
#2      | [PENDING]   | Low       | 102
================================================================
Summary: 1/2 task(s) completed.
```
