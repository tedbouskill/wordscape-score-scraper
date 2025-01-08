import fnmatch
import json
import logging
import pytesseract
import os
import re
import sqlite3
import sys
import time

from calendar import week
from numpy import insert
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageOps
from requests import get
from sympy import im

# Set up root logger configuration
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from cls_env_config import EnvConfigSingleton as EnvConfig
    from cls_env_tools import EnvTools
    from cls_img_tools import ImageTools
    from cls_logging_manager import LoggingManager
    from cls_string_helpers import StringHelpers
except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)

import easyocr

# Initialize EasyOCR
reader = easyocr.Reader(['en'])

def get_img_files(directory: str, pattern='.png') -> list:

    path = Path(directory)
    if (not path.exists()):
        logging.critical(f"Directory {directory} does not exist")
        return []
    files = [str(file) for file in path.rglob('*') if fnmatch.fnmatch(file.suffix.lower(), pattern.lower())]

    return files

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
        logger.debug(f"Date: {date_str}, Series: {series_str}")
    except Exception as e:
        logger.error(f"Error extracting date and series from filename: {e}")

    return date_str, int(series_str)

def get_weekend_dates(file_date_str: str) -> tuple:
    """
    Calculate the weekend date (Sunday) and the Friday date for a given tournament date.
    """
    tournament_date = datetime.strptime(file_date_str, "%Y-%m-%d")
    sunday_date = tournament_date + timedelta(days=(6 - tournament_date.weekday()))
    friday_date = sunday_date - timedelta(days=2)

    return sunday_date.strftime("%Y-%m-%d"), friday_date.strftime("%Y-%m-%d")

def reset_scores_for_tournament(connection, weekend_date):
    """
    Reset all player scores for a given weekend date to 0.
    """
    cursor = connection.cursor()
    cursor.execute("UPDATE tournament_results SET score = 0 WHERE weekend_date = ? AND score IS NULL", (weekend_date,))
    connection.commit()

    return

def process_image(file_name: str) -> tuple:

    img, new_height = ImageTools.resize_image_opencv(file_name, new_width=1200)

    # Crop the state image which will tell us if the tournament is finished or in progress with the time left
    state_img = ImageTools.crop_image_opencv(img, 450, 680, 300, 100)

    state_txt = pytesseract.image_to_string(state_img).strip()

    # Check if the tournament is finished
    if state_txt == "FINISHED":
        # Crop the rank image & extract the rank
        rank_img = ImageTools.crop_image_opencv(img, 100, 540, 200, 110)
        rank_img = ImageTools.convert_non_white_to_black_opencv(rank_img)
        rank_txt = pytesseract.image_to_string(rank_img).strip()
        logging.info(f"Team rank: {rank_txt}")

    player_results = []
    score_results = []

    # Crop the players image and extract the player names and scores
    players_img = ImageTools.crop_image_opencv(img, 300, 1050, 900, new_height - 1050)
    players_img = ImageTools.convert_non_white_to_black_opencv(players_img, 200)
    results = reader.readtext(players_img)
    for box, text, confidence in results:
        if box[0][0] < 50:
            player_results.append((box, text, confidence))

        if box[0][0] > 650 and StringHelpers.is_all_numeric(text):
            score_results.append((box, text, confidence))

    logging.debug("Length of player results: ", len(player_results))
    logging.debug("Length of score results: ", len(score_results))

    # Match numeric values with text values based on y-coordinate
    matches = []
    unmatched_texts = []
    unmatched_scores = []
    for text_box, text, text_confidence in player_results:
        text_y = text_box[0][1]  # y-coordinate of the top-left corner of the text box
        matched = False
        for num_box, num_text, num_confidence in score_results:
            num_y = num_box[0][1]  # y-coordinate of the top-left corner of the numeric box
            if 0 < abs(num_y - text_y) < 66:
                matches.append((text, num_text))
                matched = True
                break
        if not matched:
            unmatched_texts.append((text, text_confidence))

    # Track unmatched scores
    for num_box, num_text, num_confidence in score_results:
        num_y = num_box[0][1]  # y-coordinate of the top-left corner of the numeric box
        matched = False
        for text_box, text, text_confidence in player_results:
            text_y = text_box[0][1]  # y-coordinate of the top-left corner of the text box
            if 0 < abs(num_y - text_y) < 100:
                matched = True
                break
        if not matched:
            unmatched_scores.append((num_text, num_confidence))

    # Print matched results
    logging.debug("Matched Results:")
    for text, num in matches:
        logging.debug(f"Text: {text}, Numeric: {num}")

    # Print unmatched text results
    logging.debug("Unmatched Texts:")
    for text, confidence in unmatched_texts:
        logging.warning(f"Text: {text}, Confidence: {confidence}")

    # Print unmatched score results
    logging.debug("Unmatched Scores:")
    for score, confidence in unmatched_scores:
        logging.warning(f"Score: {score}, Confidence: {confidence}")

    return matches, unmatched_texts, unmatched_scores, rank_txt

def update_player_start_date(connection, player_id, friday_date):
    """
    Update the player's start_date in the players table if it's earlier than the existing start_date.
    """
    cursor = connection.cursor()
    cursor.execute("SELECT start_date FROM players WHERE player_id = ?", (player_id,))
    row = cursor.fetchone()
    if row:
        current_start_date = row[0]
        if current_start_date is None or friday_date < current_start_date:
            cursor.execute("UPDATE players SET start_date = ? WHERE player_id = ?", (friday_date, player_id))
    connection.commit()

    return

def insert_weekend_player_score(connection, weekend_date, player_id, score):
    """
    Insert extracted data into SQLite database.
    """
    cursor = connection.cursor()
    insert_query = """
        INSERT OR IGNORE INTO tournament_results (weekend_date, player_id, score)
        VALUES (?, ?, ?)
        """
    cursor.execute(insert_query, (weekend_date, player_id, score))
    connection.commit()

    return

def save_rankings_to_json(rankings, output_file):
    """
    Save extracted rankings to a JSON file grouped by tournament date.
    """
    data = {}

    for entry in rankings:
        weekend_date = entry["weekend_date"]
        if weekend_date not in data:
            data[weekend_date] = []
        data[weekend_date].append({
            "rank": entry["rank"],
            "player_id": entry["player_id"],
            "score": entry["score"]
        })

    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)

    return

def get_player_id(connection, player_tag):
    cursor = connection.cursor()
    cursor.execute("SELECT player_id FROM players WHERE player_tag = ?", (player_tag,))
    row = cursor.fetchone()
    if row:
        player_id = row[0]
    else:
        player_id = None

    return player_id

def get_player_id_create_if_new(connection, player_tag, friday_date):

    player_id = get_player_id(connection, player_tag)
    if player_id:
        return player_id

    cursor = connection.cursor()
    cursor.execute("INSERT INTO players (player_tag, start_date) VALUES (?, ?)", (player_tag, friday_date,))
    player_id = cursor.lastrowid
    connection.commit()

    return player_id

def process_player_matches(connection, matches, weekend_date, friday_date):

    for player_tag, score in matches:
        logging.info(f"Player: {player_tag}, Score: {score}")

        player_id = get_player_id_create_if_new(connection, player_tag, friday_date)

        insert_weekend_player_score(connection, weekend_date, player_id, score)

    return

def update_ranks_for_weekend_date(connection, weekend_date):
    cursor = connection.cursor()

    # SQL query to update ranks for the specific weekend_date
    sql = """
    WITH ranked_results AS (
        SELECT
            player_id,
            RANK() OVER (PARTITION BY weekend_date ORDER BY score DESC) AS calculated_rank
        FROM
            tournament_results
        WHERE
            weekend_date = ?
    )
    UPDATE tournament_results
    SET rank = (
        SELECT calculated_rank
        FROM ranked_results
        WHERE ranked_results.player_id = tournament_results.player_id
    )
    WHERE weekend_date = ?;
    """

    # Execute the query with the specified date
    cursor.execute(sql, (weekend_date, weekend_date))
    connection.commit()

def process_img_files(db_path, images, output_json):
    connection = sqlite3.connect(db_path)

    weekend_dates = set()

    img_files_processed = 0

    # Get weekend dates from the filenames
    for image_file in images:
        if "processed_" in image_file:
            continue

        date_str, series_str = extract_date_from_filename(image_file)

        # Calculate weekend and Friday dates
        dates = get_weekend_dates(date_str)

        weekend_dates.add(dates + (date_str,))

    # for image_file in images:

    # Process the images for each sunday weekend date
    for sunday_date, friday_date, files_date in sorted(weekend_dates): # Sort by weekend date
        logging.info(f"Processing {sunday_date}...")

        # Get the image files for the weekend date
        image_files_for_weekend = [img for img in images if files_date in img]

        # Reset scores for the tournament
        reset_scores_for_tournament(connection, sunday_date)

        for image_file in sorted(image_files_for_weekend):
            image_file_name = os.path.basename(image_file)

            logging.info(f"\tProcessing {image_file_name} . . .")

            # Process the image
            matches, unmatched_text, unmatched_scores, rank_txt = process_image(image_file)

            # Insert the player scores including creating new players and inserting friday as the join date
            process_player_matches(connection, matches, sunday_date, friday_date)

            player_found_without_score = False
            for text, confidence in unmatched_text:
                logging.warning(f"Unmatched Text: {text}, Confidence: {confidence}")
                player_id = get_player_id(connection, text)
                if player_id:
                    logging.warning(f"Player found without score: {text}")
                    player_found_without_score = True

            # This will skip deleting the file.
            if player_found_without_score:
                logging.warning("Player(s) found without score")
                for player_tag, score in matches:
                    logging.warning(f"Player: {player_tag}, Score: {score}")
                continue

            # This will skip deleting the score
            if (len(unmatched_scores) > 0):
                logging.error("Unmatched Scores:")
                for score, confidence in unmatched_scores:
                    logging.warning(f"Score: {score}, Confidence: {confidence}")
                continue

            # Delete the file if it was processed successfully
            logging.debug(f"Deleting {image_file}")
            os.remove(image_file)
            #os.rename(image_file, os.path.join(os.path.dirname(image_file), f"processed_{os.path.basename(image_file)}"))

            img_files_processed += 1

        # for img_file in sorted(img_files_for_weekend):

        # Set the weekend date ranks
        update_ranks_for_weekend_date(connection, sunday_date)

    # for sunday_date, friday_date, files_date in sorted(weekend_dates): # Sort by weekend date

    connection.close()

def main():
    global process_start_time, logger

    env_config = EnvConfig()

    repo_root = EnvTools.find_repo_root()

    db_path_config = env_config.merged_config['constants']['db_path']
    db_path = db_path_config.replace("{repo_root}", str(repo_root))

    # Get the script name without the extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    #script_folder = os.getcwd()
    logging.debug(f"Script Folder: {script_dir}")
    logging.debug(f"Script Name: {script_name}")

    images_config = env_config.merged_config['constants']['images_folder']
    images_path = images_config.replace("{script_dir}", script_dir)

    output_json_config = os.path.join(repo_root, env_config.merged_config['constants']['output_json'])
    output_json_file = output_json_config.replace("{script_dir}", script_dir)

    logging_manager = None

    try:
        logging_manager = LoggingManager(script_dir)
    except Exception as e:
        logging.exception(f"Error initializing LoggingManager: {e}")
        sys.exit(1)

    try:
        logger = logging_manager.setup_default_logging(script_name, console_level=logging.INFO)

        logger.debug(f"Database Path: {db_path}")
        logger.debug(f"Images Folder: {images_path}")
        logger.debug(f"Output JSON: {output_json_file}")

        process_start_time = time.time()  # Capture the start time

        img_files_processed = 0
        img_files_with_errors = 0

        img_files = get_img_files(images_path)
        logger.info(f"Processing {len(img_files)} rows . . .")

        results = process_img_files(db_path, img_files, output_json_file)

    except Exception as e:
        logging.exception(f"Uncaught exception in Main(): {e}")
        logger.exception(f"Uncaught exception in Main(): {e}")
    finally:
        end_time = time.time()

        duration = end_time - process_start_time

        logger.info(f"Program execution time: {duration:.2f} seconds")

        if img_files_processed is not None and img_files_processed > 0:
            logger.info(f"Total files processed: {img_files_processed} at a rate of {duration / img_files_processed:.2f} seconds per file")

    print("Script has finished.\n") # This is the last line of the script

if __name__ == "__main__":
    print("Starting import_scores.py...")
    main()