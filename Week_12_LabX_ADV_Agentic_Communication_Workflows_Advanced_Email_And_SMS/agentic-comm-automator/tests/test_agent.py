# agentic-comm-automator/tests/test_agent.py
"""Run with:  python -m unittest discover -s tests -v   (no network or credentials needed)"""
import copy
import email
import json
import os
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.communication_agent import CommunicationAgent  # noqa: E402
from src.config_parser import ConfigParser  # noqa: E402
from src.email_tasks import MockEmailTasks  # noqa: E402
from src.sample_data import ensure_sample_files  # noqa: E402
from src.sms_tasks import SMSTasks  # noqa: E402
from src.template_renderer import TemplateRenderer  # noqa: E402

def _body(eml_path):
    with open(eml_path, "rb") as f:
        msg = email.message_from_bytes(f.read())
    return "".join(p.get_payload(decode=True).decode() for p in msg.walk()
                   if p.get_content_maintype() == "text")


CONFIG_PATH = os.path.join(PROJECT_ROOT, "configs", "comm_pipeline_config.json")


class TemplateRendererTests(unittest.TestCase):
    def setUp(self):
        self.r = TemplateRenderer()
        os.environ["UNIT_TEST_VAR"] = "hello@example.com"

    def test_context_and_format_spec(self):
        self.assertEqual(self.r.render("Sales ${sales:,.2f} on {d}", {"sales": 12345.67, "d": "2026-10-12"}),
                         "Sales $12,345.67 on 2026-10-12")

    def test_env_var(self):
        self.assertEqual(self.r.render("to ${UNIT_TEST_VAR}", {}), "to hello@example.com")

    def test_missing_key_raises(self):
        with self.assertRaises(ValueError):
            self.r.render("{nope}", {})

    def test_missing_env_raises(self):
        with self.assertRaises(ValueError):
            self.r.render("${DEFINITELY_NOT_SET_123}", {})

    def test_index_access(self):
        self.assertEqual(self.r.render("{a[0][f]}", {"a": [{"f": "x.pdf"}]}), "x.pdf")


class ConfigParserTests(unittest.TestCase):
    def _write(self, data):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        self.addCleanup(os.remove, path)
        return path

    def test_project_config_is_valid(self):
        cfg = ConfigParser(CONFIG_PATH).load_config()
        self.assertEqual(len(cfg["tasks"]), 5)

    def test_missing_tasks(self):
        with self.assertRaises(ValueError):
            ConfigParser(self._write({})).load_config()

    def test_send_email_needs_recipient(self):
        bad = {"tasks": [{"name": "x", "type": "send_email",
                          "parameters": {"recipients": {"to": []}, "subject_template": "s", "body_template": "b"}}]}
        with self.assertRaises(ValueError):
            ConfigParser(self._write(bad)).load_config()

    def test_unknown_rule_condition(self):
        bad = {"tasks": [{"name": "x", "type": "process_inbox", "parameters": {
            "search_criteria": {}, "rules": [{"if": {"color_is": "red"}, "then": {"mark_as_read": True}}]}}]}
        with self.assertRaises(ValueError):
            ConfigParser(self._write(bad)).load_config()


class SMSTests(unittest.TestCase):
    def test_gateway_resolution(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        sms = SMSTasks(MockEmailTasks("me@example.com", tmp + "/mb", tmp + "/out"))
        self.assertEqual(sms.resolve_gateway("(123) 456-7890", "ATT"), "1234567890@txt.att.net")
        self.assertEqual(sms.resolve_gateway("me@example.com", None), "me@example.com")
        self.assertIsNone(sms.resolve_gateway("1234567890", "unknown"))


class AgentWorkflowTests(unittest.TestCase):
    """Runs the real project config end-to-end against the mock mail server."""

    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base)
        ensure_sample_files(self.base)
        for k, v in {"SENDER_EMAIL": "agent@example.com", "TEST_RECIPIENT_EMAIL": "team@example.com",
                     "TEST_SMS_PHONE_NUMBER": "1234567890", "TEST_SMS_CARRIER": "att"}.items():
            os.environ[k] = v
        self.config = ConfigParser(CONFIG_PATH).load_config()
        self.mail = MockEmailTasks("agent@example.com", os.path.join(self.base, "mb"), os.path.join(self.base, "out"))

    def _run(self, config):
        agent = CommunicationAgent(config, self.base, dry_run=True, email_tasks=self.mail)
        return agent, agent.run()

    def test_full_pipeline(self):
        agent, summary = self._run(self.config)
        self.assertEqual(summary["failed"], 0, summary["tasks"])
        self.assertTrue(all(t["status"] == "SUCCESS" for t in summary["tasks"]))

        subjects = [m["subject"] for m in self.mail.sent_messages]
        self.assertIn(f"Daily Sales Report - {agent.context['report_date']}", subjects)

        # rule 1: only the PDF is downloaded and renamed, email marked as read
        saved = os.listdir(os.path.join(self.base, "data", "incoming_attachments"))
        self.assertEqual(len(saved), 1)
        self.assertTrue(saved[0].endswith("sales_report.pdf"))
        request_uid = agent.context["processed_inbox_results"]["processed_emails"][0]["uid"].encode()
        self.assertIn(request_uid, self.mail.search_emails(criteria="SEEN"))
        self.assertNotIn(request_uid, self.mail.search_emails(criteria="UNSEEN"))

        # rule 2 (SMS alert) and rule 3 (auto-reply)
        processed = agent.context["processed_inbox_results"]["processed_emails"]
        self.assertEqual(len(processed), 1)
        self.assertEqual(len(processed[0]["matched_rules"]), 3)
        self.assertTrue(any(m["to"] == ["1234567890@txt.att.net"] and "URGENT" in _body(m["file"])
                            for m in self.mail.sent_messages))
        self.assertTrue(any(m["subject"].startswith("Re: Data Request") for m in self.mail.sent_messages))

        # audit report
        with open(summary["audit_report"], encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["summary"]["SUCCESS"], 5)
        self.assertNotIn("SENDER_APP_PASSWORD", json.dumps(report))

    def test_bcc_not_in_headers(self):
        self._run(self.config)
        html_mail = next(m for m in self.mail.sent_messages if m["subject"].startswith("[HTML]"))
        self.assertIn("agent@example.com", html_mail["to"])
        with open(html_mail["file"]) as f:
            self.assertNotIn("Bcc", f.read())

    def test_missing_required_attachment_fails_task_and_sends_alert(self):
        os.remove(os.path.join(self.base, "data", "reports", "sales_report.pdf"))
        _, summary = self._run(self.config)
        self.assertEqual(summary["tasks"][0]["status"], "ERROR")
        self.assertTrue(any(m["subject"].startswith("[Agent ERROR]") for m in self.mail.sent_messages))

    def test_no_matching_email_is_not_an_error(self):
        cfg = copy.deepcopy(self.config)
        cfg["tasks"] = [t for t in cfg["tasks"] if t["type"] == "process_inbox"]
        _, summary = self._run(cfg)
        self.assertEqual(summary["tasks"][0]["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
