import atexit
import json
import logging
import os
import threading

from datetime import datetime

import colorama
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    FORMAT = "  %(asctime)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: Fore.BLUE + FORMAT + Style.RESET_ALL,
        logging.INFO: Style.BRIGHT + Fore.WHITE + FORMAT + Style.RESET_ALL,
        logging.WARNING: Style.BRIGHT + Fore.YELLOW + FORMAT + Style.RESET_ALL,
        logging.ERROR: Fore.RED + FORMAT + Style.RESET_ALL,
        logging.CRITICAL: Fore.YELLOW + Back.RED + Style.BRIGHT + FORMAT + Style.RESET_ALL,
    }

    def format(self, record):
        # Handle incorrect logging usage (comma-separated args without format placeholders)
        # Convert to string concatenation if no format placeholders found
        if record.args:
            msg = record.msg
            # Check if message has format placeholders
            has_placeholders = '%' in str(msg) or '{}' in str(msg)
            
            if not has_placeholders and record.args:
                # No placeholders but args provided - concatenate them
                processed_args = []
                args_to_process = record.args if isinstance(record.args, tuple) else [record.args]
                for arg in args_to_process:
                    if arg is None:
                        processed_args.append("<null>")
                    elif arg == "":
                        processed_args.append("<empty>")
                    else:
                        processed_args.append(str(arg))
                # Concatenate message with args
                record.msg = str(msg) + " " + " ".join(processed_args)
                record.args = ()  # Clear args since we've incorporated them into msg
            else:
                # Has placeholders - just handle None/empty values
                processed_args = []
                args_to_process = record.args if isinstance(record.args, tuple) else [record.args]
                for arg in args_to_process:
                    if arg is None:
                        processed_args.append("<null>")
                    elif arg == "":
                        processed_args.append("<empty>")
                    else:
                        processed_args.append(arg)
                record.args = tuple(processed_args) if len(processed_args) > 1 else (processed_args[0],) if processed_args else ()
        
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class DelayedFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        # Pass delay=True to the FileHandler constructor to defer file creation
        super().__init__(filename, mode, encoding, delay=True)

    def emit(self, record):
        # Ensure that the file is created only when the first log entry is written
        if self.stream is None:
            self.stream = self._open()
        super().emit(record)

class LoggingManagerSingleton:
    _instance = None
    _lock = threading.Lock()  # For thread safety
    _logger = None

    def __new__(cls, log_dir=None, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(LoggingManagerSingleton, cls).__new__(cls, *args, **kwargs)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, log_dir=None):
        if self._initialized:
            return

        print(f"Initializing LoggingManager with log_dir: {log_dir}")

        self._log_dir = log_dir  # Store the log directory
        self._current_date = datetime.now().strftime("%Y%m%d")
        self._initialized = True

        # Register the cleanup function to be called at program exit
        atexit.register(self._close_loggers)

    def _close_loggers(self):
        # Close all handlers for every logger in the system
        for logger_name, logger in logging.Logger.manager.loggerDict.items():
            if isinstance(logger, logging.Logger):  # Ensure it's a Logger instance
                handlers = logger.handlers[:]
                for handler in handlers:
                    handler.close()
                    logger.removeHandler(handler)

    @property
    def logger(self):
        return self._logger

    def setup_default_logging(self, script_name, level=logging.INFO, console_level=logging.WARNING):
        log_dir = os.path.join(self._log_dir, 'logs', 'default')
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"{script_name}_default_{self._current_date}.log")

        self._logger = logging.getLogger('')
        self._logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels

        if self._logger.hasHandlers():
            self._logger.handlers.clear()

        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(level)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(console_level)

        # Use ColorFormatter for file handler too to get consistent None/<empty> handling
        file_handler.setFormatter(ColorFormatter())

        stream_handler.setFormatter(ColorFormatter())

        self._logger.addHandler(file_handler)
        self._logger.addHandler(stream_handler)

        return self._logger

    def setup_api_failures_logging(self, script_name, level=logging.WARNING):
        log_dir = os.path.join(self._log_dir, 'logs', 'api_failures')
        os.makedirs(log_dir, exist_ok=True)
        api_log_file_path = os.path.join(log_dir, f"{script_name}_api_{self._current_date}.log")

        api_failures_logger = logging.getLogger('api_failures_logger')
        api_failures_logger.setLevel(level)
        api_failures_handler = DelayedFileHandler(api_log_file_path, mode='a', encoding='utf-8')
        api_failures_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        api_failures_handler.setFormatter(formatter)

        api_failures_logger.addHandler(api_failures_handler)
        api_failures_logger.propagate = False  # Prevent propagation to the root logger

        return api_failures_logger

    def setup_query_failures_logging(self, script_name, level=logging.WARNING):
        log_dir = os.path.join(self._log_dir, 'logs', 'query_failures')
        os.makedirs(log_dir, exist_ok=True)
        query_log_file_path = os.path.join(log_dir, f"{script_name}_query_{self._current_date}.log")

        query_failures_logger = logging.getLogger('query_failures_logger')
        query_failures_logger.setLevel(level)
        query_failures_handler = DelayedFileHandler(query_log_file_path, mode='a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        query_failures_handler.setFormatter(formatter)

        query_failures_logger.addHandler(query_failures_handler)
        query_failures_logger.propagate = False  # Prevent propagation to the root logger

        return query_failures_logger

    def setup_all_logging(self, script_name, level=logging.INFO, console_level=logging.WARNING):

        logger = self.setup_default_logging(script_name, level, console_level)
        api_failures_logger = self.setup_api_failures_logging(script_name)
        query_failures_logger = self.setup_query_failures_logging(script_name)

        return logger, api_failures_logger, query_failures_logger

    def log_exception_to_file(self, exception, function_name, json_data, **params):
        log_dir = os.path.join(self._log_dir, 'logs', 'exceptions')
        os.makedirs(log_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_exception_{function_name}.json"
        file_path = os.path.join(log_dir, filename)

        # Validate json_data and handle invalid JSON
        try:
            # If json_data is already a dictionary, it's valid JSON
            if isinstance(json_data, dict):
                parsed_json_data = json_data
                is_json_valid = True
            else:
                # Try to parse json_data to check if it's valid JSON
                parsed_json_data = json.loads(json_data) if json_data else None
                is_json_valid = True
        except (TypeError, json.JSONDecodeError):
            # If parsing fails, mark the JSON as invalid and treat json_data as a string
            parsed_json_data = json_data
            is_json_valid = False

        # Prepare the new exception details
        exception_details = {
            "function_name": function_name,
            "timestamp": datetime.now().isoformat(),
            "params": params,
            "exception": {
                "type": type(exception).__name__,
                "message": str(exception),
            },
            "json_data": parsed_json_data,
            "json_data_valid": is_json_valid
        }

        # Custom JSON serialization to handle datetime objects
        def custom_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()  # Convert datetime to ISO 8601 string
            raise TypeError(f"Type {type(obj)} not serializable")

        try:
            # Initialize a variable to hold the combined exceptions data
            combined_exceptions = []

            # Check if the file exists
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    try:
                        existing_data = json.load(file)

                        # Ensure the existing data is a list
                        if isinstance(existing_data, list):
                            combined_exceptions = existing_data
                    except json.JSONDecodeError as e:
                        print(f"Error reading JSON: {e}")
                        print("The existing file content might be corrupted. Proceeding with a new list.")

            # Check if this exception already exists
            if exception_details not in combined_exceptions:
                combined_exceptions.append(exception_details)

            # Write the combined exceptions back to the file
            with open(file_path, 'w') as file:
                json.dump(combined_exceptions, file, indent=4, default=custom_serializer)

        except Exception as e:
            print(f"Failed to write exception to file: {e}")

def main():
    # Logs will the a subdirectory of the current directory called 'logs'
    # The log file will be named 'test_script_default_<current_date>.log' in the 'logs/default' directory
    # The log file will be named 'test_script_api_<current_date>.log' in the 'logs/api_failures' directory
    # The log file will be named 'test_script_query_<current_date>.log' in the 'logs/query_failures' directory
    logging_manager = LoggingManagerSingleton(log_dir='.')

    logger = logging_manager.setup_default_logging('test_script')

    # Info will only to to the log file, not the console by default, unless the console level is set to INFO
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')

    print()

    logger = logging_manager.setup_default_logging('test_script', level=logging.DEBUG, console_level=logging.INFO)
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')

    api_logger = logging_manager.setup_api_failures_logging('test_script')

    query_logger = logging_manager.setup_query_failures_logging('test_script')
    query_logger.error('This is a query error message')
    query_logger.critical('This is a query critical message')
    query_logger.warning('This is a query warning message')

    try:

        print()
        raise ValueError("This is a test exception")

    except Exception as e:
        logging_manager.log_exception_to_file(e, 'test_function', json_data='{"key": "value"}', param1='value1', param2='value2')
        print(f"Exception logged to file: {e}")

if __name__ == '__main__':
    main()