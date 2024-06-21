# runs yt-dlp to extract mp3 for a given set of links

import subprocess, sys, yt_dlp, json, ast

# commands = sys.argv[1:]
# arg = "https://www.youtube.com/watch?v=20Gb0JcviRA"
# links = str(open("links.txt", "r")).split("\n")
file_path = ""

def parse_args():
    try:
        return sys.argv[1]
    except:
        print("ERROR: file not recognized")
        exit()

def download_from_txt_using_bash(text_file):
    file = open(text_file, "r")
    line = file.readline()
    while line:
        result = subprocess.run(["bash", "script.sh", line], shell=True, capture_output=True)
        print("downloaded audio " + line)
        line = file.readline()

def load_json(json_file):
    links = []
    with open(json_file) as file:
        for line in file:
            try:
                links.append(json.loads(line).get("url"))
                print(json.loads(line).get("url"))
            except:
                print("ERROR: json line fail")
    return links

def load_json(json_file, lines):
    links = []
    with open(json_file) as file:
        for line in file:
            if lines == 0:
                break
            try:
                links.append(json.loads(line).get("url"))
                print(json.loads(line).get("url"))
                lines -= 1
            except:
                print("ERROR: json line fail")
    return links

def download_from_json_using_bash(yt_links, start_index, end_index):
    print("downloading links..")
    for i in range(start_index, end_index):
        result = subprocess.run(["bash", "script.sh", yt_links[i]], shell=True, capture_output=True)
        print("downloaded audio " + yt_links[i])

def main():
    file_path = parse_args()
    links = load_json(file_path, 5)
    download_from_json_using_bash(links, 0, 2)

if __name__ == "__main__":
    main()