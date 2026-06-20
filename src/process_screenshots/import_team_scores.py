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

PLAYER_TAG_IGNORE_LIST = [
    "DestroyaDrew",
    "Claflinxs",
    "Suriel",
    "FleurDeLys",
    "jeda",
    "VZn",
    "Disqualified",
    "I_give_up",
    "fin",
    "itme"
]

# Common OCR misreadings for player tags
PLAYER_TAG_CORRECTIONS = {
    'cAest': 'c4est',
    'Jay]': 'JayJ',
    'Jay)': 'JayJ',
    # Add more corrections here as needed
    # Format: 'incorrect_reading': 'correct_tag'
}

# Normalized lookup (trim + lowercase) to catch OCR case/spacing variations.
PLAYER_TAG_CORRECTIONS_NORMALIZED = {
    key.strip().lower(): value for key, value in PLAYER_TAG_CORRECTIONS.items()
}

# Set for fast exact (case-sensitive) membership checks.
PLAYER_TAG_IGNORE_SET = {tag.strip() for tag in PLAYER_TAG_IGNORE_LIST}

def correct_player_tag(tag: str) -> str:
    """
    Correct common OCR misreadings of player tags.
    
    Args:
        tag: The OCR-detected player tag
        
    Returns:
        The corrected player tag if a correction exists, otherwise the original tag
    """
    if tag is None:
        return ""

    cleaned_tag = str(tag).strip()
    if not cleaned_tag:
        return cleaned_tag

    # Preserve exact-match behavior first.
    if cleaned_tag in PLAYER_TAG_CORRECTIONS:
        return PLAYER_TAG_CORRECTIONS[cleaned_tag]

    # Fallback to normalized match for case/spacing OCR variance.
    normalized_tag = cleaned_tag.lower()
    return PLAYER_TAG_CORRECTIONS_NORMALIZED.get(normalized_tag, cleaned_tag)

def process_image(file_name: str) -> tuple:
    rank_txt = None

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
        rank_results = reader.readtext(rank_img, detail=0, paragraph=False)
        
        # Extract the rank text from the list returned by easyocr
        if rank_results and len(rank_results) > 0:
            rank_txt = rank_results[0]
            logging.info(f"Team rank: {rank_txt}")
            
            # Verify the team rank was extracted correctly
            # The rank text should be a hash followed by numbers, e.g., "#1"
            if not (rank_txt.startswith('#') and rank_txt[1:].isdigit()):
                logging.warning(f"Extracted rank text '{rank_txt}' does not match expected format.")
                rank_txt = None
        else:
            logging.warning("No rank text extracted from image.")
            rank_txt = None

    player_results = []
    unmatched_texts = []
    score_results = []
    ignored_player_boxes = []

    # Crop the players image and extract the player names and scores
    players_img = ImageTools.crop_image_opencv(img, 300, 1030, 900, new_height - 1030)
    players_img = ImageTools.convert_non_white_to_black_opencv(players_img, 200)
    results = reader.readtext(players_img)
    for box, text, confidence in results:
        # Apply OCR correction for common misreadings
        corrected_text = correct_player_tag(text)
        if corrected_text != text:
            logging.debug(f"Corrected OCR: '{text}' -> '{corrected_text}'")

        # Skip tags on the ignore list entirely (not an error, just not our players).
        if corrected_text.strip() in PLAYER_TAG_IGNORE_SET:
            logging.debug(f"Ignoring tag on ignore list: '{corrected_text}'")
            ignored_player_boxes.append(box)
            continue

        player_id = db_repository.get_player_id(corrected_text)
        if box[0][0] < 50:
            if player_id is not None:
                player_results.append((box, corrected_text, confidence))
            else:
                unmatched_texts.append((corrected_text, confidence))
            continue

        if box[0][0] > 650 and StringHelpers.is_all_numeric(text):
            score_results.append((box, text, confidence))

    logging.debug(f"Length of player results: {len(player_results)}")
    logging.debug(f"Length of score results: {len(score_results)}")

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
            # text is already corrected from earlier processing
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
            for ignored_box in ignored_player_boxes:
                ignored_y = ignored_box[0][1]
                if 0 <= abs(num_y - ignored_y) < 100:
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
    """
    Process matched player tags and scores.

    Returns True if all matched player scores were successfully recorded (and players are active),
    otherwise returns False so the caller can avoid deleting the source image.
    """
    all_ok = True

    for player_tag, score in matches:
        logging.info(f"Player: {player_tag}, Score: {score}")

        # Ensure the player exists; create if missing (this also marks new players active)
        player_id = db_repository.get_player_id(player_tag)
        if not player_id:
            logging.info(f"Player '{player_tag}' not found; creating new player with start date {friday_date}")
            player_id = db_repository.get_player_id_create_if_new(player_tag, friday_date)

        # Check if player is active
        is_active = db_repository.is_player_active(player_id)
        
        # If not active, check if they're on_team; if so, activate them
        if not is_active:
            is_on_team = db_repository.is_player_on_team(player_id)
            if is_on_team:
                logging.info(f"Player '{player_tag}' (id={player_id}) is on_team but not active; activating")
                db_repository.set_player_active(player_id)
                is_active = True
        
        # If still not active, skip this score
        if not is_active:
            logging.error(f"Player '{player_tag}' (id={player_id}) is not active and not on_team; skipping score insertion")
            all_ok = False
            continue

        try:
            db_repository.upsert_weekend_player_score(weekend_date, player_id, score)
        except Exception as e:
            logging.exception(f"Failed to upsert score for player '{player_tag}' (id={player_id}): {e}")
            all_ok = False

    return all_ok

def process_img_files(images):

    weekend_dates = set()

    img_files_processed = 0

    # Get weekend dates from the filenames
    print("Preprocessing images to determine weekend dates...")
    for image_file in images:

        logging.debug(f"Processing {image_file} . . .")

        date_str, file_date, series_str = ProjectTools.extract_date_time_from_filename(image_file)

        logging.debug(f"Date: {date_str}, FileStr: {file_date}, Series: {series_str}")

        # Calculate weekend and Friday dates
        sunday_date, friday_date = ProjectTools.get_weekend_dates(date_str)

        weekend_dates.add((sunday_date, file_date, friday_date, date_str))

    # for image_file in images:

    # Process the images for each sunday weekend date
    print("Processing images for each weekend date...")
    for sunday_date, files_date, friday_date, date_str in sorted(weekend_dates): # Sort by weekend date
        print(f"\nProcessing {sunday_date}...")

        # Get the image files for the weekend date
        image_files_for_weekend = [img for img in images if files_date in img]

        # Reset scores for the tournament
        db_repository.reset_scores_for_tournament(sunday_date)

        for image_file in sorted(image_files_for_weekend):
            image_file_name = os.path.basename(image_file)

            logging.info(f"\tProcessing {image_file_name} for {sunday_date} . . .")

            # Process the image
            matches, unmatched_text, unmatched_scores, rank_txt = process_image(image_file)

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
            # The team tournament rank is not being scanned correctly at this time
            if rank_txt is not None:
                db_repository.upsert_weekend_team_rank(sunday_date, rank_txt)

            # Insert the player scores including creating new players and inserting friday as the join date
            success = process_player_matches(matches, sunday_date, friday_date)

            # If any player score was not recorded (for example player not active), skip deleting the file
            if not success:
                logging.error("One or more player scores were not recorded (inactive or error); skipping deletion of image")
                continue

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

            # Delete the file if it was processed successfully
            logging.debug(f"Deleting {image_file}")
            send2trash(image_file)

            img_files_processed += 1

        # for img_file in sorted(img_files_for_weekend):

        # Set scores to 0 for missing players
        db_repository.set_missing_scores_to_zero_for_weekend(sunday_date)

        # Set the weekend date ranks
        db_repository.update_ranks_for_weekend_date(sunday_date)
        
        # Update team score for the weekend date
        db_repository.upsert_weekend_team_score_for_date(sunday_date)

    # for sunday_date, friday_date, files_date in sorted(weekend_dates): # Sort by weekend date

    return

def main():
    global process_start_time, logger, db_repository

    env_config = EnvConfig()

    repo_root = EnvTools.find_repo_root()

    db_path_config = env_config.merged_config['constants']['db_path']
    db_path = db_path_config.replace("{repo_root}", str(repo_root))

    images_config = env_config.merged_config['constants']['tournament_images_folder']
    images_path = images_config.replace("{repo_root}", str(repo_root))

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

        print(f"\nProgram execution time: {duration:.2f} seconds")

        if img_files_processed is not None and img_files_processed > 0:
            print(f"Total files processed: {img_files_processed} at a rate of {duration / img_files_processed:.2f} seconds per file")

    print("Script has finished.\n") # This is the last line of the script

if __name__ == "__main__":
    global script_name, script_directory

    # Get the script name without the extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    #script_folder = os.getcwd()

    main()