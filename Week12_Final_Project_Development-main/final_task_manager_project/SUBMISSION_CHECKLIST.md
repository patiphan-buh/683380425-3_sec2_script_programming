# Submission Checklist – Lab 12

## Required
- [ ] GitHub repository link (public)
- [ ] Screenshot(s) showing at least 2 menu options being used

## Code
- [x] `src/task.py` – Task, DueDateTask, PriorityTask with tags, add_tag/remove_tag
- [x] `src/data_persistence.py` – JSON load/save for all task types
- [x] `src/task_manager.py` – CRUD + search + filter + sort
- [x] `src/cli_interface.py` – menu 0-9 with input validation
- [x] `main.py` – entry point (import bug fixed)
- [x] `data/tasks.json` – pre-seeded demo tasks
- [x] `tests/test_task_manager.py` – 15 unit tests passing
- [x] `README.md`, `PLAN.md` updated

## Suggested screenshots
1. Option **4** – List All Tasks
2. Option **7** – Search Tasks (keyword: `urgent`)
3. Option **8** – Filter Tasks (status `no`, tags `study`)
4. Option **9** – Sort Tasks (criterion `priority`)
5. (bonus) `python -m unittest discover -s tests -v` → OK
