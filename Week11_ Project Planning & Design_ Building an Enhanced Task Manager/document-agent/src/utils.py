import logging
import os


def setup_logging(name):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger(name)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
