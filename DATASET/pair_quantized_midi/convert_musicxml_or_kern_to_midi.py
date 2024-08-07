import argparse
import os
from music21 import converter, midi
import subprocess

def get_filepath(input_file, input_dir, output_dir):
    # Construct relative path from input_dir to maintain directory structure
    relative_path = os.path.relpath(os.path.dirname(input_file), input_dir)
    specific_output_dir = os.path.join(output_dir, relative_path)

    # Ensure the specific output directory exists
    os.makedirs(specific_output_dir, exist_ok=True)

    # Get the base name for the output file
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    midi_path = os.path.join(specific_output_dir, f"{file_name}.mid")
    return midi_path

def process_humdrum_file(input_file, input_dir, output_dir, verbose=False):
    midi_path = get_filepath(input_file, input_dir, output_dir)
    try:
        if verbose:
            print(f"processing: {input_file}")
        # run the following shell command: hum2mid "$input_file" -o "$output_file"
        subprocess.run(["hum2mid", input_file, "-o", midi_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_file}: {e}")

def process_mxl_file(input_file, input_dir, output_dir, verbose=False):
    try:
        if verbose:
            print(f"processing: {input_file}")
        # Load the MusicXML file
        midi_path = get_filepath(input_file, input_dir, output_dir)
        score = converter.parse(input_file)
        # Initialize a MIDI stream for combining parts
        combined_midi = midi.MidiFile()
        # Add each part to the combined MIDI stream
        for part in score.parts:
            mf = midi.translate.streamToMidiFile(part)
            for track in mf.tracks:
                combined_midi.tracks.append(track)

        # Write the combined MIDI stream to a file
        combined_midi.open(midi_path, 'wb')
        combined_midi.write()
        combined_midi.close()

    except Exception as e:
        print(f"Error processing {input_file}: {e}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process MusicXML files and convert to MIDI.")
    parser.add_argument("--input_dir", type=str, help="Directory containing MusicXML files")
    parser.add_argument("--output_dir", type=str, help="Directory to save MIDI files")
    parser.add_argument("--input_format", type=str, default="mxl", help="Input file format (mxl or krn)")
    parser.add_argument("--verbose", action="store_true", help="enable prints")

    args = parser.parse_args()

    input_dir_abs = os.path.abspath(args.input_dir)
    output_dir_abs = os.path.abspath(args.output_dir)

    if args.verbose:
        print(f"Input Directory: {input_dir_abs}")
        print(f"Output Directory: {output_dir_abs}")

    supported_extensions = (".musicxml", ".xml", ".mxl", ".krn")
    for root, _, files in os.walk(input_dir_abs):
        if output_dir_abs.startswith(root):
            continue

        for file in files:
            if file.lower().endswith(supported_extensions):
                input_file = os.path.join(root, file)
                if args.input_format == "krn":
                    process_humdrum_file(input_file, input_dir_abs, output_dir_abs, args.verbose)
                else:
                    process_mxl_file(input_file, input_dir_abs, output_dir_abs, args.verbose)