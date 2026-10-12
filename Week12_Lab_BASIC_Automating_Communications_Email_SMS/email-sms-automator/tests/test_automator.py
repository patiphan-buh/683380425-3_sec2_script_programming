# email-sms-automator/tests/test_automator.py
# Offline unit tests (no real network). Run: pytest -v
import os
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.email_receiver import EmailReceiver  # noqa: E402
from src.email_sender import EmailSender  # noqa: E402
from src.sms_gateway import SMSGateway  # noqa: E402
from src.utils import ensure_directory_exists, get_env_variable  # noqa: E402


@pytest.fixture
def sender():
    return EmailSender("smtp.example.com", 587, "me@example.com", "pw")


# ---------- utils ----------
def test_get_env_variable_missing(monkeypatch):
    monkeypatch.delenv("NOT_SET_VAR", raising=False)
    with pytest.raises(ValueError):
        get_env_variable("NOT_SET_VAR")


def test_get_env_variable_default(monkeypatch):
    monkeypatch.delenv("NOT_SET_VAR", raising=False)
    assert get_env_variable("NOT_SET_VAR", "x") == "x"


def test_ensure_directory_exists(tmp_path):
    p = tmp_path / "a" / "b"
    ensure_directory_exists(str(p))
    assert p.is_dir()


# ---------- sender ----------
def test_build_message_with_attachment(sender, tmp_path):
    f = tmp_path / "r.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    msg = sender.build_message("you@example.com", "ทดสอบ หัวเรื่อง", "สวัสดี", str(f))
    parts = msg.get_payload()
    assert len(parts) == 2
    assert parts[1].get_filename() == "r.pdf"
    assert "สวัสดี" in parts[0].get_payload(decode=True).decode("utf-8")


def test_build_message_missing_attachment(sender):
    msg = sender.build_message("you@example.com", "s", "b", "/no/such/file.pdf")
    assert len(msg.get_payload()) == 1


@patch("src.email_sender.smtplib.SMTP")
def test_send_email_success(mock_smtp, sender):
    server = mock_smtp.return_value
    assert sender.send_email("you@example.com", "s", "b") is True
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("me@example.com", "pw")
    server.send_message.assert_called_once()
    server.quit.assert_called_once()


@patch("src.email_sender.smtplib.SMTP")
def test_send_email_auth_failure(mock_smtp, sender):
    import smtplib
    mock_smtp.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad")
    assert sender.send_email("you@example.com", "s", "b") is False


# ---------- sms ----------
def test_sms_gateway_address(sender):
    gw = SMSGateway(sender)
    assert gw.build_gateway_address("123-456-7890", "att") == "1234567890@txt.att.net"
    assert gw.build_gateway_address("x@sms.example.com") == "x@sms.example.com"
    assert gw.build_gateway_address("1234567890", "unknown") is None


def test_sms_requires_email_sender():
    with pytest.raises(TypeError):
        SMSGateway(object())


def test_send_sms_delegates(sender):
    sender.send_email = MagicMock(return_value=True)
    assert SMSGateway(sender).send_sms("1234567890", "hi", "verizon") is True
    sender.send_email.assert_called_once_with("1234567890@vtext.com", "", "hi")


# ---------- receiver ----------
def _sample_email(tmp_path):
    msg = MIMEMultipart()
    msg["From"] = "me@example.com"
    msg["Subject"] = "ทดสอบ Python Test: Email for Receiving Demo"
    msg.attach(MIMEText("เนื้อหา body", "plain", "utf-8"))
    att = MIMEApplication(b"%PDF data", Name="dummy_report.pdf")
    att["Content-Disposition"] = 'attachment; filename="dummy_report.pdf"'
    msg.attach(att)
    return msg


def test_parse_message(tmp_path):
    r = EmailReceiver("imap.example.com", "me@example.com", "pw")
    out_dir = tmp_path / "att"
    details = r.parse_message(_sample_email(tmp_path), str(out_dir))
    assert details["subject"].startswith("ทดสอบ")
    assert "เนื้อหา" in details["body_snippet"]
    assert (out_dir / "dummy_report.pdf").read_bytes() == b"%PDF data"


def test_build_search_query():
    q = EmailReceiver.build_search_query("UNSEEN", "me@example.com", "Email for Receiving Demo")
    assert q == ["UNSEEN", "FROM", '"me@example.com"', "SUBJECT", '"Email for Receiving Demo"']


@patch("src.email_receiver.imaplib.IMAP4_SSL")
def test_search_and_fetch(mock_imap, tmp_path):
    mail = mock_imap.return_value
    raw = _sample_email(tmp_path).as_bytes()

    def uid_side_effect(cmd, *args):
        if cmd == "SEARCH":
            return "OK", [b"11 12"]
        if cmd == "FETCH":
            return "OK", [(b"11 (BODY[] {n}", raw), b")"]
        return "OK", [b""]

    mail.uid.side_effect = uid_side_effect
    r = EmailReceiver("imap.example.com", "me@example.com", "pw")
    assert r.search_emails() == [b"11", b"12"]

    details = r.fetch_email_content(b"11", mark_as_read=True, download_attachments_dir=str(tmp_path))
    assert details["uid"] == "11"
    mail.uid.assert_any_call("STORE", b"11", "+FLAGS", "(\\Seen)")
