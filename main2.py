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

def create_scale_measures(title_text, scale_object, start_octave, num_octaves, instrument_name="Violin"):
    measures_stream = stream.Stream()
    lower_pitch = f"{scale_object.tonic.name}{start_octave}"
    upper_pitch = f"{scale_object.tonic.name}{start_octave + num_octaves}"

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
            if i == 0:
                txt = expressions.TextExpression(title_text)
                txt.placement = 'above'
                m_whole.insert(0, txt)
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
            if i == 0:
                txt = expressions.TextExpression(title_text)
                txt.placement = 'above'
                current_measure.insert(0, txt)
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

def generate_scales_for_instrument(
    instrument_name,
    output_folder="output2",
    base_start_octave=3,
    max_octaves=2,
    dpi=300,
    page_width=8,
    page_height=11,
    padding=80,
    spacing=350,
    usable_width_ratio=1.0  # To allow dynamic adjustment if needed
):
    """
    Generate musical scales for a specified instrument and save the outputs.

    Parameters:
    - instrument_name (str): Name of the instrument (e.g., 'Violin', 'Flute').
    - output_folder (str): Base directory to save outputs. Defaults to 'output2'.
    - base_start_octave (int): Starting octave for scale generation. Defaults to 3.
    - max_octaves (int): Number of octaves to generate. Defaults to 2.
    - dpi (int): Resolution for image generation. Defaults to 300.
    - page_width (int): Width of the page in inches. Defaults to 8.
    - page_height (int): Height of the page in inches. Defaults to 11.
    - padding (int): Padding in pixels around the page. Defaults to 80.
    - spacing (int): Vertical spacing between images on the page. Defaults to 350.
    - usable_width_ratio (float): Ratio of the page width to use for images. Defaults to 1.0.
    """
    # Define all instruments and their settings
    instrument_settings = {
        "Violin": {
            "lowest": pitch.Pitch("G3"),
        },
        "Viola": {
            "lowest": pitch.Pitch("C3"),
        },
        "Cello": {
            "lowest": pitch.Pitch("C2"),
        },
        "Double Bass": {
            "lowest": pitch.Pitch("E2"),
        },
        # Added Instruments
        "Bass Clarinet": {
            "lowest": pitch.Pitch("E3"),  # B♭2
        },
        "Alto Saxophone": {
            "lowest": pitch.Pitch("C4"),
        },
        "Bassoon": {
            "lowest": pitch.Pitch("B1"),
        },
        "Clarinet": {
            "lowest": pitch.Pitch("E3"),  # Assuming B♭ Clarinet
        },
        "Euphonium": {
            "lowest": pitch.Pitch("E2"),
        },
        "Flute": {
            "lowest": pitch.Pitch("C4"),
        },
        "French Horn": {
            "lowest": pitch.Pitch("F3"),
        },
        "Oboe": {
            "lowest": pitch.Pitch("Bb3"),
        },
        "Piccolo": {
            "lowest": pitch.Pitch("D5"),
        },
        "Tenor Saxophone": {
            "lowest": pitch.Pitch("B2"),
        },
        "Trombone": {
            "lowest": pitch.Pitch("A2"),
        },
        "Trumpet": {
            "lowest": pitch.Pitch("F#3"),
        },
        "Tuba": {
            "lowest": pitch.Pitch("C3"),
        },
    }
    all_key_signatures = ["C", "G", "D", "A", "E", "B", "F#", "C#", "Ab", "Eb", "Bb", "F"]

    # Validate the instrument
    if instrument_name not in instrument_settings:
        raise ValueError(f"Instrument '{instrument_name}' is not supported. Supported instruments are: {list(instrument_settings.keys())}")

    settings = instrument_settings[instrument_name]
    instrument_lowest = settings["lowest"]

    # Setup output directory
    instrument_folder = os.path.join(output_folder, instrument_name.replace(" ", "_"))
    if os.path.exists(instrument_folder):
        shutil.rmtree(instrument_folder)
    os.makedirs(instrument_folder, exist_ok=True)

    selected_clef = determine_clef(instrument_name)

    DPI = dpi
    PAGE_WIDTH = page_width * DPI
    PAGE_HEIGHT = page_height * DPI
    PADDING = padding
    SPACING = spacing
    USABLE_WIDTH = PAGE_WIDTH - 2 * PADDING
    USABLE_WIDTH *= usable_width_ratio

    MAX_OCTAVES = max_octaves
    base_start_octave = base_start_octave

    for octave_count in range(1, MAX_OCTAVES + 1):
        print(f"Generating scales for {octave_count} octave(s) on {instrument_name}...")

        octave_label = f"{octave_count}_octave" if octave_count == 1 else f"{octave_count}_octaves"
        octave_folder = os.path.join(instrument_folder, octave_label)
        os.makedirs(octave_folder, exist_ok=True)

        current_octave_paths = []

        for key_sig in all_key_signatures:
            major_key_obj = key.Key(key_sig, 'major')
            major_scale_obj = scale.MajorScale(key_sig)

            # Initialize start_octave to a base value
            start_octave = base_start_octave

            # Decrease start_octave if the note is higher than the instrument's lowest
            while pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave}") > instrument_lowest:
                start_octave -= 1

            # Increase start_octave if the first note is below the instrument's lowest
            while True:
                first_pitch = pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave}")
                if first_pitch < instrument_lowest:
                    start_octave += 1
                else:
                    break

            part = stream.Part()
            part.insert(0, layout.SystemLayout(isNew=True))
            part.insert(0, getattr(clef, selected_clef)())

            title_text = f"{instrument_name} - {key_sig} Major - {octave_count} octave{'s' if octave_count>1 else ''}"
            scale_measures = create_scale_measures(
                title_text=title_text,
                scale_object=major_scale_obj,
                start_octave=start_octave,
                num_octaves=octave_count,
                instrument_name=instrument_name
            )

            if not scale_measures:
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
                else:
                    print(f"Warning: Could not find {png_path} or {alt_path}!")
                    continue

            print(f"Created PNG: {png_path}")
            current_octave_paths.append(png_path)

        # Sort the paths based on the circle of fifths
        circle_of_fifths_major = ["C", "G", "D", "A", "E", "B", "F#", "C#", "Ab", "Eb", "Bb", "F"]
        order_index = {k: i for i, k in enumerate(circle_of_fifths_major)}
        def key_from_path(p):
            base = os.path.basename(p)
            for key_sig in circle_of_fifths_major:
                safe_key = key_sig.replace("#", "sharp")
                if base.startswith(safe_key + ".") or base.startswith(safe_key + "_"):
                    return key_sig
            return ""
        current_octave_paths.sort(key=lambda p: order_index.get(key_from_path(p), 999))

        # Create PDF pages
        pages = []
        current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        draw = ImageDraw.Draw(current_page)

        title_font_size = 150
        try:
            font = ImageFont.truetype("arialbd.ttf", title_font_size)
        except IOError:
            try:
                font = ImageFont.truetype("arial.ttf", title_font_size)
            except IOError:
                font = ImageFont.load_default()
        current_y = PADDING 

        for path in current_octave_paths:
            try:
                with Image.open(path) as img:
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
                current_y = PADDING

            current_page.paste(final_img, (PADDING, current_y))
            current_y += final_img.height + SPACING

        if current_y > PADDING:
            pages.append(current_page)

        # Save combined PDF
        combined_pdf_path = os.path.join(octave_folder, "combined.pdf")
        if pages:
            pages[0].save(
                combined_pdf_path,
                "PDF",
                save_all=True,
                append_images=pages[1:],
                resolution=DPI
            )
            print(f"PDF created at: {combined_pdf_path}")
        else:
            print(f"No pages to save into PDF for folder {octave_folder}.")

        # Save individual pages as PNG
        combine_folder = os.path.join(octave_folder, "combine")
        os.makedirs(combine_folder, exist_ok=True)
        for idx, page in enumerate(pages, start=1):
            page_filename = f"page{idx}.png"
            page_path = os.path.join(combine_folder, page_filename)
            page.save(page_path, "PNG")
            print(f"Saved {page_path}")

    # End of generate_scales_for_instrument

# Example usage
if __name__ == "__main__":
    # Example: Generate scales for the Violin and Flute
    instruments_to_generate = ["Violin", "Flute"]
    for instrument in instruments_to_generate:
        try:
            generate_scales_for_instrument(
                instrument_name=instrument,
                output_folder="output2",
                base_start_octave=3,
                max_octaves=2
            )
        except ValueError as ve:
            print(ve)
