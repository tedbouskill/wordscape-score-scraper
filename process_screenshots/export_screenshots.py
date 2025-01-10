import os
import time
from datetime import datetime, timedelta
from osxphotos import PhotosDB

def get_previous_sunday(date):
    """
    Calculate the Sunday preceding or equal to the given date.
    """
    return date - timedelta(days=date.weekday() + 1 if date.weekday() != 6 else 0)

def export_png_files_from_album(album_name, subfolder_name):
    # Get the folder where the script is located
    script_folder = os.path.dirname(os.path.abspath(__file__))

    # Define the destination folder as the specified subfolder
    destination_folder = os.path.join(script_folder, subfolder_name)
    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    photosdb = None

    try:

        # Initialize the PhotosDB
        photosdb = PhotosDB()

        # Query photos with specific criteria
        album_photos = photosdb.photos(albums=[album_name])

        if not album_photos:
            print(f"Album '{album_name}' not found or no photos in the album.")
            return

        # Filter for PNG files in the album
        png_photos = [photo for photo in album_photos if photo.uti == "public.png"]

        if not png_photos:
            print(f"No PNG files found in album '{album_name}'.")
            return

        # Sort photos by date-time ascending
        png_photos.sort(key=lambda p: p.date)

        # Group photos by date and export them
        date_counters = {}  # Track counters for each date
        for photo in png_photos:
            try:
                # Get the capture date and Sunday preceding or matching the date
                capture_date = photo.date
                sunday_date = get_previous_sunday(capture_date)
                formatted_date = sunday_date.strftime("%Y-%m-%d")

                # Increment the counter for the date
                if formatted_date not in date_counters:
                    date_counters[formatted_date] = 1
                else:
                    date_counters[formatted_date] += 1

                # Define the new file name with a counter
                counter = f"-{date_counters[formatted_date]:02d}"
                new_filename = f"{formatted_date}{counter}.png"
                destination_path = os.path.join(destination_folder, new_filename)

                # Export the photo and rename it
                exported_files = photo.export(destination_folder, use_photos_export=True)

                for exported_file in exported_files:
                    print(f"Exported: {exported_file}")

                    if os.path.exists(destination_path):
                        print(f"File already exists: {destination_path}")
                        os.remove(exported_file)
                        continue

                    # Rename the exported file
                    os.rename(exported_file, destination_path)

                    # Set the file dates
                    os.utime(destination_path, (capture_date.timestamp(), capture_date.timestamp()))

                    print(f"Exported and renamed to: {new_filename}")

            except Exception as e:
                print(f"Failed to export {photo.filename}: {e}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        photosdb = None

if __name__ == "__main__":

    print("Exporting PNG files from 'Wordscape Tournament Scores' album...")
    export_png_files_from_album("Wordscape Tournament Scores" , "tournament_scores")

    print("Exporting PNG files from 'Wordscape Team' album...")
    export_png_files_from_album("Wordscape Team", "weekend_warriors_team")
