# enhanced-task-manager-design/main.py
"""Orchestrator: เชื่อม TaskManager (logic) กับ CLIInterface (UI)"""
import sys

from src.task_manager import TaskManager
from src.cli_interface import CLIInterface


def main():
    # ให้ terminal Windows แสดงภาษาไทยได้ถูกต้อง
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    manager = TaskManager()
    cli = CLIInterface(manager)
    try:
        cli.run()
    except (KeyboardInterrupt, EOFError):
        print("\nออกจากโปรแกรม ขอบคุณที่ใช้งาน!")


if __name__ == "__main__":
    main()
