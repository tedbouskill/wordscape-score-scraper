import logging
import os
import re
import sys
from PIL import Image

try:
    from cls_env_config import EnvConfigSingleton as EnvConfig
    from cls_env_tools import EnvTools
    from cls_logging_manager import LoggingManagerSingleton as LoggingManager
except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)

# Initialize the configuration settings here
env_config = EnvConfig()

repo_root = EnvTools.find_repo_root()

print(f"Repository root found at: {repo_root}")

# Define the relative subfolder path containing the images
subfolder = os.path.join(repo_root, "images/png_samples/weekend_scores")

# List all PNG files in the subfolder
png_files = [f for f in os.listdir(subfolder) if f.endswith('.png')]

if not png_files:
    print("No PNG files found in the specified subfolder.")
    exit()

# Sort files to get the first one (you can modify sorting criteria as needed)
png_files.sort()

# Get the first file
first_file = png_files[0]

# Extract the date from the file name using regex
match = re.match(r"(\d{4}-\d{2}-\d{2})", first_file)
if not match:
    print(f"No date found in the file name: {first_file}")
    exit()

date_extracted = match.group(1)
print(f"Date extracted from file name: {date_extracted}")

# Open the first image file
image_path = os.path.join(subfolder, first_file)
with Image.open(image_path) as img:
    print(f"Image size: {img.size} (width x height)")

    # Define the cropping area (x, y, width, height)
    # Adjust these values as needed to tune the OCR area
    crop_area = (50, 1038, 1284, 2482)  # Example values
    cropped_img = img.crop(crop_area)

    # Show the cropped image to tune the area
    cropped_img.show()

    # Print the crop area for reference
    print(f"Crop area: {crop_area} (left, top, right, bottom)")
