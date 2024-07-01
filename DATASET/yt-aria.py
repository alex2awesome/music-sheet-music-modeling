# runs yt-dlp & aria-amt to extract midi for a given set of links
# to set up, run setup.py

import os, sys, subprocess
import json, ast, urllib.parse, argparse
import random
from tqdm.auto import tqdm

MODEL_NAME = "medium-stacked"
CHECKPOINT_NAME = f"piano-medium-stacked-1.0"
START_ID = 0
END_ID = -1
FILE_PATH = ""
MIDI_PATH = "./midi"
MP3_PATH = "./mp3"

def parse_args():
    """
    Parse command line arguments to set the start index, end index, and file path
    for the JSON file containing links.
    """
    global START_ID
    global END_ID
    global FILE_PATH
    global MIDI_PATH
    global MP3_PATH

    parser = argparse.ArgumentParser(
        prog="yt-aria-script",
        description="runs yt-dlp & aria-amt to extract midi for json file of links"
    )
    parser.add_argument("json")
    parser.add_argument("-s", "--start-idx", type=int)
    parser.add_argument("-e", "--end-idx", type=int)
    parser.add_argument("-m", "--midi-dir", type=str)
    parser.add_argument("-t", "--mp3-dir", type=str)
    parser.add_argument("-c", "--seed", type=int)
    args = parser.parse_args()
    
    if args.start_idx is not None:
        START_ID = args.start_idx
    if args.end_idx is not None:
        END_ID = args.end_idx
    if args.midi_dir is not None:
        MIDI_PATH = args.download_dir
    if args.mp3_dir is not None:
        MP3_PATH = args.download_dir
    if args.seed is not None:
        random.seed(args.seed)

    if os.path.isfile(args.json):
        FILE_PATH = str(args.json)
    else:
        print("ERROR: json file not recognized")
        exit()

def get_name(name, suffix="mp3"):
    """
    Generate a file name using the provided name, index, and suffix.

    Parameters:
    name (str): The base name for the file.
    suffix (str): The file extension/suffix (default is "mp3").

    Returns:
    str: The generated file name.
    """
    return (f"audio-{name}.{suffix}")

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

def download_set_from_json(yt_links, start_index, end_index):
    """
    Download a set of audio files from YouTube links using yt-dlp.

    Parameters:
    yt_links (list): A list of YouTube URLs.
    start_index (int): The starting index for the download.
    end_index (int): The ending index for the download.
    """
    print("downloading links..")
    for i in range(start_index, end_index):
        try:
            x = yt_links[i]
        except:
            print("ERROR: requested link is out of range")
            break
        file_name = get_name(urllib.parse.quote(yt_links[i], safe='', encoding=None, errors=None))
        os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {yt_links[i]} -o {MP3_PATH}/{file_name}")
        print("downloaded audio for video: " + yt_links[i] + " as " + file_name)

def download_from_json(yt_links, i, name=None):
    """
    Download a single audio file from a YouTube link using yt-dlp.

    Parameters:
    yt_links (list): A list of YouTube URLs.
    i (int): The index of the link to download.
    name (str, optional): The custom name for the file. Defaults to None.

    Returns:
    bool: True if the download is successful, False otherwise.
    """
    if name is None:
        name = i
    print("downloading links..")
    try:
        x = yt_links[i]
    except:
        print("ERROR: requested link is out of range")
        return False
    file_name = get_name(name)
    path = f"{MP3_PATH}/{file_name}"
    if not os.path.isfile(path):
        os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {yt_links[i]} -o {path}")
        print("downloaded audio for video: " + yt_links[i])
    else:
        print("audio already downloaded for video: " + yt_links[i] + " as " + file_name)
    return True

def download_link(link, name):
    """
    Download a single audio file from a YouTube link using yt-dlp.

    Parameters:
    link (str): The YouTube URL.
    name (str): The custom name for the file.

    Returns:
    bool: True if the download is successful, False otherwise.
    """
    print("downloading links..")
    os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {link} -o {MP3_PATH}/{get_name(name)}")
    print("downloaded audio for video: " + link)
    return True

def aria_amt_set_up():
    """
    Download aria-amt model weights if needed.
    """
    if not os.path.isfile(f"{CHECKPOINT_NAME}.safetensors"):
        # NOTE: uncomment or comment depending on system
        os.system(f"wget https://storage.googleapis.com/aria-checkpoints/amt/{CHECKPOINT_NAME}.safetensors")
        # subprocess.run(["powershell", f"wget https://storage.googleapis.com/aria-checkpoints/amt/{CHECKPOINT_NAME}.safetensors"])
    else:
        print(f"Checkpoint already exists at {CHECKPOINT_NAME} - skipping download")


def run_aria_amt(path, directory="."):
    """
    Run aria-amt to transcribe audio files to MIDI.

    Parameters:
    path (str): The path to the audio file.
    directory (str): The directory to save the MIDI files (default is current directory).
    """
    os.system(
        f"aria-amt transcribe {MODEL_NAME} {CHECKPOINT_NAME}.safetensors -load_path=\"{MP3_PATH}/{path}\" -save_dir=\"{directory}\" -bs=1"
    )

def remove_mp3(name):
    """
    Remove the downloaded MP3 file.

    Parameters:
    name (str): The base name for the file.
    """
    file_name = get_name(name)
    path = MP3_PATH + "/" + file_name
    if (os.path.isfile(path)):
        os.system(f"rm {path}")
        print(f"{path} removed")
    else:
        print(f"ERROR: mp3 file not found, could not remove")

def get_link_from_file(file_name):
    """
    Extract the original URL from the downloaded file name.

    Parameters:
    file_name (str): The name of the downloaded file.

    Returns:
    str: The original URL.
    """
    s = file_name.split("-")
    s = s[2].split(".")
    print(s[0])
    return urllib.parse.unquote_plus(s[0])

def main():
    global START_ID
    global END_ID

    parse_args()

    BATCH = 100
    file_comparison = {}
    no_good = []

    if END_ID == -1:
        links = load_json(FILE_PATH)
        END_ID = len(links)
    else:
        links = load_set_from_json(FILE_PATH, START_ID, END_ID)
        random.shuffle(links)

    aria_amt_set_up()

    if not os.path.isfile(f"{CHECKPOINT_NAME}.safetensors"):
        print(f"{CHECKPOINT_NAME}.safetensors did not install")
        exit()
    
    if not os.path.isdir(MP3_PATH):
        os.system("mkdir " + MP3_PATH)
    
    if not os.path.isdir(MIDI_PATH):
        os.system("mkdir " + MIDI_PATH)

    for i in tqdm(range(START_ID, END_ID)):
        try:
            name = urllib.parse.quote(links[i], safe='', encoding=None, errors=None)
            print(f"downloading audio/midi for {name}..")
            if not os.path.isfile(f"{MIDI_PATH}/{get_name(name, "mid")}"):
                if download_from_json(links, i, name):
                    run_aria_amt(get_name(name, "mp3"), MIDI_PATH)
                print(f"midi #{i} {get_name(name)} downloaded successfully") # in case program crashes, can run from where last left off
                # file_comparison[name] = {CALCULATE DIFF BETWEEN MP3 & MIDI}
        except Exception as e:
            print(f"ERROR {e}: failed to download audio/midi {links[i]}")

        if len(file_comparison) >= BATCH:
            for file in file_comparison.keys():
                # if file_comparison[file] < BENCHMARK:
                    # remove mid file?
                remove_mp3(get_name(file))
            file_comparison = {}

if __name__ == "__main__":
    main()
