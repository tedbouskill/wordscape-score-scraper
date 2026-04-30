from datetime import date
import cv2
import logging
import pytesseract
import os
import sys
import time

from send2trash import send2trash

# Set up root logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from cls_env_config import EnvConfigSingleton as EnvConfig
    from cls_env_tools import EnvTools
    from cls_img_tools import ImageTools
    from cls_logging_manager import LoggingManagerSingleton as LoggingManager
    from cls_project_tools import ProjectTools
    from cls_string_helpers import StringHelpers

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

    # Crop the state image which will tell us if the tournament is finished or in progress with the time left
    state_img = ImageTools.crop_image_opencv(img, 450, 680, 300, 100)
    state_txt = pytesseract.image_to_string(state_img).strip()

    # Check if the tournament is finished
    if state_txt == "FINISHED":
        # Crop the rank image & extract the rank
        rank_img = ImageTools.crop_image_opencv(img, 160, 480, 200, 200)
        # Isolate dark brown text from yellow star and light blue background
        rank_img = ImageTools.isolate_dark_text_opencv(rank_img, threshold=150)
        
        # Upscale the image to help OCR (2x or 3x size)
        rank_img = cv2.resize(rank_img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        
        # Apply slight blur to reduce noise, then sharpen
        rank_img = cv2.GaussianBlur(rank_img, (3, 3), 0)
        
        # Show the image for debugging
        #cv2.imshow("Rank Image", rank_img)
        #cv2.waitKey(0)  # Wait for a key press to close the window
        #cv2.destroyAllWindows()  # Close all OpenCV windows
        
        # Try with custom Tesseract config for better number recognition
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789#'
        rank_txt = pytesseract.image_to_string(rank_img, config=custom_config).strip()
        logging.info(f"Team rank: {rank_txt}")

    player_results = []
    unmatched_texts = []
    score_results = []

    # Crop the players image and extract the player names and scores
    players_img = ImageTools.crop_image_opencv(img, 300, 1050, 900, new_height - 1050)
    players_img = ImageTools.convert_non_white_to_black_opencv(players_img, 200)
    results = reader.readtext(players_img)
    for box, text, confidence in results:
        player_id = db_repository.get_player_id(text)
        if box[0][0] < 50:
            if player_id is not None:
                player_results.append((box, text, confidence))
            else:
                unmatched_texts.append((text, confidence))
            continue

        if box[0][0] > 650 and StringHelpers.is_all_numeric(text):
            score_results.append((box, text, confidence))

    logging.debug("Length of player results: ", len(player_results))
    logging.debug("Length of score results: ", len(score_results))

    # Match numeric values with text values based on y-coordinate
    matches = []
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
            player_id = db_repository.get_player_id(text)
            if player_id:
                matches.append((text, 0))
            else:
                unmatched_texts.append((text, text_confidence))

    # Track unmatched scores
    for num_box, num_text, num_confidence in score_results:
        num_y = num_box[0][1]  # y-coordinate of the top-left corner of the numeric box
        matched = False
        for text_box, text, text_confidence in player_results:
            text_y = text_box[0][1]  # y-coordinate of the top-left corner of the text box
            if 0 <= abs(num_y - text_y) < 100:
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
        logging.debug(f"Text: {text}, Confidence: {confidence}")

    # Print unmatched score results
    logging.debug("Unmatched Scores:")
    for score, confidence in unmatched_scores:
        logging.debug(f"Score: {score}, Confidence: {confidence}")

    return matches, unmatched_texts, unmatched_scores, rank_txt

def process_player_matches(matches, weekend_date, friday_date):

    for player_tag, score in matches:
        logging.info(f"Player: {player_tag}, Score: {score}")

    return

def process_img_files(images):

    weekend_dates = set()

    img_files_processed = 0

    # Get weekend dates from the filenames
    for image_file in images:

        logging.debug(f"Processing {image_file} . . .")

        date_str, file_date, series_str = ProjectTools.extract_date_time_from_filename(image_file)

        logging.debug(f"Date: {date_str}, FileStr: {file_date}, Series: {series_str}")

        # Calculate weekend and Friday dates
        sunday_date, friday_date = ProjectTools.get_weekend_dates(date_str)

        weekend_dates.add((sunday_date, file_date, friday_date, date_str))

    # for image_file in images:

    # Process the images for each sunday weekend date
    for sunday_date, files_date, friday_date, date_str in sorted(weekend_dates): # Sort by weekend date
        logging.info(f"Processing {sunday_date}...")

        # Get the image files for the weekend date
        image_files_for_weekend = [img for img in images if files_date in img]

        for image_file in sorted(image_files_for_weekend):
            image_file_name = os.path.basename(image_file)

            logging.info(f"\tProcessing {image_file_name} . . .")

            # Process the image
            matches, unmatched_text, unmatched_scores, rank_txt = process_image(image_file)

            if rank_txt is not None:
                print(f"Team Rank for {sunday_date}: {rank_txt}")

            #remaining_unmatched_text = []
            #for text, confidence in unmatched_text:
            #    player_id = db_repository.get_player_id(text)
            #    if player_id:
            #        logging.info(f"Player ID found in unmatched text: {text}, ID: {player_id}, assigning score: 0")
            #        matches.append((text, 0))
            #    else:
            #        logging.warning(f"Unmatched Text: {text}, Confidence: {confidence}")
            #        remaining_unmatched_text.append((text, confidence))

            # Update unmatched_text with the remaining unmatched items
            #unmatched_text = remaining_unmatched_text

            # Insert the player scores including creating new players and inserting friday as the join date
            process_player_matches(matches, sunday_date, friday_date)

            # This will skip deleting the file
            if (len(unmatched_text) > 0):
                logging.error("Unmatched Texts:")
                for text, confidence in unmatched_text:
                    logging.warning(f"Couldn't match this text: {text}, Confidence: {confidence}")
                continue

            # This will skip deleting the file
            if (len(unmatched_scores) > 0):
                logging.error("Unmatched Scores:")
                for score, confidence in unmatched_scores:
                    logging.warning(f"Score: {score}, Confidence: {confidence}")
                continue

            img_files_processed += 1

        # for img_file in sorted(img_files_for_weekend):

    # for sunday_date, friday_date, files_date in sorted(weekend_dates): # Sort by weekend date

    return

def main():
    global process_start_time, logger, db_repository

    env_config = EnvConfig()

    repo_root = EnvTools.find_repo_root()

    db_path_config = env_config.merged_config['constants']['db_path']
    db_path = db_path_config.replace("{repo_root}", str(repo_root))

    images_path = os.path.join(repo_root, "images/png_samples/weekend_scores")

    logging_manager = None

    try:
        logging_manager = LoggingManager(script_dir)
    except Exception as e:
        logging.exception(f"Error initializing LoggingManager: {e}")
        sys.exit(1)

    try:
        logger = logging_manager.setup_default_logging(script_name, console_level=logging.DEBUG)

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