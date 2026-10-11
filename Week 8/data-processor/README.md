# Week 8: Automating with CSV and JSON Data

โปรเจกต์นี้ใช้ Python built-in `csv` และ `json` อ่าน / เขียน / ประมวลผลข้อมูลแบบ structured plaintext

## Key Concepts
* **CSV Reading (`DictReader`)** – อ่านแถวเป็น dictionary โดยใช้แถวแรกเป็น header
* **CSV Writing (`DictWriter`)** – เขียน list of dict กลับเป็น CSV
* **CSV Processing** – รวมยอดขาย, หาค่าเฉลี่ย, กรองรายการที่ `Amount >= 100`
* **JSON Reading/Writing (`json.load` / `json.dump`)** – พร้อม pretty-print
* **JSON Manipulation** – แก้ nested data, อัปเดต stock, เพิ่มสินค้าใหม่
* **Modular Design** – แยก `csv_handler.py`, `json_handler.py`, `utils.py`

## Setup & Run
```bash
cd week8/data-processor
python -m venv venv
venv\Scripts\activate.bat      # macOS/Linux: source venv/bin/activate
python main.py
```

## Output Evidence (Screenshots)

### `data/output_filtered_sales.csv`
กรองเฉพาะ Amount >= 100 (3 แถว) + แถว SUMMARY (Total = 1902.00, Avg Price = 237.75, Count = 3)

![output_filtered_sales](screenshots/output_filtered_sales.png)

### `data/output_updated_inventory.json`
PROD001 stock 50 → 60, PROD003 stock 80 → 75, เพิ่ม PROD004 (Gaming Headset)

![output_updated_inventory](screenshots/output_updated_inventory.png)

## Project Structure
```
data-processor/
├── src/
│   ├── __init__.py
│   ├── csv_handler.py
│   ├── json_handler.py
│   └── utils.py
├── data/
│   ├── input_sales.csv
│   ├── input_inventory.json
│   ├── output_filtered_sales.csv          (generated, gitignored)
│   └── output_updated_inventory.json      (generated, gitignored)
├── screenshots/
│   ├── output_filtered_sales.png
│   └── output_updated_inventory.png
├── main.py
├── AllCode.md
├── .gitignore
└── README.md
```

## Debugging Tips
* `FileNotFoundError` – ตรวจว่าไฟล์ input อยู่ในโฟลเดอร์ `data/`
* `KeyError` – ชื่อ header ใน CSV ต้องตรงกับ key ที่โค้ดเรียก (`Amount`, `Price`)
* `json.JSONDecodeError` – JSON syntax ผิด (ลืม comma / วงเล็บ)
* `ValueError` – ค่าตัวเลขมีสัญลักษณ์ เช่น `$` หรือ `,`
* Encoding – ใช้ `encoding='utf-8'` ทั้งตอนอ่านและเขียน
