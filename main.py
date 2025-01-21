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
        "English Horn":    "TrebleClef",
        "Flute":           "TrebleClef",
        "Oboe":            "TrebleClef",
        "Piccolo":         "TrebleClef",
        "Tenor Saxophone": "TrebleClef",
        "Trumpet":         "TrebleClef",
        "Euphonium":       "BassClef",
        "French Horn":     "TrebleClef",
        "Trombone":        "BassClef",
        "Tuba":            "BassClef",
    }
    return instrument_map.get(instrument_name, "TrebleClef")

def create_scale_measures(title_text, scale_object, start_octave, num_octaves):
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

if __name__ == "__main__":
    # Setup output directory
    output_folder = "/Users/az/Desktop/scalegeneration3/output"
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    # Circle of fifths order for major keys
    circle_of_fifths_major = ["C", "G", "D", "A", "E", "B", "F#", "C#", "Ab", "Eb", "Bb", "F"]
    all_key_signatures = circle_of_fifths_major

    instrument_settings = {
        "Violin": {
            "lowest": pitch.Pitch("G3"),
            "highest": pitch.Pitch("A7"),
        },
    }
    all_instruments = ["Violin"]
    base_start_octave = 3

    DPI = 300
    PAGE_WIDTH = 8 * DPI
    PAGE_HEIGHT = 11 * DPI
    PADDING = 80
    SPACING = 350  # Increased spacing between images
    USABLE_WIDTH = PAGE_WIDTH - 2 * PADDING

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

        selected_clef = determine_clef(instrument_name)

        octave_count = 1
        previous_octave_folder = None
        previous_octave_keys = {}

        while True:
            print(f"Trying {octave_count} octave(s)...")
            octave_valid_for_some_key = False

            octave_label = f"{octave_count}_octave" if octave_count == 1 else f"{octave_count}_octaves"
            octave_folder = os.path.join(instrument_folder, octave_label)
            os.makedirs(octave_folder, exist_ok=True)

            current_octave_keys = {}
            current_octave_paths = []

            for key_sig in all_key_signatures:
                major_key_obj = key.Key(key_sig, 'major')
                major_scale_obj = scale.MajorScale(key_sig)

                start_octave = base_start_octave
                while True:
                    first_pitch = pitch.Pitch(f"{major_scale_obj.tonic.name}{start_octave}")
                    if first_pitch < instrument_lowest:
                        start_octave += 1
                    else:
                        break

                lower_pitch = f"{major_scale_obj.tonic.name}{start_octave}"
                upper_pitch = f"{major_scale_obj.tonic.name}{start_octave + octave_count}"
                pitches_up = major_scale_obj.getPitches(lower_pitch, upper_pitch)
                pitches_down = list(reversed(pitches_up[:-1]))
                all_pitches = pitches_up + pitches_down

                if any(p < instrument_lowest or p > instrument_highest for p in all_pitches):
                    continue

                octave_valid_for_some_key = True

                part = stream.Part()
                part.insert(0, layout.SystemLayout(isNew=True))
                part.insert(0, getattr(clef, selected_clef)())

                title_text = f"{instrument_name} - {key_sig} Major - {octave_count} octave{'s' if octave_count>1 else ''}"
                scale_measures = create_scale_measures(
                    title_text=title_text,
                    scale_object=major_scale_obj,
                    start_octave=start_octave,
                    num_octaves=octave_count
                )
                if not scale_measures:
                    continue

                first_m = scale_measures[0]
                first_m.insert(0, major_key_obj)

                for m in scale_measures:
                    part.append(m)

                scales_score = stream.Score([part])

                png_filename = f"{key_sig}_{octave_count}octave.png"
                png_path = os.path.join(octave_folder, png_filename)
                scales_score.write('musicxml.png', fp=png_path)

                # Handle alternative naming if necessary
                if not os.path.exists(png_path):
                    base_name, ext = os.path.splitext(png_path)
                    alt_path = f"{base_name}-1{ext}"
                    if os.path.exists(alt_path):
                        shutil.move(alt_path, png_path)
                    else:
                        print(f"Warning: Could not find {png_path} or {alt_path}!")
                        continue

                print(f"Created PNG: {png_path}")
                current_octave_keys[key_sig] = png_path
                current_octave_paths.append(png_path)

            missing_keys = set(all_key_signatures) - set(current_octave_keys.keys())
            if missing_keys:
                print(f"Missing scales for octave {octave_count}: {missing_keys}")
                if not previous_octave_folder:
                    print("No previous octave available to substitute missing scales. Stopping generation.")
                    shutil.rmtree(octave_folder)
                    break

                for key_sig in missing_keys:
                    prev_png_filename = f"{key_sig}_{octave_count-1}octave.png"
                    source_path = os.path.join(previous_octave_folder, prev_png_filename)
                    if os.path.exists(source_path):
                        dest_path = os.path.join(octave_folder, prev_png_filename)
                        shutil.copy(source_path, dest_path)
                        print(f"Copied from {source_path} to {dest_path}")
                        current_octave_keys[key_sig] = dest_path
                        current_octave_paths.append(dest_path)
                    else:
                        print(f"Could not find source for missing scale {key_sig} from previous octave at {source_path}.")

                still_missing = set(all_key_signatures) - set(current_octave_keys.keys())
                if still_missing:
                    print(f"Even after substitutions, scales missing for keys: {still_missing}")
                    print(f"Stopping further octave generation after {octave_count} octave(s).")
                    shutil.rmtree(octave_folder)
                    break

            if not octave_valid_for_some_key:
                print(f"No valid scales found for {octave_count} octave(s). Removing folder and stopping further generation.")
                shutil.rmtree(octave_folder)
                break

            # Sort current_octave_paths according to circle of fifths order
            order_index = {k: i for i, k in enumerate(circle_of_fifths_major)}
            def key_from_path(p):
                base = os.path.basename(p)
                for key_sig in circle_of_fifths_major:
                    if base.startswith(key_sig + "_"):
                        return key_sig
                return ""
            current_octave_paths.sort(key=lambda p: order_index.get(key_from_path(p), 999))

            # Generate combined.pdf for the current octave folder
            pages = []
            current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
            draw = ImageDraw.Draw(current_page)

            # Use a larger, bold font for title on the first page
            title_font_size = 150  # Increased title size for bigger text
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

                # If image doesn't fit on current page, start a new page without title
                if current_y + final_img.height > PAGE_HEIGHT - PADDING:
                    pages.append(current_page)
                    current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
                    draw = ImageDraw.Draw(current_page)
                    # For new pages without title, start at top padding
                    current_y = PADDING

                current_page.paste(final_img, (PADDING, current_y))
                current_y += final_img.height + SPACING

            if current_y > PADDING:
                pages.append(current_page)

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

            # Create "combine" folder to store individual page PNGs
            combine_folder = os.path.join(octave_folder, "combine")
            os.makedirs(combine_folder, exist_ok=True)
            for idx, page in enumerate(pages, start=1):
                page_filename = f"page{idx}.png"
                page_path = os.path.join(combine_folder, page_filename)
                page.save(page_path, "PNG")
                print(f"Saved {page_path}")

            previous_octave_folder = octave_folder
            previous_octave_keys = current_octave_keys.copy()
            octave_count += 1
