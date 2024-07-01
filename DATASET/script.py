# WORKING COPY, do not run

# runs yt-dlp to extract mp3 for a given set of links
# NOTE: need to download ffmpeg separately for yt-dlp to download as mp3 in some cases
# NOTE: if using Windows system and wget is not installed then see aria_amt_set_up() / for ref: https://learn.microsoft.com/en-us/answers/questions/1167673/how-to-use-wget-command-on-windows-(for-recursive
# to run: python script.py <json file name>

import subprocess
import os, sys
import json, ast

FILE_PATH = ""
MODEL_NAME = "medium-stacked"
CHECKPOINT_NAME = f"piano-medium-stacked-1.0"

def parse_args():
    try:
        return sys.argv[1]
    except:
        print("ERROR: file not recognized")
        exit()

def yt_dlp_set_up():
    try:
        os.system("pip install yt-dlp")
    except:
        print("yt-dlp install failed")
        exit()

def download_from_txt_using_bash(text_file):
    file = open(text_file, "r")
    line = file.readline()
    while line:
        result = subprocess.run(["bash", "yt-dlp.sh", line], shell=True, capture_output=True)
        print("downloaded audio " + line)
        line = file.readline()

def load_json(json_file):
    links = []
    with open(json_file) as file:
        for line in file:
            try:
                link = json.loads(line).get("url")
                print(link)
            except:
                print("ERROR: json line fail")
    return links

# def load_json(json_file, path="yt-links.txt"):
#     links = []
#     # if os.path.isfile(path):
#     #     run_again = input("rewrite links text file? (y/n)")
#     #     if (run_again.lower() != "y"):
#     #         file = open(path)
#     #         links = file.readlines()
#     #         file.close()
#     #         return links
#     try:
#         txt_file = open(path, "x")
#     except:
#         print("rewriting file...")
#         txt_file = open(path, "w")
#     with open(json_file) as file:
#         for line in file:
#             try:
#                 link = json.loads(line).get("url")
#                 links.append(link + "\n")
#                 txt_file.write(link)
#                 print(link)
#             except:
#                 print("ERROR: json line fail")
#     return links

def load_json_partial(json_file, start, end):
    links = []
    i = 0
    with open(json_file) as file:
        for line in file:
            if i == end:
                break
            elif i >= start:
                try:
                    links.append(json.loads(line).get("url"))
                    print(json.loads(line).get("url"))
                except:
                    print("ERROR: json line fail")
    return links

def download_from_json_using_bash(yt_links, start_index, end_index):
    print("downloading links..")
    for i in range(start_index, end_index):
        result = subprocess.run(["bash", "script.sh", yt_links[i]], shell=True, capture_output=True)
        print("downloaded audio " + yt_links[i])

def download_set_from_json(yt_links, start_index, end_index):
    print("downloading links..")
    for i in range(start_index, end_index):
        try:
            x = yt_links[i]
        except:
            print("out of range")
            break
        os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {yt_links[i]} -o audio-{i}.mp3")
        print("downloaded audio for video: " + yt_links[i])

def download_from_json(yt_links, i):
    print("downloading links..")
    try:
        x = yt_links[i]
    except:
        print("out of range")
        return
    if (os.path.isfile(f"audio-{i}.mpe")):
        os.system(f"yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 {yt_links[i]} -o audio-{i}.mp3")
    else:
        print("already downloaded: " + yt_links[i])
    print("downloaded audio for video: " + yt_links[i])

def aria_amt_set_up():
    install = input("install aria-amt? (y/n) ")
    if (install.lower() == "y"):
        os.system("pip uninstall aria-amt")
        os.system("pip install git+https://github.com/EleutherAI/aria-amt.git")

    install = input("download model weights? (y/n) ")
    if (install.lower() == "y"):
        if not os.path.isfile(f"{CHECKPOINT_NAME}.safetensors"):
            # NOTE: uncomment or comment depending on system
            # os.system(f"wget https://storage.googleapis.com/aria-checkpoints/amt/{CHECKPOINT_NAME}.safetensors")
            subprocess.run(["powershell", f"wget https://storage.googleapis.com/aria-checkpoints/amt/{CHECKPOINT_NAME}.safetensors"])
        else:
            print(f"Checkpoint already exists at {CHECKPOINT_NAME} - skipping download")

def run_aria_amt(path, directory="."):
    os.system(f"aria-amt transcribe {MODEL_NAME} {CHECKPOINT_NAME}.safetensors -load_path=\"{path}\" -save_dir=\"{directory}\" -bs=1")

def remove_file(i):
    os.system(f"rm audio-{i}.mp3")

def download_all(START, END):
    FILE_PATH = parse_args()
    links = []

    if END == -1:
        links = load_json(FILE_PATH)
        print(links)
        END = len(links)
    else:
        links = load_json_partial(FILE_PATH, START, END)
    
    if not os.path.isfile(f"{CHECKPOINT_NAME}.safetensors"):
        print(f"{CHECKPOINT_NAME}.safetensors did not install")
        exit()
    if not os.path.isdir("midi"):
        os.system("mkdir midi")

    for i in range(START, END):
        try:
            download_from_json(links, i)
            run_aria_amt(f"audio-{i}.mp3")
            print(f"midi downloaded successfully #{i}")
        except:
            print("error occurred while downloading")

def main():
    START = 0
    END = -1

    breakpoint()

    if (int(sys.argv[3]) == 0):
        aria_amt_set_up()
        yt_dlp_set_up()

    if (int(sys.argv[2]) == 0):
        START = int(input("START: "))
        END = int(input("END: "))
    
    download_all(START, END)

if __name__ == "__main__":
    main()