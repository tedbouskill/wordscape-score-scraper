import fnmatch
import logging
import os
import re

from pathlib import Path
from datetime import datetime, timedelta

class ProjectTools:
    @staticmethod
    def get_img_files(directory: str, pattern='.png') -> list:

        path = Path(directory)
        if (not path.exists()):
            logging.critical(f"Directory {directory} does not exist")
            return []
        files = [str(file) for file in path.rglob('*') if fnmatch.fnmatch(file.suffix.lower(), pattern.lower())]

        return files

    @staticmethod
    def extract_date_from_filename(file_path: str) -> tuple:
        """
        Extract the date from the screenshot file's metadata or filename.
        Assumes the file is named with a yyyy-mm-dd prefix.
        """
        try:
            filename = os.path.basename(file_path)
            matches = re.match(r"(\d{4}-\d{2}-\d{2})-(\d{2})", filename)
            date_str = matches.group(1)  # Extract the yyyy-mm-dd prefix
            series_str = matches.group(2)  # Extract the series number
            logging.debug(f"Date: {date_str}, Series: {series_str}")
        except Exception as e:
            logging.error(f"Error extracting date and series from filename: {e}")

        return date_str, int(series_str)

    @staticmethod
    def get_weekend_dates(file_date_str: str) -> tuple:
        """
        Calculate the weekend date (Sunday) and the Friday date for a given tournament date.
        """
        tournament_date = datetime.strptime(file_date_str, "%Y-%m-%d")
        sunday_date = tournament_date + timedelta(days=(6 - tournament_date.weekday()))
        friday_date = sunday_date - timedelta(days=2)

        return sunday_date.strftime("%Y-%m-%d"), friday_date.strftime("%Y-%m-%d")