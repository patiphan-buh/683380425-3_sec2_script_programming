# Week 7 (LabX Advanced): Advanced Web Scraping & Introduction to Automated Agents

โปรเจกต์นี้สร้าง "agentic" web scraper ด้วย `Selenium` ที่ทำงานตามไฟล์ config (JSON)
รองรับ pagination, retry, explicit waits และบันทึกผลเป็น JSON

**Target (ใช้เพื่อการศึกษา):** https://books.toscrape.com/ — เว็บจำลองสำหรับฝึก scrape โดยเฉพาะ

## Key Concepts

* **Selenium for dynamic content** — ควบคุม browser จริง (headless หรือเห็นหน้าต่าง)
* **WebDriver management** — `webdriver-manager` ดาวน์โหลด driver อัตโนมัติ (fallback เป็น Selenium Manager)
* **Config-driven agent** — พฤติกรรมของ scraper กำหนดใน `configs/example_site_config.json` ไม่ต้องแก้โค้ด
* **Modular design** — `scraper_agent`, `config_parser`, `data_models`, `utils`, `driver_manager`
* **Robustness** — explicit waits, retry การคลิก, จัดการ error, หน่วงเวลาระหว่างหน้า
* **Structured data** — เก็บข้อมูลด้วย dataclass `Product` แล้วบันทึกเป็น JSON

## Ethical and Legal Considerations

* ตรวจ `robots.txt` และ Terms of Service ก่อน scrape ทุกครั้ง
* ใช้ delay (`delay_between_pages`) และอย่าส่ง request ถี่เกินไป
* อย่านำข้อมูลที่ scrape มาเผยแพร่ซ้ำโดยไม่ได้รับอนุญาต
* โปรเจกต์นี้ใช้เพื่อการศึกษาเท่านั้น

## Setup & How to Run

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

ต้องติดตั้ง **Google Chrome** (หรือ Firefox) ในเครื่อง

1. ตรวจสอบ environment
   ```bash
   python test_setup.py
   ```
2. รัน scraper
   ```bash
   python main.py                    # headless (ค่าเริ่มต้น)
   python main.py --show-browser     # เปิดหน้าต่าง browser เพื่อ debug
   python main.py --config configs/example_site_config.json
   ```
3. ดูผลลัพธ์ใน terminal และไฟล์ `data/scraped_products.json`
   (ค่าเริ่มต้น `max_pages = 3` → 3 หน้า × 20 เล่ม = **60 รายการ**)
   แล้วแคปหน้าจอบันทึกเป็น `LabAD1 ผลลัพธ์ที่ควรได้.png`

## Config Reference (`configs/example_site_config.json`)

| Key | ความหมาย |
|---|---|
| `start_url` | URL เริ่มต้น |
| `max_pages` | จำนวนหน้าสูงสุดที่จะ scrape |
| `delay_between_pages` | หน่วงเวลา (วินาที) ระหว่างหน้า |
| `item_container_selector` | selector ของกล่องสินค้า 1 ชิ้น |
| `pagination_selector` | selector ของปุ่ม/ลิงก์ "next page" (`null` = scrape หน้าเดียว) |
| `item_data_selectors` | selector ของแต่ละ field (relative กับ container), `null` = ไม่มี field นี้ |

Selector ที่ขึ้นต้นด้วย `/` หรือ `(` จะถูกตีความเป็น XPath นอกนั้นเป็น CSS selector

## Project Structure

```
AD1-LabX-ADV_-Advanced-Web-Scraping.../
├── configs/
│   └── example_site_config.json
├── data/
│   └── scraped_products.json      # สร้างหลังรัน
├── src/
│   ├── __init__.py
│   ├── config_parser.py           # โหลด + ตรวจ config
│   ├── data_models.py             # dataclass Product
│   ├── driver_manager.py          # ตั้งค่า Selenium WebDriver
│   ├── scraper_agent.py           # logic หลักของ agent
│   └── utils.py                   # waits, robust_click, save JSON
├── .gitignore
├── LabAD1 ผลลัพธ์ที่ควรได้.png    # แคปหน้าจอหลังรัน
├── README.md
├── main.py
├── requirements.txt
└── test_setup.py
```

## Debugging

* **`SessionNotCreatedException` / driver error** — เวอร์ชัน Chrome กับ driver ไม่ตรงกัน: อัปเดต Chrome แล้ว `pip install -U selenium webdriver-manager`
* **`NoSuchElementException`** — selector ผิดหรือ element ยังโหลดไม่เสร็จ: ตรวจด้วย DevTools (F12) และใช้ explicit wait
* **`TimeoutException`** — เพิ่ม timeout หรือเช็กว่าหน้าเว็บโหลดช้าจริงหรือไม่
* **`StaleElementReferenceException`** — element หลุดจาก DOM หลังหน้าเปลี่ยน: ให้ find ใหม่
* **Pagination วนไม่จบ** — ตรวจว่าหน้าสุดท้ายยังมี selector ของ next อยู่หรือไม่ (ที่นี่ใช้ `max_pages` กันไว้)
* **ใช้ headless แล้วมีปัญหา** — ลอง `python main.py --show-browser`

## Extension Ideas

* Proxy / User-Agent rotation, บันทึกลง SQLite/CSV, retry แบบ exponential backoff
* Concurrent scraping (ระวัง rate limit), ตั้งเวลารันด้วย Task Scheduler / cron
* ให้ LLM ช่วยสร้าง selector หรือเลือกลิงก์ที่จะคลิกต่อ
