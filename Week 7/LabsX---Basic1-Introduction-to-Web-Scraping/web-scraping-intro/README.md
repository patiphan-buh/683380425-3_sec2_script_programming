# Week 7 (LabX Basic): Introduction to Web Scraping

โปรเจกต์นี้แนะนำพื้นฐานการทำ Web Scraping ด้วย Python โดยใช้ `requests` และ `BeautifulSoup4`
ดาวน์โหลด HTML จากเว็บไซต์ แล้วดึงข้อมูลที่ต้องการตามโครงสร้างของ HTML

**Target:** https://automatetheboringstuff.com/3e/ (Automate the Boring Stuff with Python, 3rd Edition)

> **Ethics & Legality:** ตรวจสอบ `robots.txt` และ Terms of Service ของเว็บไซต์ก่อน scrape เสมอ
> หลีกเลี่ยงการยิง request ถี่เกินไป โปรเจกต์นี้ใช้เพื่อการศึกษาเท่านั้น

## Implemented Features

* **HTML Download**: ใช้ `requests` ดึงเนื้อหาหน้าเว็บ (ใส่ User-Agent, timeout)
* **HTML Parsing**: ใช้ `BeautifulSoup4` วิเคราะห์ HTML
* **Data Extraction**: ดึงชื่อหนังสือ (`<article><header><h1>`) และชื่อบททั้งหมดจาก Table of Contents
* **Error Handling**: จัดการ HTTPError, ConnectionError, Timeout และ RequestException

## How to Run

1. สร้าง virtual environment และติดตั้ง dependencies
   ```bash
   python -m venv venv
   venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
2. รัน scraper
   ```bash
   python main.py
   ```
   ผลลัพธ์จะแสดงชื่อหนังสือและรายชื่อบท (27 รายการ) ใน terminal
   เปรียบเทียบกับไฟล์ `ผลลัพธ์ ที่ควรได้.png`

## Project Structure

```
web-scraping-intro/
├── src/
│   ├── __init__.py     # ทำให้ 'src' เป็น Python package
│   └── scraper.py      # Logic การ scrape
├── main.py             # Entry point
├── requirements.txt
├── ผลลัพธ์ ที่ควรได้.png
├── .gitignore
└── README.md
```

## Debugging Web Scraping

* **Inspect HTML:** กด F12 เพื่อดู tag / class / id ที่ต้องใช้
* **เช็ก status code:** 200 = สำเร็จ, 403 = ถูกบล็อก, 404 = ไม่พบหน้า
* **เช็ก `None`:** ก่อนเรียก `.get_text()` ควรตรวจว่า `find()` คืนค่า `None` หรือไม่
* **User-Agent:** บางเว็บบล็อก request ที่ไม่มี User-Agent
* **Rate limiting:** ถ้าต้อง scrape หลายหน้า ให้หน่วงเวลาด้วย `time.sleep()`
* **ภาษาไทยเพี้ยนใน PowerShell:** รัน `chcp 65001` หรือตั้ง `$env:PYTHONUTF8=1` ก่อน

## Extension Ideas

* บันทึกข้อมูลเป็น CSV / JSON (`data/scraped_output.json`)
* Scrape หลายหน้า (pagination)
* ดึงข้อมูลเพิ่ม เช่น ลิงก์ของแต่ละบท
* ใช้ Selenium สำหรับเว็บที่โหลดด้วย JavaScript (ดู Advanced Lab)

**Source:** https://automatetheboringstuff.com/3e/
