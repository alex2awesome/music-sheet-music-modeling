# runs yt-dlp & aria-amt to extract midi for a given set of links
# to set up, run setup.py

import os, sys, subprocess
import json, ast, urllib.parse, argparse
import random
from tqdm.auto import tqdm
from dtw import run as run_dtw



MODEL_NAME = "medium-stacked"
CHECKPOINT_NAME = f"piano-medium-stacked-1.0"


def parse_args():
    """
    Parse command line arguments to set the start index, end index, and file path
    for the JSON file containing links.
    """
    parser = argparse.ArgumentParser(
        prog="yt-aria-script",
        description="runs yt-dlp & aria-amt to extract midi for json file of links"
    )
    parser.add_argument("--input_json", type=str, required=True)
    parser.add_argument("-s", "--start-idx", type=int, default=0)
    parser.add_argument("-e", "--end-idx", type=int, default=-1)
    parser.add_argument("-m", "--midi-dir", type=str, default="midi")
    parser.add_argument("-t", "--mp3-dir", type=str, default="mp3")
    parser.add_argument("--dtw-file", type=str, default="dtw-scores.csv")
    parser.add_argument("-c", "--seed", type=int)
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    return args


def get_name(name, path, suffix="mp3"):
    """
    Generate a file name using the provided name, index, and suffix.

    Parameters:
    name (str): The base name for the file.
    suffix (str): The file extension/suffix (default is "mp3").

    Returns:
    str: The generated file name.
    """
    return os.path.join(path, f"audio-{name}.{suffix}")


def load_json(json_file):
    """
    Load links from a JSON file.

    Parameters:
    json_file (str): The path to the JSON file.

    Returns:
    list: A list of URLs extracted from the JSON file.
    """    
    links = []
    with open(json_file) as file:
        for line in file:
            try:
                link = json.loads(line).get("url")
                links.append(link)
            except:
                print("ERROR: json line load fail")
    return links


def load_set_from_json(json_file, start_index, end_index):
    """
    Load a subset of links from a JSON file based on the provided indices.

    Parameters:
    json_file (str): The path to the JSON file.
    start_index (int): The starting index.
    end_index (int): The ending index.

    Returns:
    list: A list of URLs extracted from the JSON file within the specified range.
    """
    links = []
    i = 0
    with open(json_file) as file:
        for line in file: # will end if reached end of json
            if i >= end_index:
                break
            elif i >= start_index:
                try:
                    link = json.loads(line).get("url")
                    links.append(link)
                    print(f"loaded: {link}")
                    i += 1
                except:
                    print("ERROR: json line load fail")
    return links


def download_using_ytdl(yt_link, mp3_output_fp):
    """
    Download a single audio file from a YouTube link using yt-dlp.

    Parameters:
    yt_links (list): A list of YouTube URLs.
    i (int): The index of the link to download.
    name (str, optional): The custom name for the file. Defaults to None.

    Returns:
    bool: True if the download is successful, False otherwise.
    """
    if not os.path.isfile(mp3_output_fp):
        os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {yt_link} -o {mp3_output_fp}")
        print("downloaded audio for video: " + yt_link)
    else:
        print("audio already downloaded for video: " + yt_link + " as " + mp3_output_fp)
    return True



def aria_amt_set_up():
    """
    Download aria-amt model weights if needed.
    """
    if not os.path.isfile(f"{CHECKPOINT_NAME}.safetensors"):
        # NOTE: uncomment or comment depending on system
        os.system(f"wget https://storage.googleapis.com/aria-checkpoints/amt/{CHECKPOINT_NAME}.safetensors")
        # subprocess.run([
        #       "powershell",
        #       f"wget https://storage.googleapis.com/aria-checkpoints/amt/{CHECKPOINT_NAME}.safetensors"
        # ])
    else:
        print(f"Checkpoint already exists at {CHECKPOINT_NAME} - skipping download")


def run_aria_amt(mp3_fp, directory="."):
    """
    Run aria-amt to transcribe audio files to MIDI.

    Parameters:
    path (str): The path to the audio file.
    directory (str): The directory to save the MIDI files (default is current directory).
    """
    os.system(
        f"aria-amt transcribe {MODEL_NAME} {CHECKPOINT_NAME}.safetensors -load_path=\"{mp3_fp}\" -save_dir=\"{directory}\" -bs=1"
    )


def remove_mp3(mp3_fp):
    """
    Remove the downloaded MP3 file.

    Parameters:
    name (str): The base name for the file.
    """
    if (os.path.isfile(mp3_fp)):
        os.system(f"rm {mp3_fp}")
        print(f"{mp3_fp} removed")
    else:
        print(f"ERROR: mp3 file not found, could not remove")


def main():
    args = parse_args()

    if args.end_idx < 0:
        links = load_json(args.input_json)
        args.end_idx = len(links)
    else:
        links = load_set_from_json(args.input_json, args.start_idx, args.end_idx)

    random.shuffle(links)
    aria_amt_set_up()

    if not os.path.isfile(f"{CHECKPOINT_NAME}.safetensors"):
        print(f"{CHECKPOINT_NAME}.safetensors did not install")
        exit()
    
    if not os.path.isdir(args.mp3_dir):
        os.system("mkdir " + args.mp3_dir)
    
    if not os.path.isdir(args.mid_dir):
        os.system("mkdir " + args.mid_dir)

    BATCH = 2
    buffer_audio_files = []
    buffer_midi_files = []
    for i in tqdm(range(args.start_idx, args.end_idx)):
        try:
            name = urllib.parse.quote(links[i], safe='', encoding=None, errors=None)
            mid_fn = get_name(name, args.mid_path, "mid")
            mp3_fn = get_name(name, args.mp3_path, "mp3")
            if not os.path.isfile(mid_fn):
                if download_using_ytdl(links[i], mp3_fn):
                    run_aria_amt(mp3_fn, args.mid_dir)
                    if os.path.isfile(mid_fn) and os.path.isfile(mp3_fn):
                        buffer_audio_files.append(mp3_fn)
                        buffer_midi_files.append(mid_fn)
            if len(buffer_audio_files) >= BATCH:
                run_dtw(args.dtw_file, args.mp3_dir, args.mid_dir, buffer_audio_files, buffer_midi_files)

                list(map(remove_mp3, buffer_audio_files))
                buffer_audio_files = []
                buffer_midi_files = []

        except Exception as e:
            print(f"ERROR {e}: failed to download audio/midi {links[i]}")


if __name__ == "__main__":
    main()
