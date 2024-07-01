# runs yt-dlp & aria-amt to extract midi for a given set of links

import os, sys, subprocess
import json, ast, urllib, argparse

MODEL_NAME = "medium-stacked"
CHECKPOINT_NAME = f"piano-medium-stacked-1.0"
START_ID = 0
END_ID = -1
FILE_PATH = ""

def parse_args():
    global START_ID
    global END_ID
    global FILE_PATH 

    parser = argparse.ArgumentParser(prog="yt-aria-script",
                                     description="runs yt-dlp & aria-amt to extract midi for json file of links")
    parser.add_argument("json")
    parser.add_argument("-s", "--start-idx", type=int)
    parser.add_argument("-e", "--end-idx", type=int)
    args = parser.parse_args()
    
    if args.start_idx is not None:
        START_ID = args.start_idx
    if args.end_idx is not None:
        END_ID = args.end_idx

    if os.path.isfile(args.json):
        FILE_PATH = str(args.json)
    else:
        print("ERROR: json file not recognized")
        exit()

def get_name(name, i, suffix="mp3"):
    return (f"audio-{i}-{name}.{suffix}")

def yt_dlp_set_up():
    if input("yt-dlp download? (y/n) ").lower() == "y":
        try:
            os.system("pip uninstall yt-dlp")
            os.system("pip install yt-dlp")
        except:
            print("ERROR: yt-dlp install failed")
            exit()

def load_json(json_file):
    links = []
    with open(json_file) as file:
        for line in file:
            try:
                link = json.loads(line).get("url")
                links.append(link)
                print(link)
            except:
                print("ERROR: json line load fail")
    return links

def load_set_from_json(json_file, start_index, end_index):
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
                    print(f"loaded #{i}: {link}")
                    i += 1
                except:
                    print("ERROR: json line load fail")
    return links

def download_set_from_json(yt_links, start_index, end_index):
    print("downloading links..")
    for i in range(start_index, end_index):
        try:
            x = yt_links[i]
        except:
            print("ERROR: requested link is out of range")
            break
        name = get_name(urllib.parse.quote(yt_links[i], safe='', encoding=None, errors=None), i, "mp3")
        os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {yt_links[i]} -o {name}")
        print("downloaded audio for video: " + yt_links[i] + " as " + file_name)

def download_from_json(yt_links, i, name=None):
    if name is None:
        name = i
    print("downloading links..")
    try:
        x = yt_links[i]
    except:
        print("ERROR: requested link is out of range")
        return False
    file_name = get_name(name, i)
    if not os.path.isfile(file_name):
        os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {yt_links[i]} -o {file_name}")
        print("downloaded audio for video: " + yt_links[i])
    else:
        print("audio already downloaded for video: " + yt_links[i] + " as " + file_name)
    return True

def download_link(link, name, i="X"):
    print("downloading links..")
    os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {link} -o {get_name(name, i)}")
    print("downloaded audio for video: " + link)
    return True

def aria_amt_set_up():
    install = input("install aria-amt? (y/n) ")
    if (install.lower() == "y"):
        os.system("pip uninstall aria-amt")
        os.system("pip install git+https://github.com/EleutherAI/aria-amt.git")

    install = input("download model weights? (y/n) ")
    if (install.lower() == "y"):
        if not os.path.isfile(f"{CHECKPOINT_NAME}.safetensors"):
            # NOTE: uncomment or comment depending on system
            os.system(f"wget https://storage.googleapis.com/aria-checkpoints/amt/{CHECKPOINT_NAME}.safetensors")
            # subprocess.run(["powershell", f"wget https://storage.googleapis.com/aria-checkpoints/amt/{CHECKPOINT_NAME}.safetensors"])
        else:
            print(f"Checkpoint already exists at {CHECKPOINT_NAME} - skipping download")

def run_aria_amt(path, directory="."):
    os.system(f"aria-amt transcribe {MODEL_NAME} {CHECKPOINT_NAME}.safetensors -load_path=\"{path}\" -save_dir=\"{directory}\" -bs=1")

def remove_mp3(name, i):
    file_name = get_name(name, i)
    if (os.path.isfile(file_name)):
        os.system(f"rm {file_name}")
        print(f"{file_name} removed")
    else:
        print(f"ERROR: mp3 file not found, could not remove")

def get_link_from_file(file_name):
    s = file_name.split("-")
    s = s[2].split(".")
    print(s[0])
    return urllib.parse.unquote_plus(s[0])

def main():
    global START_ID
    global END_ID
    global FILE_PATH 

    parse_args()

    if END_ID == -1:
        links = load_json(FILE_PATH)
        END_ID = len(links)
    else:
        links = load_set_from_json(FILE_PATH, START_ID, END_ID)

    aria_amt_set_up()
    yt_dlp_set_up()

    if not os.path.isfile(f"{CHECKPOINT_NAME}.safetensors"):
        print(f"{CHECKPOINT_NAME}.safetensors did not install")
        exit()
    
    if not os.path.isdir("midi"):
        os.system("mkdir midi")

    for i in range(START_ID, END_ID):
        try:
            name = urllib.parse.quote(links[i], safe='', encoding=None, errors=None)
            print(name)
            if not os.path.isfile(get_name(name, i, "mid")):
                if download_from_json(links, i, name):
                    run_aria_amt(get_name(name, i, "mp3"), "./midi")
                print(f"midi #{i} downloaded successfully") # in case program crashes, can run from where last left off
            remove_mp3(name, i)
        except:
            print(f"ERROR: failed to download audio/midi #{i}")

if __name__ == "__main__":
    main()