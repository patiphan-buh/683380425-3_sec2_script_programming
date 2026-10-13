# Enhanced Task Manager (Week 11 – Project Planning & Design)

แอปพลิเคชัน Task Manager แบบ Command-Line (CLI) ที่ออกแบบด้วยหลัก **Modularity** และ **Separation of Concerns**
รองรับ **Tags, Search, Filter และ Sort** — รายละเอียดการออกแบบทั้งหมดอยู่ใน [`PLAN.md`](PLAN.md)

## Features

| เมนู | ฟีเจอร์ | สถานะ |
|---|---|---|
| 1–3 | เพิ่มงาน 3 ประเภท: Normal / Due Date / Priority (พร้อม Tags) | ✅ |
| 4 | แสดงงานทั้งหมด | ✅ |
| 5 | เปลี่ยนสถานะเป็นเสร็จสิ้น | ✅ |
| 6 | ลบงาน | ✅ |
| 7 | **Search** – ค้นหาคำใน Description และ Tags (ไม่สนตัวพิมพ์เล็ก/ใหญ่) | ✅ |
| 8 | **Filter** – กรองตามสถานะ, ช่วงวันครบกำหนด, Priority, Tags (รวมหลายเงื่อนไขได้) | ✅ |
| 9 | **Sort** – เรียงตาม id, due_date, priority, description, status (กลับลำดับได้) | ✅ |
| – | บันทึก/โหลดข้อมูลอัตโนมัติที่ `data/tasks.json` | ✅ |

## Architecture

```
main.py  ──►  CLIInterface (UI)  ──►  TaskManager (Business Logic)  ──►  DataPersistence (JSON I/O)
                                              │
                                              └──►  Task / DueDateTask / PriorityTask (Models)
```

| ไฟล์ | หน้าที่ |
|---|---|
| `src/task.py` | Data models + `to_dict()` / `__str__()` |
| `src/data_persistence.py` | อ่าน/เขียน JSON และแปลงกลับเป็น object ตาม `_type` |
| `src/task_manager.py` | Logic: add, complete, delete, search, filter, sort |
| `src/cli_interface.py` | เมนู, รับ input, ตรวจสอบรูปแบบ, แสดงผล |
| `main.py` | จุดเริ่มต้นโปรแกรม เชื่อมทุกส่วนเข้าด้วยกัน |

## How to Run

ต้องใช้ Python 3.8 ขึ้นไป (ไม่ต้องติดตั้ง library เพิ่ม)

```bash
git clone https://github.com/<YOUR_USERNAME>/enhanced-task-manager-design.git
cd enhanced-task-manager-design
python main.py
```

## Project Structure

```
enhanced-task-manager-design/
├── src/
│   ├── __init__.py
│   ├── task.py
│   ├── data_persistence.py
│   ├── task_manager.py
│   └── cli_interface.py
├── data/
│   └── tasks.json
├── main.py
├── .gitignore
├── README.md
└── PLAN.md
```

## Future Ideas

Reminders, Unit Tests, SQLite แทน JSON, GUI (Tkinter), Export CSV, Undo/Redo — ดูหัวข้อ 6 ใน `PLAN.md`
