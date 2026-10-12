import json
import os
from utils import setup_logging

logger = setup_logging(__name__)


def load_config(path):
    """Load the JSON config and validate that it contains a task list."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, encoding='utf-8') as f:
        config = json.load(f)
    if not isinstance(config.get('tasks'), list) or not config['tasks']:
        raise ValueError("Config must contain a non-empty 'tasks' list.")
    logger.info(f"Loaded config with {len(config['tasks'])} tasks.")
    return config
