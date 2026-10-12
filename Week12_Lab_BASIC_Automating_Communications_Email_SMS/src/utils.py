# email-sms-automator/src/utils.py
import logging
import os

from dotenv import load_dotenv

# Load environment variables from .env file (project root)
load_dotenv()

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def setup_logging(name, level=logging.INFO):
    """Sets up a logger for specific modules."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:  # Prevent adding multiple handlers if called multiple times
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(ch)
        logger.propagate = False  # Avoid duplicated log lines via the root logger
    return logger


_logger = setup_logging(__name__)


def get_env_variable(var_name, default=None):
    """Retrieves an environment variable, raising an error if not found and no default given."""
    value = os.getenv(var_name, default)
    if value is None or str(value).strip() == "":
        raise ValueError(
            f"Environment variable '{var_name}' not set. "
            f"Please check your .env file or environment settings."
        )
    return value.strip()


def ensure_directory_exists(path):
    """Ensures that a directory exists, creating it if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        _logger.info(f"Directory ensured: {path}")
    except OSError as e:
        _logger.error(f"Error creating directory {path}: {e}")
        raise
