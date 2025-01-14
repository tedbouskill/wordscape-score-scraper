from PIL import Image, ImageOps
import os

def has_transparency(image):
    """
    Check if an image has transparency.

    Args:
        image (PIL.Image.Image): The image to check.

    Returns:
        bool: True if the image has transparency, False otherwise.
    """
    if image.mode in ("RGBA", "LA") or ("transparency" in image.info):
        # Check if any pixel in the alpha channel is not fully opaque
        if image.mode == "RGBA":
            alpha_channel = image.getchannel("A")
            if alpha_channel.getextrema()[0] < 255:
                return True
        return True
    return False

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

# Example usage
if __name__ == "__main__":
    # Load an example image using a relative path
    relative_path = "../process_screenshots/tournament_scores/2024-09-01-01.png"  # Adjust as needed
    image_path = os.path.abspath(relative_path)

    # Open the image
    image = Image.open(image_path)

    # Check for transparency
    if has_transparency(image):
        print("The image has transparency.")
    else:
        print("The image does not have transparency.")

    # Process the image to remove everything but white
    processed_image = remove_everything_but_white(image)

    # Save the processed image to a relative path
    output_relative_path = "output_keep_only_white.png"
    processed_image.save(os.path.abspath(output_relative_path))
    print(f"Processed image saved to {output_relative_path}")
