# agentic-data-processor/main.py
import os
from src.config_parser import ConfigParser
from src.data_agent import DataAgent
from src.utils import setup_logging

logger = setup_logging(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    # ทำให้ path ใน config (เช่น data/input_sales.csv) อิงจากโฟลเดอร์โปรเจกต์เสมอ
    os.chdir(BASE_DIR)

    config_path = os.path.join(BASE_DIR, "configs", "data_pipeline_config.json")
    config = ConfigParser(config_path).load_config()

    agent = DataAgent(config)
    agent.run()

if __name__ == "__main__":
    main()
