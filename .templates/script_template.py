#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template for Python Scripts
===========================
Description:
    [Add a description of what this script does.]

Usage:
    python3 script_name.py [arguments]

Author:
    Theodore Bouskill

Date:
    2025-01-26
"""

import argparse
import logging
import os
import sys

try:
    from cls_env_config import EnvConfigSingleton as EnvConfig
    from cls_env_tools import EnvTools as EnvTools
    from cls_logging_manager import LoggingManagerSingleton as LoggingManager
    from cls_metrics_tracker import MetricsTrackerSingleton as MetricsTracker
    from cls_string_helpers import StringHelpers

except ImportError as e:
    print(f"Error importing cls_env_config: {e}")
    sys.exit(1)

# Set up root logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the script name without the extension
script_name = os.path.splitext(os.path.basename(__file__))[0]
script_dir = os.path.dirname(os.path.abspath(__file__))

logging.debug(f"Script directory: {script_dir}")
logging.debug(f"Script name: {script_name}")

logging_manager = None

try:
    logging_manager = LoggingManager(script_dir)
except Exception as e:
    logging.exception(f"Error initializing LoggingManager: {e}")
    sys.exit(1)

def setup_logging(log_level=logging.INFO):
    """Set up basic logging."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

    # Set up logging manager (different log levels for console and other handlers)
    # Console level is set to None by default, which means it will use the same level as the root logger which is WARNING
    logging_manager.setup_default_logging(script_name, log_level) # Optional: console_level=logging.INFO

    # Set up logging for specific loggers
    #logging_manager.setup_api_failures_logging(script_name, log_level=None)
    #logging_manager.setup_query_failures_logging(script_name, log_level=None)

    # Set up logging for all the above loggers
    #logging_manager.setup_all_logging(script_name, log_level, console_level=None)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Template script.")
    parser.add_argument("--example", type=str, help="Example argument")
    return parser.parse_args()


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()

    # Set up logging
    setup_logging()
    # In other scripts, you can access the LoggingManagerSingleton instance like this:
    # from cls_logging_manager import LoggingManagerSingleton as LoggingManager
    # logging_manager = LoggingManager(script_dir)

    env_config = EnvConfig()
    # In other scripts, you can access the EnvConfigSingleton instance like this:
    # from cls_env_config import EnvConfigSingleton as EnvConfig
    # env_config = EnvConfig()

    repo_root = EnvTools.find_repo_root()

    metrics_tracker = MetricsTracker()
    # In other scripts, you can access the MetricsTrackerSingleton instance like this:
    # from cls_metrics_tracker import MetricsTrackerSingleton as MetricsTracker

    try:
        metrics_tracker.start()

        # Start processing

    except Exception as e:
        logging.exception(f"Error in main: {e}")
    finally:
        logging.info("Script finished.")
        metrics_tracker.end()

        logging_manager.close()

if __name__ == "__main__":
    main()
