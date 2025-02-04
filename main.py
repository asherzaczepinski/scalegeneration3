import os
import shutil
from music21 import (
    stream, note, key, scale, clef, layout,
    environment, expressions, duration, pitch
)
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------------
# Configure music21 to find MuseScore on your system
# ------------------------------------------------------------------------
environment.set('musicxmlPath', '/Applications/MuseScore 3.app/Contents/MacOS/mscore')
environment.set('musescoreDirectPNGPath', '/Applications/MuseScore 3.app/Contents/MacOS/mscore')

# ------------------------------------------------------------------------
# Enharmonic mappings
# ------------------------------------------------------------------------
ENHARM_MAP = {
    "E#": ("F", 0),
    "B#": ("C", +1),
    "Cb": ("B", -1),
    "Fb": ("E", 0),
}

def fix_enharmonic_spelling(n):
    """Adjust note n's pitch spelling if in ENHARM_MAP."""
    if not n.pitch:
        return
    original_name = n.pitch.name
    if original_name in ENHARM_MAP:
        new_name, octave_adjust = ENHARM_MAP[original_name]
        n.pitch.name = new_name
        n.pitch.octave += octave_adjust
    if n.pitch.accidental is not None:
        n.pitch.accidental.displayStatus = True
        n.pitch.accidental.displayType = 'normal'

def determine_clef(instrument_name):
    instrument_map = {
        "Violin":          "TrebleClef",
        "Viola":           "AltoClef",
        "Cello":           "BassClef",
        "Double Bass":     "BassClef",
        "Harp":            "TrebleClef",
        "Alto Saxophone":  "TrebleClef",
        "Bass Clarinet":   "TrebleClef",
        "Bassoon":         "BassClef",
        "Clarinet":        "TrebleClef",
        "Euphonium":       "BassClef",
        "Flute":           "TrebleClef",
        "French Horn":     "TrebleClef",
        "Oboe":            "TrebleClef",
        "Piccolo":         "TrebleClef",
        "Tenor Saxophone": "TrebleClef",
        "Trumpet":         "TrebleClef",
        "Trombone":        "BassClef",
        "Tuba":            "BassClef",
    }
    return instrument_map.get(instrument_name, "TrebleClef")

def create_scale_measures(title_text, scale_object, start_octave, max_high_octave_adjust, instrument_highest, instrument_name="Violin"):
    """Generate the scale measures without any title text."""
    measures_stream = stream.Stream()
    lower_pitch = f"{scale_object.tonic.name}{start_octave}"
    upper_pitch = f"{scale_object.tonic.name}{start_octave + max_high_octave_adjust}"

    pitches_up = scale_object.getPitches(lower_pitch, upper_pitch)
    pitches_down = list(reversed(pitches_up[:-1]))
    all_pitches = pitches_up + pitches_down

    notes_per_measure = 7
    current_measure = stream.Measure()
    note_counter = 0

    for i, p in enumerate(all_pitches):
        # Handle last note as a whole note in its own measure
        if i == len(all_pitches) - 1:
            if current_measure.notes:
                measures_stream.append(current_measure)
            m_whole = stream.Measure()
            # (Title text removed)
            n = note.Note(p)
            n.duration = duration.Duration('whole')
            fix_enharmonic_spelling(n)
            m_whole.append(n)
            measures_stream.append(m_whole)
            break

        pos_in_measure = note_counter % notes_per_measure
        if pos_in_measure == 0:
            if current_measure.notes:
                measures_stream.append(current_measure)
            current_measure = stream.Measure()
            # (Title text removed)
            n = note.Note(p)
            n.duration = duration.Duration('quarter')
            fix_enharmonic_spelling(n)
            current_measure.append(n)
        else:
            n = note.Note(p)
            n.duration = duration.Duration('eighth')
            fix_enharmonic_spelling(n)
            current_measure.append(n)
        note_counter += 1

    return measures_stream

def get_fingering_image_filename(instrument_name):
    """
    Map the instrument name to the fingering image filename.
    Modify this function if your fingering images have different naming conventions.
    """
    mapping = {
        "Alto Saxophone": "Alto Sax.jpg",
        "Bass Clarinet": "Bass Clarinet.jpg",
        # Add more mappings as needed
    }
    return mapping.get(instrument_name, f"{instrument_name}.jpg")

def build_pages(image_paths, DPI, PAGE_WIDTH, PAGE_HEIGHT, PADDING, SPACING, USABLE_WIDTH):
    """Given a list of image file paths (already sorted in the desired order),
    build and return a list of page images.
    
    An extra 80px is added to the top of each page.
    """
    pages = []
    current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(current_page)
    # Start below the top margin plus an extra 80px:
    current_y = PADDING + 60

    for path in image_paths:
        try:
            with Image.open(path) as img:
                # Ensure the image is in RGB
                if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode in ("RGBA", "LA"):
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img)
                    final_img = background
                else:
                    final_img = img.convert("RGB")

                if final_img.width > USABLE_WIDTH:
                    ratio = USABLE_WIDTH / final_img.width
                    new_width = int(final_img.width * ratio)
                    new_height = int(final_img.height * ratio)
                    final_img = final_img.resize(
                        (new_width, new_height), 
                        resample=Image.Resampling.LANCZOS
                    )
        except Exception as e:
            print(f"Error opening image {path}: {e}")
            continue

        if current_y + final_img.height > PAGE_HEIGHT - PADDING:
            pages.append(current_page)
            current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
            draw = ImageDraw.Draw(current_page)
            current_y = PADDING + 80  # Reset with extra top margin

        current_page.paste(final_img, (PADDING, current_y))
        current_y += final_img.height + SPACING

    if current_y > PADDING + 80:
        pages.append(current_page)
    return pages

# -------------------------
# Helper: extract key from filename
# -------------------------
def key_from_path(p):
    base = os.path.basename(p)
    for key_sig in ALL_KEY_SIGNATURES:
        safe_key = key_sig.replace("#", "sharp")
        if base.startswith(safe_key + ".") or base.startswith(safe_key + "_"):
            return key_sig
    return ""

if __name__ == "__main__":
    # ------------------------------------------------------------------------
    # Configuration Parameters
    # ------------------------------------------------------------------------
    base_output_folder = "/Users/az/Desktop/Sheet Scan/scalegeneration3"
    output_folder = os.path.join(base_output_folder, "output")
    output2_folder = os.path.join(base_output_folder, "output2")  # New output2 folder

    # Create output folder
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
        print(f"Deleted existing folder: {output_folder}")
    os.makedirs(output_folder, exist_ok=True)
    print(f"Created folder: {output_folder}")

    # Create output2 folder
    if os.path.exists(output2_folder):
        shutil.rmtree(output2_folder)
        print(f"Deleted existing folder: {output2_folder}")
    os.makedirs(output2_folder, exist_ok=True)
    print(f"Created folder: {output2_folder}")

    # ------------------------------------------------------------------------
    # Key Signature Orders
    # ------------------------------------------------------------------------
    # Original list kept here for possible later reference (not used for generation)
    ALL_KEY_SIGNATURES = [
        "C",    # No sharps/flats
        "G",    # 1 Sharp
        "F",    # 1 Flat
        "D",    # 2 Sharps
        "Bb",   # 2 Flats
        "A",    # 3 Sharps
        "Eb",   # 3 Flats
        "E",    # 4 Sharps
        "Ab",   # 4 Flats
        "B",    # 5 Sharps
        "Db",   # 5 Flats
        "F#"    # 6 Sharps
    ]
    # Circle-of-Fifths order is now used for generation:
    circle_order = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]

    instrument_settings = {
        "Violin": {
            "lowest": pitch.Pitch("G3"),
            "highest": pitch.Pitch("A7"),
        },
        "Viola": {
            "lowest": pitch.Pitch("C3"),
            "highest": pitch.Pitch("E6"),
        },
        "Cello": {
            "lowest": pitch.Pitch("C2"),
            "highest": pitch.Pitch("C6"),
        },
        "Double Bass": {
            "lowest": pitch.Pitch("E2"),
            "highest": pitch.Pitch("G4"),
        },
        "Bass Clarinet": {
            "lowest": pitch.Pitch("E3"),
            "highest": pitch.Pitch("C7"),
        },
        "Alto Saxophone": {
            "lowest": pitch.Pitch("C4"),
            "highest": pitch.Pitch("F6"),
        },
        "Bassoon": {
            "lowest": pitch.Pitch("B1"),
            "highest": pitch.Pitch("E5"),
        },
        "Clarinet": {
            "lowest": pitch.Pitch("E3"),
            "highest": pitch.Pitch("G6"),
        },
        "Euphonium": {
            "lowest": pitch.Pitch("E2"),
            "highest": pitch.Pitch("C5"),
        },
        "Flute": {
            "lowest": pitch.Pitch("C4"),
            "highest": pitch.Pitch("C7"),
        },
        "French Horn": {
            "lowest": pitch.Pitch("F3"),
            "highest": pitch.Pitch("D6"),
        },
        "Oboe": {
            "lowest": pitch.Pitch("Bb3"),
            "highest": pitch.Pitch("A6"),
        },
        "Piccolo": {
            "lowest": pitch.Pitch("D5"),
            "highest": pitch.Pitch("D8"),
        },
        "Tenor Saxophone": {
            "lowest": pitch.Pitch("C4"),
            "highest": pitch.Pitch("F6"),
        },
        "Trombone": {
            "lowest": pitch.Pitch("A2"),
            "highest": pitch.Pitch("F5"),
        },
        "Trumpet": {
            "lowest": pitch.Pitch("F#3"),
            "highest": pitch.Pitch("D6"),
        },
        "Tuba": {
            "lowest": pitch.Pitch("E1"),
            "highest": pitch.Pitch("Bb4"),
        },
    }
    all_instruments = [
        "Violin", 
        "Viola", 
        "Cello", 
        "Double Bass",
        "Bass Clarinet", 
        "Alto Saxophone", 
        "Bassoon", 
        "Clarinet",
        "Euphonium", 
        "Flute", 
        "French Horn", 
        "Oboe",
        "Piccolo", 
        "Tenor Saxophone", 
        "Trombone", 
        "Trumpet", 
        "Tuba"
    ]
    base_start_octave = 3

    DPI = 300
    PAGE_WIDTH = 8 * DPI
    PAGE_HEIGHT = 11 * DPI
    PADDING = 80
    SPACING = 350
    USABLE_WIDTH = PAGE_WIDTH - 2 * PADDING

    # Define the fingerings folder
    fingerings_folder = os.path.join(base_output_folder, "fingerings")

    for instrument_name in all_instruments:
        print("=" * 70)
        print(f"Processing instrument: {instrument_name}")
        print("=" * 70)

        settings = instrument_settings.get(instrument_name)
        if not settings:
            print(f"No settings found for {instrument_name}. Skipping.")
            continue

        instrument_lowest = settings["lowest"]
        instrument_highest = settings["highest"]
        instrument_folder = os.path.join(output_folder, instrument_name.replace(" ", "_"))
        os.makedirs(instrument_folder, exist_ok=True)
        print(f"Created folder: {instrument_folder}")

        # Setup corresponding folder in output2
        instrument_folder_output2 = os.path.join(output2_folder, instrument_name.replace(" ", "_"))
        os.makedirs(instrument_folder_output2, exist_ok=True)
        print(f"Created folder in output2: {instrument_folder_output2}")

        selected_clef = determine_clef(instrument_name)

        octave_count = 1  # Start with 1 octave
        continue_generating = True

        while continue_generating:
            print(f"Generating scales for {octave_count} octave{'s' if octave_count > 1 else ''} on {instrument_name}...")

            octave_label = f"{octave_count}_octave" if octave_count == 1 else f"{octave_count}_octaves"
            octave_folder = os.path.join(instrument_folder, octave_label)
            os.makedirs(octave_folder, exist_ok=True)
            print(f"Created folder: {octave_folder}")

            # Setup corresponding octave folder in output2
            octave_folder_output2 = os.path.join(instrument_folder_output2, octave_label)
            os.makedirs(octave_folder_output2, exist_ok=True)
            print(f"Created folder in output2: {octave_folder_output2}")

            current_octave_paths = []
            exceeded = False  # Flag to check if any scale exceeds the highest pitch

            # Iterate in circle-of-fifths order
            for key_sig in circle_order:
                major_key_obj = key.Key(key_sig, 'major')
                major_scale_obj = scale.MajorScale(key_sig)

                start_octave = base_start_octave
                # Adjust start_octave so that the tonic is not above instrument_lowest
                while pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave}") > instrument_lowest:
                    start_octave -= 1
                while True:
                    first_pitch = pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave}")
                    if first_pitch < instrument_lowest:
                        start_octave += 1
                    else:
                        break

                max_high_octave_adjust = octave_count
                highest_note_pitch = pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave + max_high_octave_adjust}")

                if highest_note_pitch > instrument_highest:
                    exceeded = True
                    print(f"Scale {key_sig} Major in octave {octave_count} exceeds the highest pitch {instrument_highest}. Skipping this scale.")
                    continue

                part = stream.Part()
                part.insert(0, layout.SystemLayout(isNew=True))
                part.insert(0, getattr(clef, selected_clef)())

                # Pass an empty string for title_text so that no title is rendered
                scale_measures = create_scale_measures(
                    title_text="",
                    scale_object=major_scale_obj,
                    start_octave=start_octave,
                    max_high_octave_adjust=max_high_octave_adjust,
                    instrument_highest=instrument_highest,
                    instrument_name=instrument_name
                )

                if not scale_measures:
                    print(f"No valid scales generated for {key_sig} major on {instrument_name} with {octave_count} octave{'s' if octave_count > 1 else ''}.")
                    continue

                first_m = scale_measures[0]
                first_m.insert(0, major_key_obj)

                for m in scale_measures:
                    part.append(m)

                scales_score = stream.Score([part])

                safe_key_sig = key_sig.replace("#", "sharp")
                png_filename = f"{safe_key_sig}.png"
                png_path = os.path.join(octave_folder, png_filename)
                scales_score.write('musicxml.png', fp=png_path)

                if not os.path.exists(png_path):
                    base_name, ext = os.path.splitext(png_path)
                    alt_path = f"{base_name}-1{ext}"
                    if os.path.exists(alt_path):
                        shutil.move(alt_path, png_path)
                        print(f"Moved alternative PNG to: {png_path}")
                    else:
                        print(f"Warning: Could not find {png_path} or {alt_path}!")
                        continue

                print(f"Created PNG: {png_path}")
                current_octave_paths.append(png_path)

            # -------------------------------
            # Build PDF pages (in circle-of-fifths order)
            # -------------------------------
            circle_order_index = {k: i for i, k in enumerate(circle_order)}
            sorted_paths = sorted(current_octave_paths, key=lambda p: circle_order_index.get(key_from_path(p), 999))
            pages = build_pages(sorted_paths, DPI, PAGE_WIDTH, PAGE_HEIGHT, PADDING, SPACING, USABLE_WIDTH)

            # --------------------------------------------
            # Add Fingering Image as the Last Page
            # --------------------------------------------
            fingering_image_filename = get_fingering_image_filename(instrument_name)
            fingering_image_path = os.path.join(fingerings_folder, fingering_image_filename)

            if os.path.exists(fingering_image_path):
                try:
                    with Image.open(fingering_image_path) as fing_img:
                        if fing_img.mode in ("RGBA", "LA") or ("transparency" in fing_img.info):
                            background = Image.new("RGB", fing_img.size, (255, 255, 255))
                            if fing_img.mode in ("RGBA", "LA"):
                                background.paste(fing_img, mask=fing_img.split()[3])
                            else:
                                background.paste(fing_img)
                            fingering_final_img = background
                        else:
                            fingering_final_img = fing_img.convert("RGB")

                        if fingering_final_img.width != PAGE_WIDTH or fingering_final_img.height != PAGE_HEIGHT:
                            fingering_final_img = fingering_final_img.resize(
                                (PAGE_WIDTH, PAGE_HEIGHT),
                                resample=Image.Resampling.LANCZOS
                            )

                        pages.append(fingering_final_img)
                        print(f"Added fingering image to the pages: {fingering_image_path}")
                except Exception as e:
                    print(f"Error processing fingering image {fingering_image_path}: {e}")
            else:
                print(f"No fingering image found for {instrument_name} at {fingering_image_path}. Skipping fingering image.")

            # --------------------------------------------
            # Save PDF
            # --------------------------------------------
            combined_pdf_path = os.path.join(octave_folder, "combined.pdf")
            if pages:
                try:
                    pages[0].save(
                        combined_pdf_path,
                        "PDF",
                        save_all=True,
                        append_images=pages[1:],
                        resolution=DPI
                    )
                    print(f"PDF created at: {combined_pdf_path}")
                except Exception as e:
                    print(f"Error saving PDF {combined_pdf_path}: {e}")
            else:
                print(f"No pages to save into PDF for folder {octave_folder}.")

            # Optionally, save each page as separate PNGs in a 'combine' subfolder
            combine_folder = os.path.join(octave_folder, "combine")
            os.makedirs(combine_folder, exist_ok=True)
            for idx, page in enumerate(pages, start=1):
                page_filename = f"page{idx}.png"
                page_path = os.path.join(combine_folder, page_filename)
                try:
                    page.save(page_path, "PNG")
                    print(f"Saved {page_path}")
                except Exception as e:
                    print(f"Error saving image {page_path}: {e}")

            # Copy combined PDF to output2
            try:
                shutil.copy(combined_pdf_path, os.path.join(octave_folder_output2, "combined.pdf"))
                print(f"Copied combined PDF to output2.")
            except Exception as e:
                print(f"Error copying combined PDF to output2: {e}")

            if exceeded:
                print(f"Stopping further octave generation for {instrument_name} as some scales in octave {octave_count} exceed the highest playable pitch.")
                break

            octave_count += 1

        print(f"Completed processing for {instrument_name}.\n")
