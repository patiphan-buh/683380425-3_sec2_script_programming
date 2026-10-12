# agentic-comm-automator/src/utils.py
"""Logging, environment-variable loading, directory and audit helpers."""
import datetime
import logging
import os

from dotenv import load_dotenv

# Project root = parent of the src/ directory. Load .env from there so the agent
# works no matter which directory it is launched from.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# Values that must never be written to logs or audit reports.
SECRET_ENV_VARS = ("SENDER_APP_PASSWORD",)


def setup_logging(name, level=logging.INFO):
    """Returns a module logger that writes through the root handler (no duplicate lines)."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def add_file_logging(log_path, level=logging.INFO):
    """Additionally writes every log line to a file (used by main.py)."""
    ensure_directory_exists(os.path.dirname(log_path) or ".")
    root = logging.getLogger()
    for h in root.handlers:
        if isinstance(h, logging.FileHandler) and os.path.abspath(h.baseFilename) == os.path.abspath(log_path):
            return
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(fh)


def get_env_variable(var_name, default=None):
    """Retrieves an environment variable; raises if missing and no default is given."""
    value = os.getenv(var_name)
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(
            f"Environment variable '{var_name}' not set. Please check your .env file or environment settings."
        )
    return value


def mask_secrets(text):
    """Replaces any secret env value that appears in text with ***."""
    if not isinstance(text, str):
        return text
    for var in SECRET_ENV_VARS:
        secret = os.getenv(var)
        if secret:
            text = text.replace(secret, "***")
    return text


def ensure_directory_exists(path):
    """Ensures that a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        logging.debug(f"Directory ensured: {path}")
    except OSError as e:
        logging.error(f"Error creating directory {path}: {e}")
        raise


def log_audit_entry(audit_log_list, status, message, task_type="N/A", details=None):
    """Adds an entry to the audit log list and mirrors it to the console log."""
    message = mask_secrets(message)
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "status": status,
        "task_type": task_type,
        "message": message,
        "details": details if details else {},
    }
    audit_log_list.append(log_entry)
    if status in ("ERROR", "CRITICAL"):
        logging.error(f"AUDIT LOG - {status}: {message} | Task: {task_type} | Details: {details}")
    elif status == "WARNING":
        logging.warning(f"AUDIT LOG - {status}: {message} | Task: {task_type}")
    else:
        logging.info(f"AUDIT LOG - {status}: {message} | Task: {task_type}")
    return log_entry
