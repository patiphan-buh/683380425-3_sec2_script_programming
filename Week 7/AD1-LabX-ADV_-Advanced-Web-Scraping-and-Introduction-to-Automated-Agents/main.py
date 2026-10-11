# agentic-web-scraper/main.py
import argparse
import logging
import os

from src.config_parser import ConfigParser
from src.scraper_agent import ScraperAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "example_site_config.json")


def main():
    """Main entry point: loads config and runs the scraping agent."""
    parser = argparse.ArgumentParser(description="Config-driven product scraper agent")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="path to the JSON config file")
    parser.add_argument("--browser", default="chrome", choices=["chrome", "firefox"])
    parser.add_argument("--show-browser", action="store_true",
                        help="run with a visible browser window (useful for debugging)")
    args = parser.parse_args()

    try:
        config = ConfigParser(args.config).load_config()
        agent = ScraperAgent(config, browser=args.browser, headless=not args.show_browser)
        agent.run()
    except FileNotFoundError as e:
        logging.error(f"Configuration file error: {e}")
    except ValueError as e:
        logging.error(f"Configuration validation error: {e}")
        logging.info("Please check the format and required fields in your config file.")
    except Exception as e:
        logging.critical(f"An unexpected error occurred during execution: {e}")


if __name__ == "__main__":
    main()
