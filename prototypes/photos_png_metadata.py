import json
from osxphotos import PhotosDB
from datetime import datetime

def make_serializable(data):
    """
    Recursively process the data to make it JSON serializable.
    Converts datetime to ISO 8601 strings and handles other non-serializable types.
    """
    if isinstance(data, dict):
        return {key: make_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_serializable(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()  # Convert datetime to ISO 8601 string
    else:
        return data  # Return the data as-is if it's already serializable

def inspect_png_files():
    # Initialize the PhotosDB
    photosdb = PhotosDB()

    # Query all photos in the Photos library
    all_photos = photosdb.photos()

    # Filter for PNG files
    png_photos = [photo for photo in all_photos if photo.uti == "public.png"]

    print(f"Found {len(png_photos)} PNG files.\n")

    # Inspect attributes for each PNG photo
    for photo in png_photos:
        print(f"Filename: {photo.filename}")
        print(f"Original filename: {photo.original_filename}")
        print(f"Date: {photo.date}")
        print(f"Keywords: {photo.keywords}")
        print(f"Albums: {photo.albums}")
        print(f"Description: {photo.description}")
        print(f"Title: {photo.title}")
        print(f"Place: {photo.place}")
        print(f"Has adjustments: {photo.hasadjustments}")
        print(f"Is favorite: {photo.favorite}")
        print(f"Is hidden: {photo.hidden}")
        print(f"File UTI: {photo.uti}")
        print(f"Path to original: {photo.path}")
        print(f"Path to edited: {photo.path_edited}")

        # Preprocess and print the _info attribute as formatted JSON
        serializable_info = make_serializable(photo._info)
        print("Metadata (_info):")
        print(json.dumps(serializable_info, indent=4))
        print("\n---\n")

if __name__ == "__main__":
    inspect_png_files()
