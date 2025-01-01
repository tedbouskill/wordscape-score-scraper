import pytesseract
import re
import os
import sqlite3
import json

from datetime import datetime, timedelta
from PIL import Image, ImageOps

class ImageTools:
    @staticmethod
    def remove_everything_but_white(image, threshold=250):
        """
        Remove everything but white from an image.

        Args:
            image (PIL.Image.Image): The image to process.
            threshold (int): Brightness threshold for white (0-255). Defaults to 200.

        Returns:
            PIL.Image.Image: The processed image with only white pixels retained.
        """
        # Ensure the image is in RGB mode
        image = image.convert("RGB")

        # Create a new image for the output
        output_image = Image.new("RGB", image.size, (0, 0, 0))  # Black background

        # Process each pixel
        pixels = image.load()
        output_pixels = output_image.load()

        for y in range(image.height):
            for x in range(image.width):
                r, g, b = pixels[x, y]
                # Check if the pixel is "white" (all channels above the threshold)
                if r > threshold and g > threshold and b > threshold:
                    output_pixels[x, y] = (255, 255, 255)  # Keep white
                else:
                    output_pixels[x, y] = (0, 0, 0)  # Set everything else to black

        return output_image

