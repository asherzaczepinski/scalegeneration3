import os
from PIL import Image

# ---------------------------------------------
# The following PNG generation code has been commented out.
# This script only combines existing PNG images.
# ---------------------------------------------
# (Your PNG generation code would be here)
#
# generated_png_paths = [ ... ]  # A list of PNG file paths created by your scale generation logic

# ---------------------------------------------
# Default PNG file paths based on your log output.
# ---------------------------------------------
generated_png_paths = [
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_C_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_C#_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_D_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_Eb_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_E_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_F_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_F#_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_G_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_Ab_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_A_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_Bb_Major_Scale_Octave_3.png",
    "/Users/az/Desktop/scalegeneration3/output/Clarinet/Octave_3/Clarinet_B_Major_Scale_Octave_3.png"
]

# Exit if no PNG paths are provided.
if not generated_png_paths:
    print("No PNG paths provided. Please populate the 'generated_png_paths' list with your file paths.")
    exit()

# ---------------------------------------------
# Define page size and padding (8" × 11" page at 100 DPI in portrait orientation).
# ---------------------------------------------
DPI = 300  # Increase this (e.g., 150 or 300) for higher resolution output.
PAGE_WIDTH = 8 * DPI    # 8 inches * 100 DPI = 800 pixels
PAGE_HEIGHT = 11 * DPI  # 11 inches * 100 DPI = 1100 pixels
PADDING = 40            # 40 pixels padding from all sides
SPACING = 200            # Additional vertical space between each image

USABLE_WIDTH = PAGE_WIDTH - 2 * PADDING  # 800 - 80 = 720 pixels
USABLE_HEIGHT = PAGE_HEIGHT - 2 * PADDING  # 1100 - 80 = 1020 pixels

# ---------------------------------------------
# Load PNG images and handle transparency.
# ---------------------------------------------
scale_images = []
for path in generated_png_paths:
    try:
        with Image.open(path) as img:
            # Convert images with transparency to RGB on a white background.
            if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode in ("RGBA", "LA"):
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                scale_images.append(background.copy())
            else:
                scale_images.append(img.convert("RGB").copy())
    except Exception as e:
        print(f"Error opening image {path}: {e}")

# ---------------------------------------------
# Combine images into multipage PDF pages.
# ---------------------------------------------
pages = []
current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
current_y = PADDING  # Start at 40 pixels from the top edge

for img in scale_images:
    # Resize the image if it's too wide for the usable area.
    if img.width > USABLE_WIDTH:
        ratio = USABLE_WIDTH / img.width
        new_width = USABLE_WIDTH
        new_height = int(img.height * ratio)
        img = img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)
    
    # Check if the image (plus spacing) fits on the current page.
    if current_y + img.height > PAGE_HEIGHT - PADDING:
        pages.append(current_page)
        current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        current_y = PADDING  # Reset vertical position for the new page

    # Paste the image onto the current page with left padding.
    current_page.paste(img, (PADDING, current_y))
    # Increase current_y by the image height plus extra spacing.
    current_y += img.height + SPACING

# Append the last page if it has content.
if current_y > PADDING:
    pages.append(current_page)

# ---------------------------------------------
# Save the pages as a multipage PDF.
# ---------------------------------------------
combined_pdf_path = os.path.join("combined.pdf")
if pages:
    pages[0].save(
        combined_pdf_path,
        "PDF",
        save_all=True,
        append_images=pages[1:],
        resolution=DPI
    )
    print(f"Combined multipage PDF created at: {combined_pdf_path}")
else:
    print("No pages were created.")
