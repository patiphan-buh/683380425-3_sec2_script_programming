import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, 'src'))

from config_parser import load_config
from document_agent import DocumentAgent


def main():
    config = load_config(os.path.join(BASE, 'configs', 'document_automation_config.json'))
    agent = DocumentAgent(config, BASE)
    agent.run_all()


if __name__ == "__main__":
    main()
