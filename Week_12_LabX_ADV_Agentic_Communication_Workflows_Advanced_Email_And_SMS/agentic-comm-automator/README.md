# Week 22 LabX ADV: Agentic Communication Workflows (Advanced Email & SMS)

A configuration-driven **CommunicationAgent** that runs email and SMS workflows defined in a JSON file:
dynamic templating from a shared context, To/CC/BCC, conditional attachments, HTML email, rule-based
inbox processing (download + rename attachments, mark as read, SMS alert, auto-reply), error
notification and a JSON audit report.

It runs in two modes:

| Mode | Command | Needs |
|---|---|---|
| **Dry-run (offline demo)** | `python main.py --dry-run` | nothing – emails are written as `.eml` files to `data/dry_run/` and a local mock inbox is used |
| **Real** | `python main.py` | `.env` with a Gmail address + App Password |

## Quick start

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python main.py --dry-run          # 1) demo without credentials
python -m unittest discover -s tests -v   # 2) 14 automated tests

cp .env.example .env              # 3) real run: fill in your Gmail + App Password
python main.py
```

The sample attachments `data/reports/sales_report.pdf` and `data/reports/summary_data.xlsx` are
created automatically if missing (or run `python -m src.sample_data`).

### Gmail App Password
Google Account → Security → 2-Step Verification (turn on) → **App passwords** → create one → paste the
16 characters into `SENDER_APP_PASSWORD`. Your normal Gmail password will not work. IMAP is enabled by
default on Gmail; if not, turn it on in Gmail Settings → Forwarding and POP/IMAP.

### About SMS
SMS is sent through email-to-SMS gateways (e.g. `1234567890@txt.att.net`), which only exist for some
US carriers. In other countries (e.g. Thailand), set `TEST_SMS_PHONE_NUMBER` to an **email address you
can read** and leave `TEST_SMS_CARRIER` empty – the agent then sends the short "SMS" text there.

## The workflow (`configs/comm_pipeline_config.json`)

| # | Task | Type | Shows |
|---|---|---|---|
| 1 | Send Daily Sales Report Email | `send_email` | subject/body templates, To + CC, 2 attachments from context paths (`{attachment_path_1}`), required vs optional attachment |
| 2 | Send HTML Summary Email | `send_email` | HTML body with a table, **BCC**, uses output of task 1 (`{daily_report_email[attachments]}`), attachment only if a context key exists |
| 3 | Send Sales Alert SMS | `send_sms` | dynamic SMS text, carrier gateway |
| 4 | Simulate Incoming Request Email | `send_email` | sends a "Data Request … Urgent" email with attachments to yourself |
| 5 | Process Incoming Data Requests | `process_inbox` | polls the inbox (up to 60 s) and applies 3 rules |

Rules in task 5:

1. **IF** sender contains `SENDER_EMAIL` AND subject contains "Request" AND has attachments
   **THEN** download only `.pdf` files to `data/incoming_attachments/`, rename them
   `{report_date}_uid{uid}_{filename}`, and mark the email as read.
2. **IF** body contains "urgent" **THEN** send an SMS alert.
3. **IF** body contains "new data processing" **THEN** send an automatic reply (threaded with `In-Reply-To`).

The search uses `status: "ALL"` plus the subject tag `run {run_id}` so each run finds exactly the email it just
sent (Gmail sometimes marks messages you send to yourself as already read, which would make `UNSEEN`
miss them).

### Configuration reference

* Placeholders: `${ENV_VAR}` → value from `.env` (UPPER_CASE names); `{key}` → agent context, with Python
  format specs (`{sales_figure:,.2f}`) and indexing (`{daily_report_email[subject]}`).
  `${sales_figure:,.2f}` is a literal `$` followed by the formatted number.
* `send_email`: `recipients` {`to`,`cc`,`bcc`}, `subject_template`, `body_template`, `is_html`,
  `attachments` – a string (attach if it exists) or `{"path", "required", "only_if_context"}`.
* `send_sms`: `phone_numbers`, `message_template`, `carrier_name` (messages > 160 chars are truncated).
* `process_inbox`: `mailbox`, `search_criteria` {`status` UNSEEN/SEEN/ALL, `from_sender`, `subject_contains`
  (string or list = all must match)}, `wait_for_email_seconds`, `poll_interval_seconds`, `max_emails`, `rules`.
  * conditions (`if`, all must be true, case-insensitive, a list = any of): `from_sender_contains`,
    `subject_contains`, `body_contains`, `has_attachments`, `attachment_extension`
  * actions (`then`): `download_attachments_to`, `attachment_extensions`, `rename_template`, `mark_as_read`,
    `send_sms_alert` (+ `alert_phone_numbers`, `alert_carrier`, `alert_message_template`),
    `reply_with_template` (+ `reply_subject_template`)
  * email fields usable in rule templates: `uid, sender, sender_address, subject, date, text_body,
    has_attachments, attachment_count, attachments_meta, downloaded_files`
* `output_context_key`: stores the task's result in the context for later tasks.
* Top level: `stop_on_error` (default false), `error_notification` {`to`, `subject_template`} – emails a
  summary when any task fails, `initial_context` – extra starting values.

## Output

* Console + `logs/agent.log`
* `reports/audit_report_comm_<run_id>.json` – run summary, per-task status, every agent decision
  (secrets are masked)
* `data/incoming_attachments/` – downloaded attachments
* Dry-run only: `data/dry_run/outbox/<run_id>/*.eml` (open with any mail app) and `data/dry_run/mailbox/`

Exit code: `0` all tasks succeeded, `2` some task failed, `1` configuration/startup error.

## Project structure

```
agentic-comm-automator/
├── src/
│   ├── __init__.py
│   ├── communication_agent.py   # agent: dispatcher, context, rule engine, audit, error alert
│   ├── email_tasks.py           # SMTP/IMAP (EmailTasks) + offline MockEmailTasks
│   ├── sms_tasks.py             # email-to-SMS gateways
│   ├── config_parser.py         # loads + validates the JSON config
│   ├── template_renderer.py     # ${ENV} and {context} templates
│   ├── sample_data.py           # creates the sample PDF / XLSX
│   └── utils.py                 # logging, .env, audit helpers
├── configs/comm_pipeline_config.json
├── data/
│   ├── attachments/
│   ├── reports/ (sales_report.pdf, summary_data.xlsx)
│   └── incoming_attachments/
├── tests/test_agent.py
├── docs/sample_run/             # console output + audit report of a dry-run
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py
└── README.md
```

## Bugs fixed from the lab prototype

| # | Problem in the original code | Fix |
|---|---|---|
| 1 | `main.py` added `src/` to `sys.path` and imported `config_parser` directly, but the modules use relative imports (`from .utils`) → `ImportError` | import as a package: `from src.config_parser import …` |
| 2 | Validator required `parameters.to`, but the config uses `parameters.recipients.to` → every run stopped with "requires 'to'" | validator accepts `recipients` {to/cc/bcc} (and legacy `to`) |
| 3 | `"${TEST_RECIPIENT_EMAIL}"`, `"${SENDER_EMAIL}"` were never replaced → `KeyError` in the renderer | renderer substitutes `${ENV_VAR}` from `.env` |
| 4 | `carrier_name` / `alert_carrier` were not rendered → SMS gateway never resolved | rendered like other fields |
| 5 | `{attachments_meta.0.filepath}` is invalid `str.format` syntax (`.0` is attribute access) | use `{downloaded_files}` / `{attachments_meta[0][filepath]}` |
| 6 | IMAP sequence numbers reused across separate logins; `SUBJECT Data Request` sent unquoted (two words) | UID SEARCH/FETCH/STORE and quoted search terms |
| 7 | `RFC822` fetch marks every email read and always downloads all attachments – rules could not decide | `BODY.PEEK[]`; downloading/marking are rule actions |
| 8 | Auto-reply sent to `"Name <addr>"` string | reply to the parsed address, threaded with `In-Reply-To` |
| 9 | Self-sent email may already be marked read / not yet arrived → `UNSEEN` search found nothing | unique run tag in subject + polling with timeout |
| 10 | Duplicate console lines (module handler + root handler) | single root handler, plus log file |
| 11 | "Audit report generated" entry was added after the file was written | logged before writing; report has a summary section |
| 12 | Body template used `${sales_figure:.2f}` with no thousands separator; SMS could exceed 160 chars | `:,.2f`; SMS truncated with a warning |

## Extension ideas
Jinja2 templates, chaining with the Week 20 DataAgent through a shared context file, folder watcher /
webhook triggers, storing processed-email metadata in SQLite, NLP-based rule conditions, a small Streamlit UI.

---

## สรุปงาน (ภาษาไทย)

**สิ่งที่ทำ:** สร้าง CommunicationAgent ที่อ่าน workflow จากไฟล์ JSON แล้วทำงาน 5 ขั้นตอน — ส่งอีเมลรายงานยอดขาย
(To/CC + ไฟล์แนบ 2 ไฟล์), ส่งอีเมล HTML (BCC + ใช้ผลลัพธ์จากงานก่อนหน้า), ส่ง SMS, จำลองอีเมลขอข้อมูลส่งหาตัวเอง
และประมวลผลกล่องจดหมายด้วยกฎ IF-THEN 3 ข้อ (ดาวน์โหลดเฉพาะ PDF + เปลี่ยนชื่อไฟล์ + ทำเครื่องหมายอ่านแล้ว,
ส่ง SMS แจ้งเตือนเมื่อเนื้อหามีคำว่า urgent, ตอบกลับอัตโนมัติ) พร้อมบันทึก audit report เป็น JSON
และส่งอีเมลแจ้งเตือนเมื่อมีงานล้มเหลว

**วิธีทดสอบ:** `python main.py --dry-run` (ไม่ต้องใช้รหัสอีเมล) และ `python -m unittest discover -s tests -v`
(ผ่านทั้ง 14 เทสต์) — ถ้าจะรันจริง คัดลอก `.env.example` เป็น `.env` แล้วใส่ Gmail + App Password

**แก้บั๊กจากโค้ดต้นแบบ 12 จุด** (ตารางด้านบน) เช่น import ผิดแบบ, ตัวตรวจ config ไม่ตรงกับไฟล์ config,
`${ENV_VAR}` ไม่ถูกแทนค่า, การค้น IMAP ด้วยหัวเรื่องที่มีช่องว่าง และการ mark อ่านแล้วก่อนที่กฎจะทำงาน

**หมายเหตุ SMS:** ผู้ให้บริการมือถือในไทยไม่มี email-to-SMS gateway ให้ใส่อีเมลของตัวเองใน
`TEST_SMS_PHONE_NUMBER` และเว้น `TEST_SMS_CARRIER` ว่าง ข้อความ "SMS" จะมาเป็นอีเมลสั้นแทน
