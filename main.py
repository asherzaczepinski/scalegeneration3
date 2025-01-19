import os
import shutil  # To remove directories
from music21 import (
    stream, note, key, scale, clef, layout,
    environment, expressions, duration
)
from PIL import Image, ImageOps

# ------------------------------------------------------------------------
# Point music21 to MuseScore 3 (adjust paths for your system)
# ------------------------------------------------------------------------
environment.set('musicxmlPath', '/Applications/MuseScore 3.app/Contents/MacOS/mscore')
environment.set('musescoreDirectPNGPath', '/Applications/MuseScore 3.app/Contents/MacOS/mscore')

# ------------------------------------------------------------------------
# Enharmonic mapping: name -> (newName, octaveAdjustment)
# ------------------------------------------------------------------------
ENHARM_MAP = {
    "E#": ("F", 0),
    "B#": ("C", +1),
    "Cb": ("B", -1),
    "Fb": ("E", 0),
}

def fix_enharmonic_spelling(n):
    """Adjust enharmonic spelling using ENHARM_MAP if needed."""
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

def determine_clef_and_octave(instrument_name, part='right'):
    """
    Return a tuple (ClefName, OctaveStart) or a dict if the instrument is Piano.
    """
    if instrument_name == "Piano":
        # Return a dict for both hands
        return {
            "right": ("TrebleClef", 4),
            "left": ("BassClef", 2)
        }
    
    # Full instrument map
    instrument_map = {
        "Violin":          ("TrebleClef", 3),
        "Viola":           ("AltoClef",   3),
        "Cello":           ("BassClef",   2),
        "Double Bass":     ("BassClef",   1),
        "Harp":            ("TrebleClef", 3),
        "Alto Saxophone":  ("TrebleClef", 4),
        "Bass Clarinet":   ("TrebleClef", 2),
        "Bassoon":         ("BassClef",   2),
        "Clarinet":        ("TrebleClef", 3),
        "English Horn":    ("TrebleClef", 4),
        "Flute":           ("TrebleClef", 4),
        "Oboe":            ("TrebleClef", 4),
        "Piccolo":         ("TrebleClef", 5),
        "Tenor Saxophone": ("TrebleClef", 3),
        "Trumpet":         ("TrebleClef", 4),
        "Euphonium":       ("BassClef",   2),
        "French Horn":     ("TrebleClef", 3),
        "Trombone":        ("BassClef",   2),
        "Tuba":            ("BassClef",   1),
    }

    return instrument_map.get(instrument_name, ("TrebleClef", 4))

def create_scale_measures(title_text, scale_object, octave_start, num_octaves):
    """
    Create a series of measures containing ascending and descending scales
    for the specified scale object, starting octave, and number of octaves.
    """
    measures_stream = stream.Stream()
    pitches_up = scale_object.getPitches(
        f"{scale_object.tonic.name}{octave_start}",
        f"{scale_object.tonic.name}{octave_start + num_octaves}"
    )
    # For descending, reverse everything except the last note (to avoid a duplicate)
    pitches_down = list(reversed(pitches_up[:-1]))
    all_pitches = pitches_up + pitches_down

    notes_per_measure = 7
    current_measure = stream.Measure()
    note_counter = 0

    for i, p in enumerate(all_pitches):
        # If we're at the very last note, give it a whole note measure.
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
    # --------------------------------------------------------------------
    # 1. Generate PNG images for scales using music21 and MuseScore.
    # --------------------------------------------------------------------
    # Base output directory.
    output_folder = "/Users/az/Desktop/scalegeneration3/output"

    # Remove the output folder (and its contents) each time the script runs.
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    # List all key signatures to generate
    all_key_signatures = [
        "C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"
    ]
    num_octaves = 3  # Number of octaves for each scale.

    # Use only band/orchestra instruments (no percussion, guitars, etc.)
    all_instruments = [
        # Strings
        "Violin", 
        # "Viola", "Cello", "Double Bass", "Harp",
        # # Woodwinds
        # "Flute", "Piccolo", "Oboe", "English Horn",
        # "Clarinet", "Bass Clarinet", "Bassoon",
        # "Alto Saxophone", "Tenor Saxophone",
        # # Brass
        # "French Horn", "Trumpet", "Trombone", "Euphonium", "Tuba",
        # Optional: Uncomment "Piano" if you want it included.
        # "Piano",
    ]

    # --------------------------------------------------------------------
    # For each instrument, generate the scales, save PNGs, and then create
    # one PDF containing all the PNGs for that instrument.
    # --------------------------------------------------------------------
    for instrument_name in all_instruments:
        print("=" * 60)
        print(f"Processing instrument: {instrument_name}")
        print("=" * 60)

        # Create folder for this instrument's outputs.
        instrument_folder = os.path.join(
            output_folder, instrument_name.replace(" ", "_")
        )
        os.makedirs(instrument_folder, exist_ok=True)

        # Determine the clef & base octave. (Could be a dict if it's Piano.)
        clef_octave = determine_clef_and_octave(instrument_name)

        # We'll store all generated PNG paths for this instrument
        generated_png_paths = []

        # A small helper to handle either a single-staff or two-staff instrument (e.g. Piano).
        if isinstance(clef_octave, dict):
            # Example: Piano -> {"right": ("TrebleClef", 4), "left": ("BassClef", 2)}
            parts_to_make = clef_octave.items()
        else:
            # Single staff instrument
            parts_to_make = [("single", clef_octave)]

        # We'll assume each staff range is from baseOctave to baseOctave + 2 (or any range you like).
        for staff_label, (selected_clef, base_octave) in parts_to_make:
            # Range of octaves from base_octave to base_octave + 2.
            min_octave = base_octave
            max_octave = base_octave + 2

            # Loop through each octave in that range
            for octave in range(min_octave, max_octave + 1):
                # Create a folder for each octave (optional).
                octave_folder = os.path.join(
                    instrument_folder, f"{staff_label}_Octave_{octave}"
                )
                os.makedirs(octave_folder, exist_ok=True)

                # Loop over all key signatures
                for key_sig in all_key_signatures:
                    part = stream.Part()
                    # Insert a system layout and the proper clef.
                    part.insert(0, layout.SystemLayout(isNew=True))
                    part.insert(0, getattr(clef, selected_clef)())

                    major_key_obj = key.Key(key_sig, 'major')
                    major_scale_obj = scale.MajorScale(key_sig)

                    scale_measures = create_scale_measures(
                        title_text=f"{instrument_name} - {staff_label} staff - {key_sig} Major Scale",
                        scale_object=major_scale_obj,
                        octave_start=octave,
                        num_octaves=num_octaves
                    )

                    if not scale_measures:
                        continue

                    # Insert the key signature into the first measure.
                    first_m = scale_measures[0]
                    first_m.insert(0, major_key_obj)

                    for m in scale_measures:
                        part.append(m)

                    # Create a score for this key signature and octave.
                    scales_score = stream.Score([part])
                    png_filename = (
                        f"{instrument_name}_{staff_label}_{key_sig}_Major_Scale_Octave_{octave}.png"
                    )
                    png_path = os.path.join(octave_folder, png_filename)
                    
                    # Write out the score as a PNG using MuseScore (via music21).
                    scales_score.write('musicxml.png', fp=png_path)
                    
                    # MuseScore may add a suffix if a file by that name already exists.
                    if not os.path.exists(png_path):
                        base, ext = os.path.splitext(png_path)
                        alt_path = f"{base}-1{ext}"
                        if os.path.exists(alt_path):
                            os.rename(alt_path, png_path)
                            print(f"Renamed {alt_path} to {png_path}")
                        else:
                            print(f"Warning: Neither {png_path} nor {alt_path} exists!")
                    
                    print(f"Created PNG: {png_path}")
                    generated_png_paths.append(png_path)

        # ----------------------------------------------------------------
        # 2. Combine the generated PNG images for this instrument into a PDF
        # ----------------------------------------------------------------
        if not generated_png_paths:
            print(f"No PNGs were generated for instrument: {instrument_name}")
            continue  # Move to the next instrument

        # Sort the PNGs by path for consistent ordering (optional)
        generated_png_paths.sort()

        # Define page settings
        DPI = 300  # Increase for higher resolution output.
        PAGE_WIDTH = 8 * DPI    # e.g. 8 inches wide
        PAGE_HEIGHT = 11 * DPI  # e.g. 11 inches tall
        PADDING = 80            # pixels of padding on all sides
        SPACING = 250           # space between images

        USABLE_WIDTH = PAGE_WIDTH - 2 * PADDING
        USABLE_HEIGHT = PAGE_HEIGHT - 2 * PADDING

        # Load PNG images (with white background if needed)
        scale_images = []
        for path in generated_png_paths:
            try:
                with Image.open(path) as img:
                    # If the image has transparency, paste it on a white background
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

        # Combine images into pages
        pages = []
        current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        current_y = PADDING  # Starting y-position

        for img in scale_images:
            # Resize image if it exceeds the usable width
            if img.width > USABLE_WIDTH:
                ratio = USABLE_WIDTH / img.width
                new_width = USABLE_WIDTH
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)
            
            # If the image doesn't fit on the current page, start a new page
            if current_y + img.height > PAGE_HEIGHT - PADDING:
                pages.append(current_page)
                current_page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
                current_y = PADDING
            
            # Paste the image on the page
            current_page.paste(img, (PADDING, current_y))
            current_y += img.height + SPACING

        # Append the final page if it has content
        if current_y > PADDING:
            pages.append(current_page)

        # Save the combined pages into a multipage PDF for this instrument
        combined_pdf_path = os.path.join(
            instrument_folder,
            f"{instrument_name.replace(' ', '_')}_combined.pdf"
        )
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
            print(f"No pages were created for {instrument_name}.")
