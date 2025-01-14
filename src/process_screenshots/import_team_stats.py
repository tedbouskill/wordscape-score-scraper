import logging
import os
import sys
import time

from calendar import week
from numpy import insert
from datetime import datetime
from send2trash import send2trash

# Set up root logger configuration
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from cls_env_config import EnvConfigSingleton as EnvConfig
    from cls_env_tools import EnvTools
    from cls_img_tools import ImageTools
    from cls_logging_manager import LoggingManager
    from cls_project_tools import ProjectTools

    from cls_db_tools import DbRepositorySingleton
except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)

import easyocr

# Initialize EasyOCR
reader = easyocr.Reader(['en'])

def process_image(file_name: str) -> tuple:
    rank_txt = None

    img, new_height = ImageTools.resize_image_opencv(file_name, new_width=1200)

    offset_height = 600
    players_img = ImageTools.crop_image_opencv(img, 280, offset_height, 440, new_height - offset_height) # Only player tags
    players_img = ImageTools.convert_non_white_to_black_opencv(players_img, 225)
    #display_image_opencv(players_img, title="Players Image")

    player_results = []
    results = reader.readtext(players_img, mag_ratio=2.0)
    for box, text, confidence in results:
        if box[0][0] < 50:
            player_results.append((box, text, confidence))
        #print(f"Player: {player[1]} - Box y {player[0][0][1]}")

    helps_img = ImageTools.crop_image_opencv(img, 740, offset_height, 150, new_height - offset_height)
    helps_img = ImageTools.convert_non_white_to_black_opencv(helps_img, 245)
    #display_image_opencv(helps_img, title="Helps Image")

    player_helps = []
    results = reader.readtext(helps_img, mag_ratio=2.0, allowlist="0123456789")
    for box, text, confidence in results:
        player_helps.append((box, text, confidence))
        #print(f"Helps: {help[1]} - Box y {help[0][0][1]}")

    player_stars = []
    stars_img = ImageTools.crop_image_opencv(img, 890, offset_height, 250, new_height - offset_height)
    stars_img = ImageTools.convert_non_white_to_black_opencv(stars_img, 245)
    #display_image_opencv(stars_img, title="Stars Image")
    results = reader.readtext(stars_img, mag_ratio=2.0, allowlist="0123456789,")
    for box, text, confidence in results:
        player_stars.append((box, text, confidence))
        #print(f"Stars: {text} - Box y {box[0][1]}")

    logging.debug(f"Length of player results: {len(player_results)}")
    logging.debug(f"Length of player helps: {len(player_helps)}")
    logging.debug(f"Length of player stars: {len(results)}")

    # Match numeric values with text values based on y-coordinate
    matches = []
    unmatched = []
    for player_text_box, player_text, player_text_confidence in player_results:
        player_y = player_text_box[0][1]  # y-coordinate of the top-left corner of the text box
        helps_stars = (None, None)
        for help_text_box, help_text, help_text_confidence in player_helps:
            help_y = help_text_box[0][1]  # y-coordinate of the top-left corner of the numeric box
            if -40 <= (player_y - help_y) <= 25:
                helps_stars = (help_text, None)
                break;

        # if we didn't find a Helps match it's because it was 0 which EasyOCR is not recognizing
        if helps_stars[0] is None:
            helps_stars = (0, None)

        for star_text_box, star_text, star_text_confidence in results:
            star_y = star_text_box[0][1]
            if -40 <= (player_y - star_y) <= 25:
                helps_stars = (helps_stars[0], star_text)
                break

        if helps_stars[1] is None:
            unmatched.append((player_text, helps_stars))
        else:
            matches.append((player_text, helps_stars))

    return matches, unmatched

def process_img_files(images):

    file_groups = set()

    # Get weekend dates from the filenames
    for image_file in images:

        logging.debug(f"Processing {image_file} . . .")

        date_str, file_str, series_str = ProjectTools.extract_date_time_from_filename(image_file)

        logging.debug(f"Date: {date_str}, FileStr: {file_str}, Series: {series_str}")

        file_groups.add((file_str, date_str))

    # for image_file in images:

    for file_str, date_str in sorted(file_groups):
        logging.debug(f"File: {file_str}, Date: {date_str}")

        print(f"Processing {file_str} . . .")

        sunday_date = ProjectTools.next_sunday(datetime.strptime(date_str, "%Y-%m-%d"))

        # Get the image files for the weekend date
        image_files_group = [img for img in images if file_str in img]

        player_metrics = {}
        unmatched_metrics = {}
        delete_files = []

        for image_file in sorted(image_files_group):
            print(f"Processing {image_file} . . .")

            matches, unmatched = process_image(image_file)

            # if we have matches and no unmatched, then we can delete the image file
            if (len(matches) > 0) and (len(unmatched) == 0):
                delete_files.append(image_file)

            for match in matches:
                player_metrics[match[0]] = match

            for unmatch in unmatched:
                unmatched_metrics[unmatch[0]] = unmatch

        # Get the players from the database
        player_rows = db_repository.get_players()

        # Create a dictionary with player_tag as the key
        players_dict = {player[1]: player for player in player_rows}  # Assuming player_tag is at index 1

        missing_player_stats = set()

        for player_tag, player in players_dict.items():
            player_id = player[0]  # Access player_id using index 0
            on_team = player[2]  # Access on_team using index 2
            leave_date = player[4]  # Access leave_date using index 4

            # If the player is not on the team, skip them
            if on_team == 0:
                continue

            # The player is on the time, find their metrics from the OCR results
            player_metric = player_metrics.get(player_tag)
            if player_metric:
                helps = player_metric[1][0]
                stars = int(player_metric[1][1].replace(",", ""))

                db_repository.upsert_weekly_player_stats(sunday_date, player_id, helps, stars)
            else:
                missing_player_stats.add(player)

        # for player, metrics in sorted(player_metrics):

        # If there are missing players from the OCR results, they are not on the team
        for missing_player in missing_player_stats:
            player_tag = missing_player['player_tag']
            unmatched = unmatched_metrics.get(player_tag)
            if unmatched:
                logging.warning(f"Player: {player_tag}, Unmatched: {unmatched}")
            else:
                logging.warning(f"Player: {player_tag}, No OCR results")

        for delete_file in delete_files:
            send2trash(delete_file)

    # for sunday_date, friday_date, files_date in sorted(weekend_dates): # Sort by weekend date

    return

def main():
    global process_start_time, logger, db_repository

    env_config = EnvConfig()

    repo_root = EnvTools.find_repo_root()

    db_path_config = env_config.merged_config['constants']['db_path']
    db_path = db_path_config.replace("{repo_root}", str(repo_root))

    images_config = env_config.merged_config['constants']['team_images_folder']
    images_path = images_config.replace("{script_dir}", script_dir)
    print(f"Images Path: {images_path}")

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

        process_start_time = time.time()  # Capture the start time

        img_files_processed = 0
        img_files_with_errors = 0

        db_repository = DbRepositorySingleton(db_path)

        img_files = ProjectTools.get_img_files(images_path)
        logger.info(f"Processing {len(img_files)} rows . . .")

        results = process_img_files(img_files)

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
    global script_name, script_directory

    # Get the script name without the extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    #script_folder = os.getcwd()

    main()