# set up script for yt-aria.py

import os

MODEL_NAME = "medium-stacked"
CHECKPOINT_NAME = f"piano-medium-stacked-1.0"

def yt_dlp_set_up():
    """
    Prompt the user to download and install yt-dlp if needed.
    """    
    if input("yt-dlp download? (y/n) ").lower() == "y":
        try:
            os.system("pip uninstall yt-dlp")
            os.system("pip install yt-dlp")
        except:
            print("ERROR: yt-dlp install failed")
            exit()

def aria_amt_set_up():
    """
    Prompt the user to install aria-amt and download model weights if needed.
    """
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

if __name__ == "__main__":
    aria_amt_set_up()
    yt_dlp_set_up()