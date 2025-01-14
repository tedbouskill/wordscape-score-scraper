import os
from datetime import datetime, timedelta
from osxphotos import PhotosDB

def get_previous_sunday(date):
    """
    Calculate the Sunday preceding or equal to the given date.
    """
    return date - timedelta(days=date.weekday() + 1 if date.weekday() != 6 else 0)

def group_photos_by_time(photos, time_threshold=300):
    """
    Group photos based on capture time within a specified threshold (in seconds).
    """
    grouped_photos = []
    current_group = []

    for photo in photos:
        capture_time = photo.date
        if not current_group:
            current_group.append(photo)
        else:
            last_capture_time = current_group[-1].date
            if (capture_time - last_capture_time).total_seconds() <= time_threshold:
                current_group.append(photo)
            else:
                grouped_photos.append(current_group)
                current_group = [photo]

    if current_group:
        grouped_photos.append(current_group)

    return grouped_photos

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

        # Group photos by capture time within 5 minutes
        grouped_photos = group_photos_by_time(png_photos, time_threshold=300)

        for group in grouped_photos:
            if not group:
                continue

            # Use the capture date, hour, and minute of the first photo in the group
            first_photo = group[0]
            capture_date = first_photo.date
            formatted_date = capture_date.strftime("%Y-%m-%d_%H-%M")

            for index, photo in enumerate(group, start=1):
                try:
                    # Define the new file name with a counter
                    counter = f"{index:02d}"
                    new_filename = f"{formatted_date}_{counter}.png"
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
        del photosdb

if __name__ == "__main__":
    print("Exporting PNG files from 'Wordscape Tournament Scores' album...")
    export_png_files_from_album("Wordscape Tournament Scores", "tournament_scores")

    print("Exporting PNG files from 'Wordscape Team' album...")
    export_png_files_from_album("Wordscape Team", "weekend_warriors_team")
