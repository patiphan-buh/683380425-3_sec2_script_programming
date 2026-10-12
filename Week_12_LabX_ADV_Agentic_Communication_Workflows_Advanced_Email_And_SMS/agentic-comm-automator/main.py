# agentic-comm-automator/main.py
"""
Entry point for the Agentic Communication Automator.

    python main.py              # real run (needs .env with Gmail + App Password)
    python main.py --dry-run    # offline demo: emails are written as .eml files, no credentials needed
    python main.py --config configs/other.json
"""
import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)  # so "src" is importable as a package

from src.communication_agent import CommunicationAgent  # noqa: E402
from src.config_parser import ConfigParser  # noqa: E402
from src.sample_data import ensure_sample_files  # noqa: E402
from src.utils import add_file_logging, ensure_directory_exists, setup_logging  # noqa: E402

logger = setup_logging("main")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the Communication Agent workflow.")
    parser.add_argument("--config", default=os.path.join("configs", "comm_pipeline_config.json"),
                        help="Path to the JSON workflow config (relative to the project folder).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Do not use the network: write emails to data/dry_run/ instead.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config_path = args.config if os.path.isabs(args.config) else os.path.join(BASE_DIR, args.config)

    for sub in ("data/reports", "data/attachments", "data/incoming_attachments", "configs", "reports", "logs"):
        ensure_directory_exists(os.path.join(BASE_DIR, sub))
    add_file_logging(os.path.join(BASE_DIR, "logs", "agent.log"))

    try:
        created = ensure_sample_files(BASE_DIR)
        for path in created:
            logger.info(f"Sample attachment created: {os.path.relpath(path, BASE_DIR)}")

        logger.info(f"Loading configuration from: {config_path}")
        config = ConfigParser(config_path).load_config()

        logger.info("Initializing Communication Agent...")
        agent = CommunicationAgent(config, BASE_DIR, dry_run=args.dry_run)

        logger.info("Running Communication Agent workflow...")
        summary = agent.run()
    except FileNotFoundError as e:
        logger.critical(f"File system error: {e}")
        return 1
    except ValueError as e:
        logger.critical(f"Configuration or environment variable error: {e}")
        logger.info("Check the config file and your .env (copy .env.example to .env).")
        return 1
    except Exception as e:  # pragma: no cover - last-resort guard
        logger.critical(f"Unexpected critical error: {e}", exc_info=True)
        return 1

    print("\n================ RUN SUMMARY ================")
    for t in summary["tasks"]:
        print(f"  [{t['status']:<7}] {t['name']}")
    print(f"  Audit report: {os.path.relpath(summary['audit_report'], BASE_DIR)}")
    if args.dry_run:
        print("  Dry-run emails: data/dry_run/outbox/  (open the .eml files to inspect them)")
    print("=============================================\n")
    return 2 if summary["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
