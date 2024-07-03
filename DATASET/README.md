#  to run
python yt-aria.py \<json file name\>


# notes for debugging:
+ for yt-dlp, need to install ffmpeg onto system to get mp3 file format
+ numpy needs to be a version below 2.0 for aria, python needs to be 3.11
+ if running on a windows machine, wget only works in powershell; uncomment/comment lines in aria_amt_set_up() accordingly