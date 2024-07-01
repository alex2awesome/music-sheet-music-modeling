#!/usr/bin/bash

# echo "help on yt-dlp"
# command yt-dlp --help

youtube_link=$(echo "https://www.youtube.com/watch?v=c6GyiGMM9pE"$1)
save_path=$(echo "C:\Users\ssmoo\personal\berkeley\research\sheet-music-recognition\scripting"$1)

command yt-dlp --extract-audio --audio-format mp3 --no-playlist --audio-quality 0 $1

# echo $save_file