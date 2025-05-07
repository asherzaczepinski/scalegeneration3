import os
import shutil
from music21 import (
    stream, note, key, scale, clef, layout,
    environment, duration, pitch
)
from PIL import Image, ImageDraw

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
    # For our purposes we only need the Double Bass clef.
    instrument_map = {
        "Double Bass": "BassClef",
    }
    return instrument_map.get(instrument_name, "TrebleClef")

def create_scale_measures(title_text, scale_object, start_octave, max_high_octave_adjust, instrument_highest, instrument_name="Double Bass"):
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

def build_pages(image_paths, DPI, PAGE_WIDTH, PAGE_HEIGHT, PADDING, SPACING, USABLE_WIDTH):
    """Given a list of image file paths (already sorted in the desired order),
    build and return a list of page images.
    
    An extra 80px is added to the top of each page.
    """
    pages = []
    current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    current_y = PADDING + 60

    for path in image_paths:
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
                    final_img = final_img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Error opening image {path}: {e}")
            continue

        if current_y + final_img.height > PAGE_HEIGHT - PADDING:
            pages.append(current_page)
            current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
            current_y = PADDING + 80

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
    for key_sig in ["C", "G", "F", "D", "Bb", "A", "Eb", "E", "Ab", "B", "Db", "F#"]:
        safe_key = key_sig.replace("#", "sharp")
        if base.startswith(safe_key + ".") or base.startswith(safe_key + "_"):
            return key_sig
    return ""

if __name__ == "__main__":
    # ------------------------------------------------------------------------
    # Configuration Parameters (Double Bass 2nd octave into output2)
    # ------------------------------------------------------------------------
    base_output_folder = "/Users/az/Desktop/Sheet Scan/scalegeneration3"
    output2_folder = os.path.join(base_output_folder, "output2")
    
    # Delete and recreate the output2 folder.
    if os.path.exists(output2_folder):
        shutil.rmtree(output2_folder)
        print(f"Deleted existing folder: {output2_folder}")
    os.makedirs(output2_folder, exist_ok=True)
    print(f"Created folder: {output2_folder}")
    
    instrument_name = "Double Bass"
    
    # Instrument settings for Double Bass
    instrument_settings = {
        "Double Bass": {
            "lowest": pitch.Pitch("E2"),
            "highest": pitch.Pitch("G4"),
        }
    }
    settings = instrument_settings[instrument_name]
    instrument_lowest = settings["lowest"]
    instrument_highest = settings["highest"]
    
    instrument_folder = os.path.join(output2_folder, instrument_name.replace(" ", "_"))
    os.makedirs(instrument_folder, exist_ok=True)
    print(f"Created folder for {instrument_name}: {instrument_folder}")
    
    # Process only the 2‑octave version.
    octave_count = 2  
    octave_label = f"{octave_count}_octaves"
    octave_folder = os.path.join(instrument_folder, octave_label)
    os.makedirs(octave_folder, exist_ok=True)
    print(f"Created folder for octave {octave_count}: {octave_folder}")
    
    # PDF page settings
    DPI = 300
    PAGE_WIDTH = 8 * DPI
    PAGE_HEIGHT = 11 * DPI
    PADDING = 80
    SPACING = 350
    USABLE_WIDTH = PAGE_WIDTH - 2 * PADDING

    # For the Double Bass 2nd octave, generate F, G, and A major scales.
    keys_to_generate = ["F", "G", "A"]

    current_octave_paths = []

    selected_clef = determine_clef(instrument_name)
    base_start_octave = 3

    for key_sig in keys_to_generate:
        major_key_obj = key.Key(key_sig, 'major')
        major_scale_obj = scale.MajorScale(key_sig)

        # Determine an appropriate starting octave.
        start_octave = base_start_octave
        while pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave}") > instrument_lowest:
            start_octave -= 1
        while True:
            first_pitch = pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave}")
            if first_pitch < instrument_lowest:
                start_octave += 1
            else:
                break

        # For the 2‑octave version, force generation even if the highest note exceeds the instrument's range.
        max_high_octave_adjust = octave_count
        highest_note_pitch = pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave + max_high_octave_adjust}")
        # (For non-Double Bass cases we might skip scales out of range, but here we force generation.)

        part = stream.Part()
        part.insert(0, layout.SystemLayout(isNew=True))
        part.insert(0, getattr(clef, selected_clef)())

        # Generate the measures (no title text)
        scale_measures = create_scale_measures(
            title_text="",
            scale_object=major_scale_obj,
            start_octave=start_octave,
            max_high_octave_adjust=max_high_octave_adjust,
            instrument_highest=instrument_highest,
            instrument_name=instrument_name
        )

        if not scale_measures:
            print(f"No valid scale generated for {key_sig} major.")
            continue

        first_measure = scale_measures[0]
        first_measure.insert(0, major_key_obj)

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

        print(f"Created PNG for {key_sig} major: {png_path}")
        current_octave_paths.append(png_path)

    # Sort the generated PNG paths in circle-of-fifths order.
    # Standard circle-of-fifths order for major keys:
    circle_order = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
    sort_order = {k: i for i, k in enumerate(circle_order)}
    sorted_paths = sorted(current_octave_paths, key=lambda p: sort_order.get(key_from_path(p), 999))
    
    pages = build_pages(sorted_paths, DPI, PAGE_WIDTH, PAGE_HEIGHT, PADDING, SPACING, USABLE_WIDTH)

    # Save the combined PDF in output2.
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
        print("No pages to save into PDF.")
