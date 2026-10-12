# agentic-spreadsheet-processor/main.py
import os

from src.utils import setup_logging
from src.config_parser import ConfigParser
from src.spreadsheet_agent import SpreadsheetAgent

# Set up main logger
logger = setup_logging(__name__)

def main():
    """
    Main entry point for the Agentic Spreadsheet Processor.
    Loads config and runs the agent.
    """
    # Make relative paths in the config (data/...) resolve from the project root
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    config_file_path = os.path.join('configs', 'example_spreadsheet_config.json')

    try:
        os.makedirs('data', exist_ok=True)

        logger.info(f"Loading configuration from: {config_file_path}")
        config_parser = ConfigParser(config_file_path)
        config = config_parser.load_config()

        input_file_path = config.get("input_file")
        if not os.path.exists(input_file_path):
            logger.critical(f"Input Excel file not found: '{input_file_path}'. Run create_dummy_data.py first.")
            logger.info("Refer to the README.md for example content and file structure.")
            return

        logger.info("Initializing Spreadsheet Agent...")
        agent = SpreadsheetAgent(config)

        logger.info("Running Spreadsheet Agent...")
        agent.run()

    except FileNotFoundError as e:
        logger.critical(f"File system error: {e}")
        logger.info("Please ensure all specified input files and configurations exist.")
    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
        logger.info("Please check the format and required fields in your config file.")
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred during execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()
