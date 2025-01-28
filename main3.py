import os
from PIL import Image

def auto_crop_image(image_path, output_path, background_color=None, tolerance=10):
    """
    Crops the image to remove borders of a specific background color.

    :param image_path: Path to the original image.
    :param output_path: Path to save the cropped image.
    :param background_color: Tuple indicating the background color to remove (R, G, B). If None, uses the color of the top-left pixel.
    :param tolerance: Tolerance for color matching. Higher values allow more variance.
    """
    with Image.open(image_path) as img:
        # Convert image to RGBA to ensure it has an alpha channel
        img = img.convert("RGBA")
        datas = img.getdata()

        if background_color is None:
            # Use the color of the top-left pixel as the background color
            background_color = img.getpixel((0, 0))[:3]

        # Create a mask where the background pixels are transparent
        newData = []
        for item in datas:
            if all(abs(item[i] - background_color[i]) <= tolerance for i in range(3)):
                # If within tolerance, make pixel transparent
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)

        img.putdata(newData)

        # Get the bounding box of the non-transparent pixels
        bbox = img.getbbox()
        if bbox:
            cropped_img = img.crop(bbox)
            cropped_img.save(output_path, "PNG")
            print(f"Cropped and saved: {output_path}")
        else:
            print(f"No content to crop in: {image_path}")

def process_clarinet_folder(clarinet_folder):
    """
    Processes all images in the clarinet folder by auto-cropping them.

    :param clarinet_folder: Path to the 'clarinet' folder.
    """
    # Define the output folder
    output_folder = os.path.join(clarinet_folder, 'cropped')
    os.makedirs(output_folder, exist_ok=True)

    # Supported image extensions
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')

    # Loop through all files in the clarinet folder
    for filename in os.listdir(clarinet_folder):
        if filename.lower().endswith(supported_extensions):
            file_path = os.path.join(clarinet_folder, filename)
            # Define the output file path with PNG extension
            output_filename = os.path.splitext(filename)[0] + '.png'
            output_path = os.path.join(output_folder, output_filename)
            try:
                auto_crop_image(file_path, output_path)
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")

if __name__ == "__main__":
    # Replace this with the actual path to your 'clarinet' folder
    clarinet_folder = 'Clarinet'  # e.g., '/Users/username/Pictures/clarinet'

    if not os.path.isdir(clarinet_folder):
        print(f"The folder '{clarinet_folder}' does not exist. Please check the path.")
    else:
        process_clarinet_folder(clarinet_folder)
