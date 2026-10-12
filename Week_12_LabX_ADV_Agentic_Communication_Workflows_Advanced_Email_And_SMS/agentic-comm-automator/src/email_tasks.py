# agentic-comm-automator/src/email_tasks.py
"""
Email sending (SMTP) and receiving (IMAP).

EmailTasks      – talks to a real mail server (e.g. Gmail with an App Password).
MockEmailTasks  – same interface, but writes .eml files to disk instead of using the network.
                  Used by `python main.py --dry-run` and by the unit tests, so the whole
                  workflow can be demonstrated without real credentials.
"""
import email
import imaplib
import json
import os
import re
import smtplib
from email.header import decode_header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid, parseaddr

from .utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)


def _uid_str(uid):
    return uid.decode("utf-8") if isinstance(uid, bytes) else str(uid)


def _as_list(value):
    if not value:
        return []
    return [v for v in value if v] if isinstance(value, list) else [value]


def _imap_quote(value):
    """Quotes a value for an IMAP SEARCH (needed for strings containing spaces)."""
    value = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def _safe_filename(name):
    name = os.path.basename(name or "").strip()
    name = re.sub(r'[\\/:*?"<>|\r\n]+', "_", name)
    return name or "attachment.bin"


def _html_to_text(html):
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text).strip()


class EmailTasks:
    """Handles sending and receiving emails via SMTP and IMAP protocols."""

    def __init__(self, smtp_server, smtp_port, imap_server, sender_email, sender_password,
                 imap_port=993, timeout=30):
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port)
        self.imap_server = imap_server
        self.imap_port = int(imap_port)
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.timeout = timeout
        self._smtp = None
        self._imap = None
        self._raw_cache = {}  # (mailbox, uid) -> raw RFC822 bytes
        logger.info(f"{self.__class__.__name__} initialized for {sender_email}.")

    # ------------------------------------------------------------------ SMTP
    def _connect_smtp(self):
        if self._smtp:
            return True
        try:
            if self.smtp_port == 465:
                self._smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=self.timeout)
            else:
                self._smtp = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout)
                self._smtp.starttls()
            self._smtp.login(self.sender_email, self.sender_password)
            logger.info("Successfully connected and logged into SMTP server.")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed. Check email and app password. Error: {e}")
        except (smtplib.SMTPConnectError, OSError) as e:
            logger.error(f"SMTP connection failed. Check server address/port and network. Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during SMTP connect/login: {e}")
        self._smtp = None
        return False

    def _disconnect_smtp(self):
        if self._smtp:
            try:
                self._smtp.quit()
                logger.info("Disconnected from SMTP server.")
            except Exception as e:
                logger.warning(f"Error during SMTP disconnection: {e}")
            finally:
                self._smtp = None

    def build_message(self, recipients, subject, body, attachments=None, is_html=False, in_reply_to=None):
        """Builds a MIME message. Returns (message, all_recipient_addresses, attached_paths)."""
        to_list = [r for r in recipients.get("to", []) if r]
        cc_list = [r for r in recipients.get("cc", []) if r]
        bcc_list = [r for r in recipients.get("bcc", []) if r]  # never written to a header

        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        if to_list:
            msg["To"] = ", ".join(to_list)
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        msg.attach(MIMEText(body, "html" if is_html else "plain", "utf-8"))

        attached = []
        for path in attachments or []:
            if not os.path.isfile(path):
                logger.warning(f"Attachment file not found: {path}. Skipping.")
                continue
            try:
                with open(path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(path)}"'
                msg.attach(part)
                attached.append(path)
                logger.info(f"Attached file: {path}")
            except OSError as e:
                logger.error(f"Error attaching file {path}: {e}")

        # de-duplicate while keeping order
        all_recipients = list(dict.fromkeys(to_list + cc_list + bcc_list))
        return msg, all_recipients, attached

    def send_email(self, recipients, subject, body, attachments=None, is_html=False, in_reply_to=None):
        """
        Sends an email.
        :param recipients: dict with lists for 'to', 'cc', 'bcc'.
        :return: dict {"success", "attached", "recipients", "message_id"}.
        """
        msg, all_recipients, attached = self.build_message(
            recipients, subject, body, attachments, is_html, in_reply_to)
        result = {"success": False, "attached": attached, "recipients": all_recipients,
                  "message_id": msg["Message-ID"]}
        if not all_recipients:
            logger.error("No recipients specified for email.")
            return result
        result["success"] = self._deliver(msg, all_recipients)
        if result["success"]:
            logger.info(f"Email sent to {len(all_recipients)} recipient(s). Subject: '{subject}'.")
        return result

    def _deliver(self, msg, all_recipients):
        if not self._connect_smtp():
            return False
        try:
            self._smtp.send_message(msg, from_addr=self.sender_email, to_addrs=all_recipients)
            return True
        except Exception as e:
            logger.error(f"Failed to send email. Error: {e}")
            return False
        finally:
            self._disconnect_smtp()

    # ------------------------------------------------------------------ IMAP
    def _connect_imap(self, mailbox="INBOX"):
        try:
            if not self._imap:
                self._imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=self.timeout)
                self._imap.login(self.sender_email, self.sender_password)
                logger.info("Successfully connected and logged into IMAP server.")
            status, _ = self._imap.select(mailbox)
            if status != "OK":
                logger.error(f"Could not select mailbox '{mailbox}'.")
                self._disconnect_imap()
                return False
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication/command failed. Check email and app password. Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during IMAP connect/login: {e}")
        self._imap = None
        return False

    def _disconnect_imap(self):
        if self._imap:
            try:
                self._imap.logout()
                logger.info("Disconnected from IMAP server.")
            except Exception as e:
                logger.warning(f"Error during IMAP disconnection: {e}")
            finally:
                self._imap = None

    def search_emails(self, mailbox="INBOX", criteria="UNSEEN", from_sender=None, subject_contains=None):
        """Searches a mailbox. Returns a list of message UIDs (bytes). UIDs stay valid across sessions."""
        if not self._connect_imap(mailbox):
            return []
        try:
            query = [criteria or "ALL"]
            if from_sender:
                query += ["FROM", _imap_quote(from_sender)]
            for term in _as_list(subject_contains):  # several terms = all must match (AND)
                query += ["SUBJECT", _imap_quote(term)]
            status, data = self._imap.uid("SEARCH", None, *query)
            if status != "OK":
                logger.error(f"IMAP search failed. Status: {status}")
                return []
            uids = data[0].split() if data and data[0] else []
            logger.info(f"Found {len(uids)} emails matching {query} in '{mailbox}'.")
            return uids
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
        finally:
            self._disconnect_imap()

    def _fetch_raw(self, uid, mailbox):
        if not self._connect_imap(mailbox):
            return None
        try:
            # BODY.PEEK[] does not set \Seen – marking as read is decided by the rules.
            status, data = self._imap.uid("FETCH", _uid_str(uid), "(BODY.PEEK[])")
            if status != "OK":
                logger.error(f"Failed to fetch email UID {_uid_str(uid)}. Status: {status}")
                return None
            for item in data:
                if isinstance(item, tuple) and len(item) > 1:
                    return item[1]
            logger.error(f"Email UID {_uid_str(uid)} returned no body.")
            return None
        finally:
            self._disconnect_imap()

    def _set_seen(self, uid, mailbox):
        if not self._connect_imap(mailbox):
            return False
        try:
            status, _ = self._imap.uid("STORE", _uid_str(uid), "+FLAGS", "(\\Seen)")
            return status == "OK"
        finally:
            self._disconnect_imap()

    def _get_raw(self, uid, mailbox):
        key = (mailbox, _uid_str(uid))
        if key not in self._raw_cache:
            raw = self._fetch_raw(uid, mailbox)
            if raw is None:
                return None
            self._raw_cache[key] = raw
        return self._raw_cache[key]

    def fetch_email_content(self, uid, mailbox="INBOX", mark_as_read=False, download_attachments_dir=None):
        """Fetches and parses one email. Returns a dict with sender, subject, bodies and attachment info."""
        try:
            raw = self._get_raw(uid, mailbox)
            if raw is None:
                return None
            info = self.parse_message(email.message_from_bytes(raw), uid)
            if download_attachments_dir:
                info["attachments_meta"] = self.save_attachments(uid, download_attachments_dir, mailbox=mailbox)
            if mark_as_read:
                self.mark_as_read(uid, mailbox)
            return info
        except Exception as e:
            logger.error(f"Error fetching/parsing email UID {_uid_str(uid)}: {e}")
            return None

    def mark_as_read(self, uid, mailbox="INBOX"):
        ok = self._set_seen(uid, mailbox)
        if ok:
            logger.info(f"Marked email UID {_uid_str(uid)} as read.")
        else:
            logger.error(f"Could not mark email UID {_uid_str(uid)} as read.")
        return ok

    def save_attachments(self, uid, target_dir, allowed_extensions=None, rename_func=None, mailbox="INBOX"):
        """
        Saves attachments of an already-fetched email.
        :param allowed_extensions: e.g. [".pdf"]; None = save everything.
        :param rename_func: callable(original_filename) -> new filename.
        :return: list of {filename, original_filename, filepath, content_type, size}.
        """
        raw = self._get_raw(uid, mailbox)
        if raw is None:
            return []
        msg = email.message_from_bytes(raw)
        allowed = [e.lower() if e.startswith(".") else "." + e.lower() for e in (allowed_extensions or [])]
        ensure_directory_exists(target_dir)
        saved = []
        for part in msg.walk():
            filename = part.get_filename()
            if not filename or part.get_content_maintype() == "multipart":
                continue
            original = self._decode_header_part(filename)
            ext = os.path.splitext(original)[1].lower()
            if allowed and ext not in allowed:
                logger.info(f"Skipping attachment '{original}' (extension {ext or 'none'} not allowed).")
                continue
            new_name = _safe_filename(rename_func(original) if rename_func else original)
            path = os.path.join(target_dir, new_name)
            base, extension = os.path.splitext(path)
            counter = 1
            while os.path.exists(path):  # never overwrite an earlier download
                path = f"{base}_{counter}{extension}"
                counter += 1
            payload = part.get_payload(decode=True) or b""
            try:
                with open(path, "wb") as f:
                    f.write(payload)
                saved.append({"filename": os.path.basename(path), "original_filename": original,
                              "filepath": path, "content_type": part.get_content_type(), "size": len(payload)})
                logger.info(f"Downloaded attachment: {path}")
            except OSError as e:
                logger.error(f"Error downloading attachment {original}: {e}")
        return saved

    def parse_message(self, msg, uid):
        sender = self._decode_header_part(msg.get("From"))
        text_body, html_body, attachments = "", "", []
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            disposition = str(part.get("Content-Disposition") or "")
            filename = part.get_filename()
            if filename or "attachment" in disposition:
                payload = part.get_payload(decode=True) or b""
                attachments.append({"filename": self._decode_header_part(filename) if filename else "unnamed",
                                    "filepath": None, "content_type": part.get_content_type(),
                                    "size": len(payload)})
                continue
            ctype = part.get_content_type()
            if ctype in ("text/plain", "text/html"):
                try:
                    content = (part.get_payload(decode=True) or b"").decode(
                        part.get_content_charset() or "utf-8", errors="replace")
                except LookupError:
                    content = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
                if ctype == "text/plain":
                    text_body += content
                else:
                    html_body += content
        if not text_body and html_body:
            text_body = _html_to_text(html_body)
        return {
            "uid": _uid_str(uid),
            "message_id": msg.get("Message-ID", ""),
            "sender": sender,
            "sender_address": parseaddr(sender)[1] or sender,
            "subject": self._decode_header_part(msg.get("Subject")),
            "date": msg.get("Date", ""),
            "text_body": text_body,
            "html_body": html_body,
            "has_attachments": bool(attachments),
            "attachment_count": len(attachments),
            "attachments_meta": attachments,
        }

    @staticmethod
    def _decode_header_part(header_value):
        """Decodes RFC 2047 encoded headers (e.g. '=?UTF-8?B?...?=')."""
        if header_value is None:
            return ""
        decoded = ""
        for part, charset in decode_header(str(header_value)):
            if isinstance(part, bytes):
                try:
                    decoded += part.decode(charset or "utf-8")
                except (LookupError, UnicodeDecodeError):
                    decoded += part.decode("latin-1", errors="replace")
            else:
                decoded += part
        return decoded.strip()


class MockEmailTasks(EmailTasks):
    """
    Offline stand-in for EmailTasks.
      * Every sent message is written to <outbox_dir>/*.eml (so you can open and inspect it).
      * Messages addressed to the sender's own address are also delivered to a local mock
        mailbox (<mailbox_dir>/INBOX), so the process_inbox task has something to find –
        exactly like sending to yourself on Gmail.
    """

    def __init__(self, sender_email, mailbox_dir, outbox_dir):
        super().__init__("mock-smtp", 0, "mock-imap", sender_email, "")
        self.mailbox_dir = mailbox_dir
        self.outbox_dir = outbox_dir
        self.sent_messages = []
        ensure_directory_exists(outbox_dir)
        ensure_directory_exists(os.path.join(mailbox_dir, "INBOX"))

    def _index_path(self, mailbox):
        return os.path.join(self.mailbox_dir, mailbox, "index.json")

    def _load_index(self, mailbox):
        path = self._index_path(mailbox)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_index(self, mailbox, index):
        ensure_directory_exists(os.path.join(self.mailbox_dir, mailbox))
        with open(self._index_path(mailbox), "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

    def _deliver(self, msg, all_recipients):
        n = len(os.listdir(self.outbox_dir)) + 1
        out_path = os.path.join(self.outbox_dir, f"{n:03d}.eml")
        with open(out_path, "wb") as f:
            f.write(msg.as_bytes())
        self.sent_messages.append({"to": all_recipients, "subject": msg["Subject"], "file": out_path})
        logger.info(f"[DRY-RUN] Email written to {out_path} (to: {', '.join(all_recipients)})")

        if self.sender_email.lower() in [r.lower() for r in all_recipients]:
            index = self._load_index("INBOX")
            uid = str(max([int(u) for u in index] or [0]) + 1)
            eml = os.path.join(self.mailbox_dir, "INBOX", f"{uid}.eml")
            with open(eml, "wb") as f:
                f.write(msg.as_bytes())
            index[uid] = {"file": os.path.basename(eml), "seen": False}
            self._save_index("INBOX", index)
            logger.info(f"[DRY-RUN] Delivered to mock INBOX as UID {uid}.")
        return True

    def search_emails(self, mailbox="INBOX", criteria="UNSEEN", from_sender=None, subject_contains=None):
        index = self._load_index(mailbox)
        criteria = (criteria or "ALL").upper()
        uids = []
        for uid, meta in sorted(index.items(), key=lambda kv: int(kv[0])):
            if criteria == "UNSEEN" and meta["seen"]:
                continue
            if criteria == "SEEN" and not meta["seen"]:
                continue
            with open(os.path.join(self.mailbox_dir, mailbox, meta["file"]), "rb") as f:
                msg = email.message_from_bytes(f.read())
            if from_sender and from_sender.lower() not in self._decode_header_part(msg["From"]).lower():
                continue
            subject = self._decode_header_part(msg["Subject"]).lower()
            if any(term.lower() not in subject for term in _as_list(subject_contains)):
                continue
            uids.append(uid.encode())
        logger.info(f"[DRY-RUN] Found {len(uids)} emails matching criteria in mock '{mailbox}'.")
        return uids

    def _fetch_raw(self, uid, mailbox):
        meta = self._load_index(mailbox).get(_uid_str(uid))
        if not meta:
            return None
        with open(os.path.join(self.mailbox_dir, mailbox, meta["file"]), "rb") as f:
            return f.read()

    def _set_seen(self, uid, mailbox):
        index = self._load_index(mailbox)
        if _uid_str(uid) not in index:
            return False
        index[_uid_str(uid)]["seen"] = True
        self._save_index(mailbox, index)
        return True
