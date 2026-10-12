# Week 12 LabX BASIC: Automating Communications (Email & SMS)

This project demonstrates how to automate sending and receiving emails, and sending SMS messages, using Python. It uses `smtplib` for sending, `imaplib` for receiving, and email-to-SMS gateways for text messages. Credentials are loaded securely from a `.env` file.

Every email sent by the script carries the student's **name and student ID** (from `STUDENT_NAME` / `STUDENT_ID` in `.env`) in both the subject and the body.

## Key Concepts Demonstrated
* **Email Sending (SMTP)** — TLS via `starttls()`, App Password login, multipart emails with `email.mime` (plain text / HTML + PDF attachment, UTF-8 for Thai text).
* **Email Receiving (IMAP)** — `IMAP4_SSL`, `UID SEARCH` by `UNSEEN` + `FROM` + `SUBJECT`, fetch with `BODY.PEEK[]`, parse multipart messages, download attachments, mark as read with `STORE +FLAGS (\Seen)`.
* **SMS via Email Gateway** — carrier-specific addresses such as `1234567890@txt.att.net`.
* **Secure Credential Handling** — `.env` + `python-dotenv`; `.env` is git-ignored and `.env.example` is provided.
* **Error Handling & Logging** — `try/except` around every network operation with informative log output.
* **Unit Tests** — offline tests with `unittest.mock` in `tests/`.

## Project Structure
```
email-sms-automator/
├── data/
│   ├── attachments/        # Received attachments are saved here (.gitkeep keeps the folder)
│   └── dummy_report.pdf    # Sample attachment
├── src/
│   ├── __init__.py
│   ├── email_receiver.py   # IMAP: search, fetch, parse, download, mark as read
│   ├── email_sender.py     # SMTP: build & send emails (+ attachments)
│   ├── sms_gateway.py      # Email-to-SMS gateway helper
│   └── utils.py            # Logging, env loading, directory helpers
├── tests/
│   └── test_automator.py   # Offline unit tests (pytest)
├── .env.example            # Template for your .env (copy & fill in)
├── .gitignore
├── main.py                 # Runs Task 1–4
├── requirements.txt
└── README.md
```

## Setup & How to Run
1. **Clone and install**
   ```bash
   git clone https://github.com/YOUR_USERNAME/email-sms-automator.git
   cd email-sms-automator
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Create an App Password (Gmail)** — turn on 2-Step Verification, then go to
   Google Account → Security → *App passwords* (or https://myaccount.google.com/apppasswords) and create one. Your normal Gmail password will **not** work.
3. **Create `.env`**
   ```bash
   cp .env.example .env            # Windows: copy .env.example .env
   ```
   Fill in `SENDER_EMAIL`, `SENDER_APP_PASSWORD`, `TEST_RECIPIENT_EMAIL`, `STUDENT_NAME`, `STUDENT_ID`.
   **Never commit `.env`.**
4. **Run**
   ```bash
   python main.py
   ```
5. **Run tests (optional)**
   ```bash
   pytest -v
   ```

## What the script does
| Task | Action |
|------|--------|
| 1 | Sends a plain-text email to `TEST_RECIPIENT_EMAIL` |
| 2 | Sends an email with `data/dummy_report.pdf` attached |
| 3 | Sends an SMS through a carrier email-to-SMS gateway (US carriers; Thai carriers have no public gateway, so this usually bounces — expected) |
| 4 | Emails itself with an attachment, then searches the inbox (IMAP) for it, prints sender/subject/snippet, downloads the attachment to `data/attachments/`, and marks it as read |

## Fixes vs. the lab handout code
* `main.py` imported modules via `sys.path` while `src/` uses relative imports → `ImportError`. Now imports `from src...`.
* Receiver now uses real IMAP **UIDs** (`mail.uid(...)`) — the handout used sequence numbers and called them UIDs.
* Search values are quoted so subjects with spaces work; the search subject is ASCII (IMAP SEARCH is ASCII-only).
* Emails are encoded as UTF-8 so Thai names display correctly.
* Attachment filenames are sanitized (`os.path.basename`) to prevent path traversal.
* `.gitignore` inline comments were invalid (`.env # ...` would not match `.env`).

## Debugging
* **`ValueError: Environment variable ... not set`** — `.env` missing / not in the project root / typo.
* **`SMTPAuthenticationError` / IMAP login failed** — use an App Password, not your Gmail password.
* **Connection errors** — check `smtp.gmail.com:587`, `imap.gmail.com`, firewall, internet.
* **SMS not arriving** — carrier gateways are unreliable and US-only; a bounce email in your inbox is normal.

## Extension Ideas
Scheduled notifications (`schedule` / `APScheduler`), Jinja2 templates, command-by-email, Twilio/Vonage for production SMS, error alerts by email.
