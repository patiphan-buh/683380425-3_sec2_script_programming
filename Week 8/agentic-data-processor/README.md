# Agentic Data Processor (Week 8 – Extension)

ต่อยอดจาก `data-processor` โดยให้ "agent" ทำงานตาม **config JSON** แทนการ hard-code

## แนวคิด: Plan → Act → Observe → Report
1. **Plan** – สร้างรายการ step (load_csv → validate_csv → process_csv → write_csv → load_json → validate_json → update_json → write_json)
2. **Act** – รันแต่ละ step ผ่าน `CSVHandler` / `JSONHandler`
3. **Observe** – บันทึกผล OK/FAIL ของแต่ละ step; ถ้า FAIL จะหยุด pipeline
4. **Report** – เขียน audit report ลง `reports/audit_report_YYYYMMDD_HHMMSS.txt`

## ปรับพฤติกรรมได้ที่ `configs/data_pipeline_config.json`
* path ของไฟล์ input/output
* `min_sale_amount` สำหรับกรองยอดขาย
* required columns / keys สำหรับ validation
* รายการ `stock_updates` และ `new_products`
  (ตัวอย่างมี `PROD999` ที่ไม่มีอยู่จริง เพื่อแสดงว่า audit report จับ warning ได้)

## Run
```bash
cd week8/agentic-data-processor
python main.py
```

## Structure
```
agentic-data-processor/
├── configs/data_pipeline_config.json
├── data/ (input_sales.csv, input_inventory.json)
├── reports/audit_report_<timestamp>.txt
├── src/ (agent.py, csv_handler.py, json_handler.py, utils.py)
├── main.py
├── AllCode.md
├── .gitignore
└── README.md
```
