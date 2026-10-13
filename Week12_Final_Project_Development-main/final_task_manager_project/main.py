# final_task_manager_project/main.py
"""
Entry point for the Enhanced Task Manager.
Run from inside this folder:  python main.py
"""
import logging
import os
import sys

# Make sure the project root (the folder that contains 'src') is importable,
# so the relative imports inside the 'src' package work correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.task_manager import TaskManager  # noqa: E402
from src.cli_interface import CLIInterface  # noqa: E402

# Change to logging.INFO to see debug messages
logging.basicConfig(level=logging.WARNING, format="%(levelname)s - %(message)s")


def main():
    manager = TaskManager()
    cli = CLIInterface(manager)
    cli.run()


if __name__ == "__main__":
    main()
