# Project Plan: Enhanced Task Manager CLI (Final Version)

## 1. Introduction
This document started as the Week 11 blueprint and now reflects the final state of the
Enhanced Task Manager CLI built in Week 12.

## 2. Requirements – Status

### 2.1 Functional
| Requirement | Status |
|---|---|
| Create / list / complete / delete tasks | Done |
| `DueDateTask` and `PriorityTask` types | Done |
| Tags on every task (`add_tag`, `remove_tag`) | Done |
| Search in description and tags (case-insensitive, partial) | Done |
| Filter by status, due date range, priority, tags (combined with AND) | Done |
| Sort by id, description, completed, due_date, priority | Done |
| Save / load all task types and tags in `data/tasks.json` | Done |

### 2.2 Non-functional
- **Usability:** clear menu, `[Success]` / `[Error]` / `[Info]` messages, task count in lists, delete confirmation.
- **Reliability:** input validation loops for dates and priorities; corrupted/missing JSON handled; Ctrl+C exits cleanly.
- **Maintainability:** one responsibility per module, docstrings, PEP 8 style.
- **Testability:** 15 unit tests using a temporary data file.

## 3. Architecture (As Implemented)
```
main.py ──► CLIInterface ──► TaskManager ──► DataPersistence ──► data/tasks.json
                                  │
                                  └── Task / DueDateTask / PriorityTask (src/task.py)
```

## 4. Implementation Details & Challenges

### 4.1 Tags
- `tags` is a list in the base `Task`; the constructor routes every tag through `add_tag`
  so tags are always lowercase, trimmed and unique.
- `load_tasks` uses `setdefault('tags', [])` so older JSON files without tags still load.
- `__str__` uses a small `_extra_info()` hook so subclasses insert *Due* / *Priority*
  before *Tags* without string splitting.

### 4.2 Search
- Keyword is lowercased and matched as a substring of the description or any tag.

### 4.3 Filter
- Criteria are applied one after another to narrow the list (logical AND).
- **Challenge – dates:** `isinstance(t, DueDateTask)` ensures only tasks with a due date
  are compared; dates are compared as `datetime.date` objects.
- **Challenge – tags:** `all(tag in t.tags for tag in wanted)` requires every tag.

### 4.4 Sort
- `sorted()` / `list.sort()` with `lambda` keys and `t.id` as a tie-breaker.
- **Challenge – polymorphic sorting:** using `date.max` / `99` as a placeholder moved tasks
  without the attribute to the *front* when sorting in reverse. Final solution: split the list
  into tasks with and without the attribute, sort only the first group, and append the second
  group at the end, so missing values are always last.
- `PRIORITY_MAP = {"High": 1, "Medium": 2, "Low": 3}` converts text to numbers.

### 4.5 Bug Found During Integration
- `main.py` added `src/` to `sys.path` and imported `task_manager` directly, but
  `task_manager.py` uses relative imports (`from .task import ...`), which raised
  `ImportError: attempted relative import with no known parent package`.
  **Fix:** add the project folder to `sys.path` and import `from src.task_manager import TaskManager`.

### 4.6 Debugging Lessons
- Separating modules made it easy to tell UI bugs (input parsing) from logic bugs (filter/sort).
- Unit tests with a temporary JSON file allowed testing logic without touching real data.
- The `logging` module (set to `INFO` in `main.py`) shows add/save/load events without extra `print`s.

## 5. Lessons Learned
- Plan first, then implement and test one feature at a time.
- Keep business logic out of the UI so it can be tested directly.
- Edge cases (empty input, wrong date format, missing attributes) need explicit handling.

## 6. Future Work
GUI, SQLite storage, reminders, recurring tasks, edit-task option, CSV export, web interface.
