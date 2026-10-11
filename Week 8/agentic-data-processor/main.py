# agentic-data-processor/main.py
import sys
import os
import json

# Add the 'src' directory to the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from agent import DataPipelineAgent
from utils import setup_logging

logger = setup_logging(__name__)

def main():
    config_path = os.path.join(BASE_DIR, 'configs', 'data_pipeline_config.json')
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    agent = DataPipelineAgent(config, BASE_DIR)
    report_path = agent.run()
    logger.info(f"Done. See report: {report_path}")

if __name__ == "__main__":
    main()
