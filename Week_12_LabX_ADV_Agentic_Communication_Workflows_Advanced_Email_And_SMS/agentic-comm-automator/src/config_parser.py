# agentic-comm-automator/src/config_parser.py
import json
import os

from .utils import setup_logging

logger = setup_logging(__name__)

SUPPORTED_TASK_TYPES = ("send_email", "send_sms", "process_inbox")
SUPPORTED_CONDITIONS = (
    "from_sender_contains", "subject_contains", "body_contains",
    "has_attachments", "attachment_extension",
)
SUPPORTED_ACTIONS = (
    "download_attachments_to", "attachment_extensions", "rename_template", "mark_as_read",
    "send_sms_alert", "alert_phone_numbers", "alert_carrier", "alert_message_template",
    "reply_with_template", "reply_subject_template",
)


class ConfigParser:
    """Parses and validates the communication automation configuration from a JSON file."""

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}

    def load_config(self):
        if not os.path.exists(self.config_path):
            logger.critical(f"Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON format in config file: {e}")
            raise ValueError(f"Invalid JSON format in config file: {e}") from e
        self._validate_config()
        logger.info(f"Configuration loaded successfully from {self.config_path}")
        return self.config

    @staticmethod
    def _is_str_list(value):
        return isinstance(value, list) and all(isinstance(v, str) for v in value)

    def _validate_config(self):
        if not isinstance(self.config, dict) or "tasks" not in self.config:
            raise ValueError("Missing required field in config: 'tasks'")
        if not isinstance(self.config["tasks"], list) or not self.config["tasks"]:
            raise ValueError("Config field 'tasks' must be a non-empty list.")

        names = set()
        for i, task in enumerate(self.config["tasks"]):
            if not isinstance(task, dict):
                raise ValueError(f"Task {i} must be a JSON object.")
            if "type" not in task:
                raise ValueError(f"Task {i} is missing 'type' field.")
            if "name" not in task:
                raise ValueError(f"Task {i} (type: {task['type']}) is missing 'name' field.")
            if task["name"] in names:
                raise ValueError(f"Task name '{task['name']}' is used more than once.")
            names.add(task["name"])

            params = task.get("parameters")
            ttype = task["type"]
            label = f"Task {i} ('{task['name']}', {ttype})"

            if ttype not in SUPPORTED_TASK_TYPES:
                logger.warning(f"{label}: unsupported task type – it will be skipped at runtime.")
                continue
            if not isinstance(params, dict):
                raise ValueError(f"{label} requires a 'parameters' object.")

            if ttype == "send_email":
                self._validate_send_email(params, label)
            elif ttype == "send_sms":
                for k in ("phone_numbers", "message_template"):
                    if k not in params:
                        raise ValueError(f"{label} requires '{k}' in parameters.")
                if not self._is_str_list(params["phone_numbers"]) or not params["phone_numbers"]:
                    raise ValueError(f"{label} 'phone_numbers' must be a non-empty list of strings.")
            elif ttype == "process_inbox":
                self._validate_process_inbox(params, label)

        notify = self.config.get("error_notification")
        if notify is not None:
            if not isinstance(notify, dict) or not self._is_str_list(notify.get("to", [])):
                raise ValueError("'error_notification' must be an object with a 'to' list.")
        logger.info("Configuration validated.")

    def _validate_send_email(self, params, label):
        for k in ("subject_template", "body_template"):
            if k not in params:
                raise ValueError(f"{label} requires '{k}' in parameters.")
        # Accept either {"recipients": {"to": [...], "cc": [...], "bcc": [...]}} or legacy {"to": [...]}
        recipients = params.get("recipients", {"to": params.get("to", [])})
        if not isinstance(recipients, dict):
            raise ValueError(f"{label} 'recipients' must be an object with to/cc/bcc lists.")
        for key, value in recipients.items():
            if key not in ("to", "cc", "bcc"):
                raise ValueError(f"{label} unknown recipients field '{key}' (use to/cc/bcc).")
            if not self._is_str_list(value):
                raise ValueError(f"{label} recipients '{key}' must be a list of strings.")
        if not any(recipients.get(k) for k in ("to", "cc", "bcc")):
            raise ValueError(f"{label} needs at least one recipient in to/cc/bcc.")
        attachments = params.get("attachments", [])
        if not isinstance(attachments, list):
            raise ValueError(f"{label} 'attachments' parameter must be a list.")
        for att in attachments:
            if isinstance(att, dict):
                if "path" not in att:
                    raise ValueError(f"{label} attachment objects need a 'path'.")
            elif not isinstance(att, str):
                raise ValueError(f"{label} attachments must be strings or objects with 'path'.")

    def _validate_process_inbox(self, params, label):
        if "search_criteria" not in params or not isinstance(params["search_criteria"], dict):
            raise ValueError(f"{label} requires 'search_criteria' object in parameters.")
        rules = params.get("rules", [])
        if not isinstance(rules, list):
            raise ValueError(f"{label} 'rules' parameter must be a list.")
        for r, rule in enumerate(rules):
            if not isinstance(rule, dict) or not isinstance(rule.get("if", {}), dict) \
                    or not isinstance(rule.get("then"), dict):
                raise ValueError(f"{label} rule {r} must have an 'if' object and a 'then' object.")
            for cond in rule.get("if", {}):
                if cond not in SUPPORTED_CONDITIONS:
                    raise ValueError(f"{label} rule {r}: unknown condition '{cond}'. "
                                     f"Supported: {', '.join(SUPPORTED_CONDITIONS)}")
            for action in rule["then"]:
                if action not in SUPPORTED_ACTIONS:
                    raise ValueError(f"{label} rule {r}: unknown action '{action}'. "
                                     f"Supported: {', '.join(SUPPORTED_ACTIONS)}")
