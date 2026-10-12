# agentic-comm-automator/src/communication_agent.py
"""
CommunicationAgent – reads a declarative JSON workflow, dispatches each task to a handler,
keeps a shared context (self.context) for templating / task chaining, and writes an audit report.
"""
import datetime
import json
import os
import time

from .email_tasks import EmailTasks, MockEmailTasks
from .sms_tasks import SMSTasks
from .template_renderer import TemplateRenderer
from .utils import ensure_directory_exists, get_env_variable, log_audit_entry, setup_logging

logger = setup_logging(__name__)

DRY_RUN_ENV_DEFAULTS = {
    "SENDER_EMAIL": "agent@example.com",
    "TEST_RECIPIENT_EMAIL": "team@example.com",
    "TEST_SMS_PHONE_NUMBER": "1234567890",
    "TEST_SMS_CARRIER": "att",
}


class CommunicationAgent:
    def __init__(self, config, base_dir, dry_run=False, email_tasks=None):
        self.config = config
        self.base_dir = os.path.abspath(base_dir)
        self.dry_run = dry_run
        self.audit_log = []
        self.context = {}
        self.task_results = []  # [{name, type, status}]
        self.start_time = datetime.datetime.now()
        self.run_id = self.start_time.strftime("%Y%m%d-%H%M%S")
        self.template_renderer = TemplateRenderer()

        if email_tasks is not None:
            self.email_tasks = email_tasks
        elif dry_run:
            for k, v in DRY_RUN_ENV_DEFAULTS.items():
                os.environ.setdefault(k, v)
            run_dir = os.path.join(self.base_dir, "data", "dry_run")
            self.email_tasks = MockEmailTasks(
                sender_email=os.environ["SENDER_EMAIL"],
                mailbox_dir=os.path.join(run_dir, "mailbox"),
                outbox_dir=os.path.join(run_dir, "outbox", self.run_id),
            )
        else:
            try:
                self.email_tasks = EmailTasks(
                    smtp_server=get_env_variable("SMTP_SERVER", "smtp.gmail.com"),
                    smtp_port=int(get_env_variable("SMTP_PORT", "587")),
                    imap_server=get_env_variable("IMAP_SERVER", "imap.gmail.com"),
                    sender_email=get_env_variable("SENDER_EMAIL"),
                    sender_password=get_env_variable("SENDER_APP_PASSWORD"),
                )
            except ValueError as e:
                logger.critical(f"Agent initialization failed: {e}")
                raise
        self.sms_tasks = SMSTasks(self.email_tasks)

        # Task dispatcher: task "type" in the JSON -> handler method
        self.handlers = {
            "send_email": self._handle_send_email,
            "send_sms": self._handle_send_sms,
            "process_inbox": self._handle_process_inbox,
        }
        logger.info(f"CommunicationAgent initialized (dry_run={dry_run}, run_id={self.run_id}).")

    # ------------------------------------------------------------ context helpers
    def _update_context(self, key, value):
        self.context[key] = value
        logger.debug(f"Context updated: '{key}' = {value}")

    def _get_context_value(self, key, default=None):
        return self.context.get(key, default)

    def _render_template(self, template_string, extra=None):
        ctx = {**self.context, **(extra or {})}
        try:
            return self.template_renderer.render(template_string, ctx)
        except Exception as e:
            log_audit_entry(self.audit_log, "ERROR", f"Template rendering failed: {e}", "template_render",
                            {"template": template_string, "available_keys": sorted(ctx.keys())})
            raise

    def _abs_path(self, path):
        return path if os.path.isabs(path) else os.path.join(self.base_dir, path)

    def _rel_path(self, path):
        try:
            return os.path.relpath(path, self.base_dir)
        except ValueError:
            return path

    # ------------------------------------------------------------ task handlers
    def _handle_send_email(self, params):
        raw_recipients = params.get("recipients") or {"to": params.get("to", [])}
        recipients = {k: [self._render_template(r) for r in v] for k, v in raw_recipients.items()}
        subject = self._render_template(params["subject_template"])
        body = self._render_template(params["body_template"])

        # Conditional attachments: string = attach if it exists;
        # object = {"path": ..., "required": bool, "only_if_context": "key"}
        attachments, skipped = [], []
        for att in params.get("attachments", []):
            spec = att if isinstance(att, dict) else {"path": att}
            if spec.get("only_if_context") and not self._get_context_value(spec["only_if_context"]):
                skipped.append({"path": spec["path"], "reason": f"context '{spec['only_if_context']}' is empty"})
                continue
            path = self._abs_path(self._render_template(spec["path"]))
            if not os.path.isfile(path):
                if spec.get("required"):
                    raise FileNotFoundError(f"Required attachment not found: {path}")
                skipped.append({"path": self._rel_path(path), "reason": "file not found"})
                log_audit_entry(self.audit_log, "WARNING", f"Optional attachment missing, skipped: {path}",
                                "send_email")
                continue
            attachments.append(path)

        result = self.email_tasks.send_email(recipients, subject, body, attachments,
                                             is_html=params.get("is_html", False))
        output = {"recipients": recipients, "subject": subject,
                  "attachments": [self._rel_path(p) for p in result["attached"]],
                  "skipped_attachments": skipped, "message_id": result["message_id"]}
        return result["success"], output

    def _handle_send_sms(self, params):
        numbers = [self._render_template(p) for p in params["phone_numbers"]]
        message = self._render_template(params["message_template"])
        carrier = self._render_template(params.get("carrier_name"))
        result = self.sms_tasks.send_sms(numbers, message, carrier)
        return result["success"], {"phone_numbers": numbers, "message": result["message"],
                                   "sent_via": result["sent"], "failed": result["failed"]}

    def _handle_process_inbox(self, params):
        mailbox = params.get("mailbox", "INBOX")
        criteria = params["search_criteria"]
        status = criteria.get("status", "UNSEEN")
        from_sender = self._render_template(criteria.get("from_sender")) or None
        subject_contains = [self._render_template(t) for t in self._as_list(criteria.get("subject_contains") or [])]
        max_emails = int(params.get("max_emails", 20))
        wait_seconds = 0 if self.dry_run else int(params.get("wait_for_email_seconds", 0))
        poll_interval = max(1, int(params.get("poll_interval_seconds", 10)))
        rules = params.get("rules", [])

        # Poll the inbox: a just-sent email can take a few seconds to arrive.
        deadline = time.time() + wait_seconds
        while True:
            uids = self.email_tasks.search_emails(mailbox, status, from_sender, subject_contains)
            remaining = deadline - time.time()
            if uids or remaining <= 0:
                break
            logger.info(f"No matching email yet – checking again in {poll_interval}s "
                        f"({int(remaining)}s left).")
            time.sleep(min(poll_interval, remaining))

        search_info = {"mailbox": mailbox, "status": status, "from_sender": from_sender,
                       "subject_contains": subject_contains, "emails_found": len(uids)}
        if not uids:
            log_audit_entry(self.audit_log, "INFO", "No emails matched the search criteria.", "process_inbox",
                            search_info)
            return True, {"search": search_info, "processed_emails": []}

        processed, fetch_errors = [], 0
        for uid in uids[-max_emails:]:
            info = self.email_tasks.fetch_email_content(uid, mailbox=mailbox)
            if not info:
                fetch_errors += 1
                log_audit_entry(self.audit_log, "ERROR", f"Failed to fetch email UID {uid!r}", "process_inbox")
                continue
            info.update({"downloaded_files": "none", "matched_rules": [], "actions": []})
            for idx, rule in enumerate(rules):
                rule_name = rule.get("name", f"rule_{idx + 1}")
                if self._rule_matches(rule.get("if", {}), info):
                    logger.info(f"Rule '{rule_name}' matched email UID {info['uid']}.")
                    info["matched_rules"].append(rule_name)
                    self._apply_actions(rule_name, rule["then"], info, uid, mailbox)
            if not info["matched_rules"]:
                logger.info(f"No rule matched email UID {info['uid']}.")
            processed.append({k: info[k] for k in (
                "uid", "sender", "subject", "date", "has_attachments", "attachments_meta",
                "matched_rules", "actions")})
            log_audit_entry(self.audit_log, "INFO", f"Processed email UID {info['uid']}: '{info['subject']}'",
                            "process_inbox", {"matched_rules": info["matched_rules"], "actions": info["actions"]})

        self._update_context("last_processed_count", len(processed))
        success = fetch_errors == 0
        return success, {"search": search_info, "processed_emails": processed, "fetch_errors": fetch_errors}

    # ------------------------------------------------------------ rule engine
    @staticmethod
    def _as_list(value):
        return value if isinstance(value, list) else [value]

    def _rule_matches(self, conditions, info):
        """All conditions must be true (AND). A list value means 'any of these' (OR). Case-insensitive."""
        ctx = info
        body = (info["text_body"] + "\n" + info["html_body"]).lower()
        for cond, expected in conditions.items():
            if cond == "has_attachments":
                if bool(expected) != info["has_attachments"]:
                    return False
                continue
            values = [self._render_template(v, ctx).lower() for v in self._as_list(expected)]
            if cond == "from_sender_contains":
                ok = any(v in info["sender"].lower() for v in values)
            elif cond == "subject_contains":
                ok = any(v in info["subject"].lower() for v in values)
            elif cond == "body_contains":
                ok = any(v in body for v in values)
            elif cond == "attachment_extension":
                exts = [v if v.startswith(".") else "." + v for v in values]
                ok = any(a["filename"].lower().endswith(tuple(exts)) for a in info["attachments_meta"])
            else:
                logger.warning(f"Unknown condition '{cond}' – treated as not matched.")
                ok = False
            if not ok:
                return False
        return True

    def _apply_actions(self, rule_name, actions, info, uid, mailbox):
        def record(action, ok, detail=None):
            entry = {"rule": rule_name, "action": action, "success": ok, "detail": detail}
            info["actions"].append(entry)
            log_audit_entry(self.audit_log, "SUCCESS" if ok else "ERROR",
                            f"Rule '{rule_name}' -> {action} ({'ok' if ok else 'failed'})",
                            "process_inbox_rule", {"uid": info["uid"], "detail": detail})

        if actions.get("download_attachments_to"):
            target = self._abs_path(self._render_template(actions["download_attachments_to"], info))
            rename_tpl = actions.get("rename_template")

            def rename(original):
                if not rename_tpl:
                    return original
                stem, ext = os.path.splitext(original)
                return self._render_template(rename_tpl, {**info, "filename": original, "stem": stem, "ext": ext})

            saved = self.email_tasks.save_attachments(uid, target, actions.get("attachment_extensions"),
                                                      rename, mailbox)
            for s in saved:
                s["filepath"] = self._rel_path(s["filepath"])
            if saved:
                info["attachments_meta"] = saved
                info["downloaded_files"] = ", ".join(s["filepath"] for s in saved)
                self._update_context("last_downloaded_files", [s["filepath"] for s in saved])
            record("download_attachments", True, {"saved": [s["filepath"] for s in saved]})

        if actions.get("mark_as_read"):
            record("mark_as_read", self.email_tasks.mark_as_read(uid, mailbox))

        if actions.get("send_sms_alert"):
            msg = self._render_template(actions.get(
                "alert_message_template", "Urgent email received: {subject} from {sender_address}"), info)
            numbers = [self._render_template(p, info) for p in actions.get("alert_phone_numbers", [])]
            carrier = self._render_template(actions.get("alert_carrier"), info)
            result = self.sms_tasks.send_sms(numbers, msg, carrier)
            record("send_sms_alert", result["success"], {"message": result["message"], "sent_via": result["sent"]})

        if actions.get("reply_with_template"):
            body = self._render_template(actions["reply_with_template"], info)
            subject = self._render_template(actions.get("reply_subject_template", "Re: {subject}"), info)
            result = self.email_tasks.send_email({"to": [info["sender_address"]]}, subject, body,
                                                 in_reply_to=info.get("message_id") or None)
            record("reply", result["success"], {"to": info["sender_address"], "subject": subject})

    # ------------------------------------------------------------ orchestration
    def _process_task(self, task):
        task_type = task.get("type")
        task_name = task.get("name", task_type)
        output_key = task.get("output_context_key")
        logger.info(f"===== Executing task: '{task_name}' (type: {task_type}) =====")
        log_audit_entry(self.audit_log, "INFO", f"Starting task '{task_name}'", task_type,
                        {"parameters": task.get("parameters", {})})

        handler = self.handlers.get(task_type)
        if handler is None:
            log_audit_entry(self.audit_log, "WARNING", f"Unsupported task type: {task_type} – skipped", task_type)
            self.task_results.append({"name": task_name, "type": task_type, "status": "SKIPPED"})
            return "SKIPPED"

        started = time.time()
        try:
            success, output = handler(task.get("parameters", {}))
        except Exception as e:
            logger.error(f"Error during task '{task_name}': {e}", exc_info=True)
            log_audit_entry(self.audit_log, "ERROR", f"An error occurred during task '{task_name}': {e}",
                            task_type, {"error": str(e)})
            self.task_results.append({"name": task_name, "type": task_type, "status": "ERROR", "error": str(e)})
            return "ERROR"

        duration = round(time.time() - started, 2)
        if success and output_key:
            self._update_context(output_key, output)
        status = "SUCCESS" if success else "ERROR"
        log_audit_entry(self.audit_log, status,
                        f"Task '{task_name}' {'completed successfully' if success else 'failed'} in {duration}s.",
                        task_type, {"output": output})
        self.task_results.append({"name": task_name, "type": task_type, "status": status, "seconds": duration})
        return status

    def _send_error_notification(self):
        notify = self.config.get("error_notification") or {}
        failed = [r for r in self.task_results if r["status"] == "ERROR"]
        if not failed or not notify.get("enabled", True) or not notify.get("to"):
            return
        try:
            to = [self._render_template(r) for r in notify["to"]]
            subject = self._render_template(notify.get(
                "subject_template", "[Agent ERROR] {error_count} task(s) failed in run {run_id}"),
                {"error_count": len(failed)})
            lines = [f"- {r['name']} ({r['type']}): {r.get('error', 'see audit report')}" for r in failed]
            body = (f"Communication Agent run {self.run_id} finished with errors:\n\n" + "\n".join(lines)
                    + "\n\nCheck the JSON audit report in the reports/ folder for full details.")
            result = self.email_tasks.send_email({"to": to}, subject, body)
            log_audit_entry(self.audit_log, "INFO" if result["success"] else "ERROR",
                            f"Error notification {'sent' if result['success'] else 'could not be sent'} to {to}",
                            "error_notification")
        except Exception as e:
            log_audit_entry(self.audit_log, "ERROR", f"Error notification failed: {e}", "error_notification")

    def _generate_audit_report(self, output_dir):
        ensure_directory_exists(output_dir)
        report_path = os.path.join(output_dir, f"audit_report_comm_{self.run_id.replace('-', '_')}.json")
        counts = {s: sum(1 for r in self.task_results if r["status"] == s) for s in ("SUCCESS", "ERROR", "SKIPPED")}
        log_audit_entry(self.audit_log, "INFO", f"Audit report generated at {self._rel_path(report_path)}",
                        "audit_report")
        report = {
            "run_id": self.run_id,
            "dry_run": self.dry_run,
            "started_at": self.start_time.isoformat(),
            "finished_at": datetime.datetime.now().isoformat(),
            "summary": {"total_tasks": len(self.task_results), **counts},
            "tasks": self.task_results,
            "final_context_keys": sorted(self.context.keys()),
            "entries": self.audit_log,
        }
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4, ensure_ascii=False, default=str)
            logger.info(f"Audit report saved to: {report_path}")
        except OSError as e:
            logger.critical(f"Failed to save audit report: {e}")
        return report_path

    def run(self):
        """Executes all tasks in order. Returns a summary dict."""
        logger.info("Starting Communication Agent run...")
        log_audit_entry(self.audit_log, "INFO", "Communication Agent started.", "agent_run",
                        {"run_id": self.run_id, "dry_run": self.dry_run})

        # Simulated data that would normally come from an earlier agent (e.g. the Week 20 DataAgent)
        self._update_context("run_id", self.run_id)
        self._update_context("report_name", "DailySalesSummary")
        self._update_context("report_date", datetime.date.today().strftime("%Y-%m-%d"))
        self._update_context("sales_figure", 12345.67)
        self._update_context("total_customers", 500)
        self._update_context("attachment_path_1", "data/reports/sales_report.pdf")
        self._update_context("attachment_path_2", "data/reports/summary_data.xlsx")
        for key, value in (self.config.get("initial_context") or {}).items():
            self._update_context(key, value)

        stop_on_error = self.config.get("stop_on_error", False)
        for task in self.config.get("tasks", []):
            status = self._process_task(task)
            if status == "ERROR" and stop_on_error:
                log_audit_entry(self.audit_log, "WARNING", "stop_on_error is true – remaining tasks skipped.",
                                "agent_run")
                break

        self._send_error_notification()
        duration = (datetime.datetime.now() - self.start_time).total_seconds()
        log_audit_entry(self.audit_log, "INFO", f"Communication Agent finished in {duration:.2f} seconds.",
                        "agent_run_summary", {"tasks": self.task_results})
        report_path = self._generate_audit_report(os.path.join(self.base_dir, "reports"))
        failed = sum(1 for r in self.task_results if r["status"] == "ERROR")
        logger.info(f"Communication Agent finished: {len(self.task_results) - failed} ok, {failed} failed, "
                    f"{duration:.2f}s.")
        return {"run_id": self.run_id, "failed": failed, "tasks": self.task_results, "audit_report": report_path}
