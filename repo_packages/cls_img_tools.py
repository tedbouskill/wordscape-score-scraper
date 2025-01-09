import cv2
import numpy as np

from PIL import Image

class ImageTools:
    @staticmethod
    def resize_image_opencv(image_path: str, new_width: int = 1200) -> np.ndarray:
        # Read the image
        img = cv2.imread(image_path)

        # Get the original dimensions
        original_height, original_width = img.shape[:2]

        # Calculate the new dimensions
        aspect_ratio = original_height / original_width
        new_height = int(aspect_ratio * new_width)

        # Resize the image
        resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

        return resized_img, new_height

    @staticmethod
    def crop_image_opencv(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
        # Crop the image using array slicing
        cropped_img = image[y:y+height, x:x+width]
        return cropped_img

    @staticmethod
    def convert_non_white_to_black_opencv(image: np.ndarray, threshold=225) -> np.ndarray:
        # Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Create a mask where pixels above the threshold are considered white
        mask = gray > threshold

        # Create an output image and set all pixels to black
        output = np.zeros_like(image)

        # Set the pixels that are above the threshold in the original image to white in the output image
        output[mask] = [255, 255, 255]

        return output

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

