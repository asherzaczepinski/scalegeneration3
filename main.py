import os
import shutil
from music21 import (
    stream, note, key, scale, clef, layout,
    environment, expressions, duration
)
from PIL import Image

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
    """
    Return a clef string (e.g. 'TrebleClef', 'BassClef', etc.)
    """
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
    """
    Create ascending + descending measures from start_octave up to (start_octave + num_octaves).
    """
    measures_stream = stream.Stream()

    # Build the pitch range, e.g. "C3" up to "C5"
    lower_pitch = f"{scale_object.tonic.name}{start_octave}"
    upper_pitch = f"{scale_object.tonic.name}{start_octave + num_octaves}"

    pitches_up = scale_object.getPitches(lower_pitch, upper_pitch)
    # For descending, reverse everything except the last note (avoid duplication)
    pitches_down = list(reversed(pitches_up[:-1]))
    all_pitches = pitches_up + pitches_down

    notes_per_measure = 7
    current_measure = stream.Measure()
    note_counter = 0

    for i, p in enumerate(all_pitches):
        # If we're on the very last note, put it in a whole-measure
        if i == len(all_pitches) - 1:
            if current_measure.notes:
                measures_stream.append(current_measure)
            m_whole = stream.Measure()
            # If it's the first note in the entire piece, add the title
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
            # Start a new measure if the current is not empty
            if current_measure.notes:
                measures_stream.append(current_measure)
            current_measure = stream.Measure()

            # Title text if first note overall
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
    # --------------------------------------------------------------------
    # 1. Setup Output & Instrument Settings
    # --------------------------------------------------------------------

    # Base output directory
    output_folder = "/Users/az/Desktop/scalegeneration3/output"

    # Remove the output folder each time
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    # Key signatures
    all_key_signatures = [
        "C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"
    ]

    # For each instrument, we can define a max octave count
    instrument_max_octaves = {
        "Violin": 3,
        # Add more instruments + their max octaves as needed
        # "Viola": 3,
        # "Trombone": 2,
    }

    # Which instruments to actually process
    all_instruments = [
        "Violin",
        # "Viola",
        # "Trombone",
        # ...
    ]

    # We'll start them all at the same start_octave
    start_octave = 3

    # --------------------------------------------------------------------
    # 2. Generate Scales & Collect PNG Paths
    # --------------------------------------------------------------------
    for instrument_name in all_instruments:
        print("=" * 70)
        print(f"Processing instrument: {instrument_name}")
        print("=" * 70)

        # Instrument output folder
        instrument_folder = os.path.join(
            output_folder,
            instrument_name.replace(" ", "_")
        )
        os.makedirs(instrument_folder, exist_ok=True)

        # Determine the clef
        selected_clef = determine_clef(instrument_name)
        # Determine the maximum octaves we want for this instrument
        max_octaves_for_instrument = instrument_max_octaves.get(instrument_name, 2)

        # We'll collect all PNG file paths here
        all_generated_png_paths = []

        # For each octave count from 1..max_octaves_for_instrument
        for octave_count in range(1, max_octaves_for_instrument + 1):
            # Make a subfolder like "1_octave" or "2_octaves"
            octave_label = f"{octave_count}_octave" if octave_count == 1 else f"{octave_count}_octaves"
            octave_folder = os.path.join(instrument_folder, octave_label)
            os.makedirs(octave_folder, exist_ok=True)

            # Generate a scale (major) for each key signature
            for key_sig in all_key_signatures:
                part = stream.Part()
                part.insert(0, layout.SystemLayout(isNew=True))
                part.insert(0, getattr(clef, selected_clef)())

                # Create Key + scale
                major_key_obj = key.Key(key_sig, 'major')
                major_scale_obj = scale.MajorScale(key_sig)

                # Create measures for ascending+descending
                title_text = (f"{instrument_name} - {key_sig} Major - "
                              f"{octave_count} octave{'s' if octave_count>1 else ''}")
                scale_measures = create_scale_measures(
                    title_text=title_text,
                    scale_object=major_scale_obj,
                    start_octave=start_octave,
                    num_octaves=octave_count
                )
                if not scale_measures:
                    continue

                # Insert the key signature in the first measure
                first_m = scale_measures[0]
                first_m.insert(0, major_key_obj)

                # Build the part
                for m in scale_measures:
                    part.append(m)

                # Score for this single scale
                scales_score = stream.Score([part])

                # Filename
                png_filename = f"{instrument_name}_{key_sig}_{octave_count}octaveScale.png"
                png_path = os.path.join(octave_folder, png_filename)

                # Write out to PNG via MuseScore (musicxml.png)
                scales_score.write('musicxml.png', fp=png_path)

                # If the direct path doesn't exist, check if there's a `-1` variant
                if not os.path.exists(png_path):
                    base, ext = os.path.splitext(png_path)
                    alt_path = f"{base}-1{ext}"
                    if os.path.exists(alt_path):
                        print(f"Found: {alt_path} instead of {png_path}")
                        png_path = alt_path  # Just use the alt path
                    else:
                        print(f"Warning: Could not find {png_path} or {alt_path}!")
                        continue

                print(f"Created PNG: {png_path}")
                all_generated_png_paths.append(png_path)

        # ----------------------------------------------------------------
        # 3. Combine All PNGs for This Instrument Into One PDF
        # ----------------------------------------------------------------
        if not all_generated_png_paths:
            print(f"No PNGs were generated for {instrument_name}. Skipping PDF.")
            continue

        # Sort them so they appear in a consistent order
        all_generated_png_paths.sort()

        # PDF layout settings
        DPI = 300
        PAGE_WIDTH = 8 * DPI      # 8.0 inches
        PAGE_HEIGHT = 11 * DPI    # 11.0 inches
        PADDING = 80
        SPACING = 250

        USABLE_WIDTH = PAGE_WIDTH - 2 * PADDING

        pages = []
        current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        current_y = PADDING

        for path in all_generated_png_paths:
            try:
                with Image.open(path) as img:
                    # If there's alpha, flatten onto white
                    if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode in ("RGBA", "LA"):
                            background.paste(img, mask=img.split()[3])
                        else:
                            background.paste(img)
                        final_img = background
                    else:
                        final_img = img.convert("RGB")

                    # Resize if needed
                    if final_img.width > USABLE_WIDTH:
                        ratio = USABLE_WIDTH / final_img.width
                        new_width = USABLE_WIDTH
                        new_height = int(final_img.height * ratio)
                        final_img = final_img.resize(
                            (new_width, new_height), 
                            resample=Image.Resampling.LANCZOS
                        )
            except Exception as e:
                print(f"Error opening image {path}: {e}")
                continue

            # If doesn't fit, new page
            if current_y + final_img.height > PAGE_HEIGHT - PADDING:
                pages.append(current_page)
                current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
                current_y = PADDING

            current_page.paste(final_img, (PADDING, current_y))
            current_y += final_img.height + SPACING

        # Add the last page if it has any content
        if current_y > PADDING:
            pages.append(current_page)

        # Save final PDF
        pdf_filename = f"{instrument_name.replace(' ', '_')}_AllOctaves.pdf"
        combined_pdf_path = os.path.join(instrument_folder, pdf_filename)

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
            print("No pages to save into PDF.")