import fnmatch
import logging
import os
import re

from pathlib import Path
from datetime import datetime, timedelta

class ProjectTools:
    @staticmethod
    def get_img_files(directory: str, pattern='.png', recursive: bool = False) -> list:

        path = Path(directory)
        if (not path.exists()):
            logging.critical(f"Directory {directory} does not exist")
            return []
        
        if recursive:
            files = [str(file) for file in path.rglob('*') if fnmatch.fnmatch(file.suffix.lower(), pattern.lower())]
        else:
            files = [str(file) for file in path.glob('*') if fnmatch.fnmatch(file.suffix.lower(), pattern.lower())]

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
    def extract_date_time_from_filename(file_path: str) -> tuple:
        """
        Extract the date from the screenshot file's metadata or filename.
        Assumes the file is named with a yyyy-mm-dd prefix.
        """
        try:
            filename = os.path.basename(file_path)
            matches = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})_(\d{2})", filename)
            date_str = matches.group(1)  # Extract the yyyy-mm-dd prefix
            time_str = matches.group(2)  # Extract the time
            series_str = matches.group(3)  # Extract the series number
            logging.debug(f"Date: {date_str}, Time: {time_str}, Series: {series_str}")
        except Exception as e:
            logging.error(f"Error extracting date and series from filename: {e}")

        return date_str, date_str+"_"+time_str, int(series_str)

    @staticmethod
    def get_weekend_dates(file_date_str: str) -> tuple:
        """
        Calculate the weekend date (Sunday) and the Friday date for a given tournament date.
        Tournament runs Friday-Sunday. Returns the Sunday of the tournament weekend:
        - If screenshot is Fri-Sun: returns the upcoming/current Sunday
        - If screenshot is Mon-Thu: returns the previous Sunday
        """
        tournament_date = datetime.strptime(file_date_str, "%Y-%m-%d")
        weekday = tournament_date.weekday()  # Mon=0, Tue=1, ..., Sun=6
        
        if weekday <= 3:  # Monday (0) through Thursday (3) - tournament already finished
            # Go back to the previous Sunday
            days_back = (weekday + 1) % 7
            sunday_date = tournament_date - timedelta(days=days_back)
        else:  # Friday (4), Saturday (5), Sunday (6) - tournament in progress or just ending
            # Go forward to the upcoming Sunday (or stay on Sunday)
            days_forward = 6 - weekday
            sunday_date = tournament_date + timedelta(days=days_forward)
        
        friday_date = sunday_date - timedelta(days=2)

        return sunday_date.strftime("%Y-%m-%d"), friday_date.strftime("%Y-%m-%d")

    @staticmethod
    def next_sunday(date):
        """
        Calculate the next Sunday following a given date.
        If the date is already a Sunday, it returns the same date.
        """
        days_ahead = 6 - date.weekday()  # Sunday is 6
        if days_ahead < 0:  # Target day already passed in the current week
            days_ahead += 7
        next_sunday_date = date + timedelta(days=days_ahead)
        return next_sunday_date.strftime('%Y-%m-%d')