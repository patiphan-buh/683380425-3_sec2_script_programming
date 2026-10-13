# Project Plan: Enhanced Task Manager CLI

## 1. Introduction
เอกสารนี้คือแผนการพัฒนา Task Manager แบบ CLI เวอร์ชันปรับปรุง ต่อยอดจากเวอร์ชันก่อนหน้า
โดยเน้น **ความเป็นโมดูล (Modularity)**, **การแยกหน้าที่ (Separation of Concerns)** และฟีเจอร์ใหม่
ได้แก่ **Tags, Search, Filter, Sort** เพื่อให้ดูแลรักษาและต่อยอดได้ง่าย

**ปัญหาที่ต้องการแก้:** เวอร์ชันเดิมรวม input/output, logic และการอ่าน/เขียนไฟล์ไว้ปนกัน
ทำให้เพิ่มฟีเจอร์ยากและเสี่ยงเกิด "Spaghetti Code" อีกทั้งเมื่อมีงานจำนวนมากผู้ใช้หางานที่ต้องการได้ยาก

## 2. Requirements

### 2.1 Functional Requirements
| ID | Requirement |
|---|---|
| FR-1 | สร้างงานทั่วไปที่มี description, สถานะ (เริ่มต้น Pending) และ tags (ไม่บังคับ) |
| FR-2 | สร้าง Due Date Task (วันที่รูปแบบ YYYY-MM-DD) |
| FR-3 | สร้าง Priority Task (High / Medium / Low) |
| FR-4 | แสดงงานทั้งหมดพร้อมรายละเอียดเฉพาะประเภทและ tags |
| FR-5 | ทำเครื่องหมายงานว่าเสร็จสิ้นด้วย ID |
| FR-6 | ลบงานด้วย ID |
| FR-7 | **Search:** ค้นหาคำใน description หรือ tags (case-insensitive) |
| FR-8 | **Filter:** กรองตามสถานะ, ช่วงวันครบกำหนด (before/after), priority, tags — รวมหลายเงื่อนไขแบบ AND |
| FR-9 | **Sort:** เรียงตาม id (ลำดับการสร้าง), due_date, priority, description, status และกลับลำดับได้ |
| FR-10 | บันทึกลง `data/tasks.json` ทุกครั้งที่มีการเปลี่ยนแปลง และโหลดกลับเป็น object ที่ถูกประเภทตอนเปิดโปรแกรม |

### 2.2 Non-Functional Requirements
- **Usability:** เมนูสองภาษา (ไทย/อังกฤษ) ชัดเจน, ช่องที่ไม่บังคับเว้นว่างได้
- **Reliability:** ตรวจสอบ input ทุกจุด (วันที่, ID ที่ไม่ใช่ตัวเลข, priority, ค่าว่าง) โดยโปรแกรมไม่ crash; ไฟล์ JSON เสียหายต้องไม่ทำให้โปรแกรมพัง
- **Maintainability:** แต่ละโมดูลมีหน้าที่เดียว มี docstring อธิบาย
- **Extensibility:** เพิ่มประเภทงานใหม่ได้โดยแก้เฉพาะ `task.py` และ map `TASK_TYPES`; เปลี่ยนจาก JSON เป็น SQLite ได้โดยแก้เฉพาะ `data_persistence.py`
- **Performance:** หลักร้อยงานต้องตอบสนองทันที (ทุก operation เป็น O(n) หรือ O(n log n))

## 3. High-Level Design / Architecture

```
┌──────────┐     ┌────────────────┐     ┌───────────────┐     ┌───────────────────┐
│ main.py  │ ──► │ CLIInterface   │ ──► │ TaskManager   │ ──► │ DataPersistence   │ ──► data/tasks.json
│(orchestr)│     │ (UI layer)     │     │ (logic layer) │     │ (data layer)      │
└──────────┘     └────────────────┘     └───────┬───────┘     └───────────────────┘
                                                │ ใช้
                                        ┌───────▼────────┐
                                        │ task.py models │  Task ◄── DueDateTask
                                        └────────────────┘       ◄── PriorityTask
```
ทิศทางการพึ่งพาเป็นทางเดียว: UI รู้จัก Logic, Logic รู้จัก Data — แต่ Logic ไม่เคย `print`/`input` และ UI ไม่เคยแตะไฟล์

### 3.1 Module Responsibilities
- **`task.py` (Models)** — `Task`, `DueDateTask`, `PriorityTask`; เมธอด `mark_complete`, `add_tag`, `remove_tag`, `to_dict`, `__str__`, `__repr__`; subclass override `_extra_str()` แทนการตัดต่อ string ซ้ำ (DRY)
- **`data_persistence.py` (Data Layer)** — อ่าน/เขียน JSON (UTF-8 รองรับภาษาไทย), สร้าง object จาก `_type` ผ่าน dictionary `TASK_TYPES`, จัดการ `JSONDecodeError` และข้อมูลไม่ครบ
- **`task_manager.py` (Business Logic)** — เก็บ list งาน, ดูแล `next_id`, CRUD, `search_tasks`, `filter_tasks`, `sort_tasks`; คืนค่า `(success, message)` ให้ UI แสดงผล
- **`cli_interface.py` (UI Layer)** — แสดงเมนู, รับและตรวจสอบ input, เรียกเมธอดของ `TaskManager`; ใช้ dictionary map เมนู → handler แทน if/elif ยาว
- **`main.py` (Orchestrator)** — ตั้งค่า UTF-8, สร้าง `TaskManager` และ `CLIInterface`, เริ่ม loop

### 3.2 Data Model
| Class | Attributes |
|---|---|
| Task | `id: int`, `description: str`, `completed: bool`, `tags: list[str]` |
| DueDateTask | + `due_date: datetime.date` |
| PriorityTask | + `priority: str` ("High"/"Medium"/"Low") |

ตัวอย่าง JSON:
```json
{ "id": 2, "description": "ส่งงานโปรเจกต์", "completed": false,
  "tags": ["assignment", "university"], "due_date": "2026-10-20", "_type": "DueDateTask" }
```

### 3.3 Interface Design (CLI)
```
1-3 เพิ่มงาน | 4 แสดงทั้งหมด | 5 เสร็จสิ้น | 6 ลบ | 7 ค้นหา | 8 กรอง | 9 เรียงลำดับ | 0 ออก
```

### 3.4 Pseudocode ฟีเจอร์ใหม่
```
search(keyword):
    kw = lower(keyword)
    return งานที่ kw อยู่ใน lower(description) หรือ อยู่ใน tag ใด tag หนึ่ง

filter(status, before, after, priority, tags):
    result = งานทั้งหมด
    ถ้ามี status    -> เก็บเฉพาะ completed == status
    ถ้ามี before/after -> เก็บเฉพาะ DueDateTask ที่ due_date อยู่ในช่วง
    ถ้ามี priority  -> เก็บเฉพาะ PriorityTask ที่ priority ตรงกัน
    ถ้ามี tags      -> เก็บเฉพาะงานที่มี tags ครบทุกตัว
    return result

sort(criterion, reverse):
    แยกงานที่ "มีค่า" ของ criterion ออกจากงานที่ "ไม่มี"
    เรียงกลุ่มที่มีค่า (priority ใช้ map High=1, Medium=2, Low=3)
    return กลุ่มที่เรียงแล้ว + กลุ่มที่ไม่มีค่า (อยู่ท้ายเสมอ)
```

## 4. Implementation Plan
1. ✅ Refactor models ไปไว้ที่ `src/task.py` และเพิ่ม `tags`
2. ✅ แยก JSON I/O ไป `data_persistence.py`
3. ✅ แยก input/output ไป `cli_interface.py`, ให้ `main.py` เป็น orchestrator
4. ✅ Tags: รับ input, แสดงผล, บันทึก
5. ✅ Search
6. ✅ Filter
7. ✅ Sort
8. ⏳ Unit tests (สัปดาห์ถัดไป)

## 5. Challenges & Decisions
- **เรียงงานต่างประเภท:** งานที่ไม่มี due_date/priority ให้อยู่ท้ายรายการเสมอ แม้กด reverse — ผู้ใช้ไม่ต้องเห็นงานที่ไม่เกี่ยวข้องขึ้นมาก่อน
- **ช่วงวันที่:** ใช้ before/after แบบรวมวันนั้น (inclusive) ซึ่งครอบคลุม "ก่อน", "หลัง" และ "ระหว่าง" ได้ด้วย 2 ช่อง
- **CLI ซับซ้อนขึ้น:** ช่องกรองทุกช่องเว้นว่างได้ = ไม่ใช้เงื่อนไขนั้น
- **ภาษาไทยใน Windows terminal:** ตั้ง `stdout` เป็น UTF-8 และบันทึก JSON ด้วย `ensure_ascii=False`

## 6. Future Enhancements
- Reminders: แจ้งงานที่ใกล้ครบกำหนด/เลยกำหนดตอนเปิดโปรแกรม (มี `is_overdue()` รองรับแล้ว)
- Unit tests ด้วย `unittest`/`pytest`
- เปลี่ยน persistence เป็น SQLite
- GUI ด้วย Tkinter / PyQt
- Export/Import CSV
- Undo/Redo stack
- User accounts
