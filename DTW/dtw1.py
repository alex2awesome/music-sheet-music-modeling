# AUDIO MIDI COMPARISON

# pip install git+https://github.com/alex2awesome/djitw.git

import argparse
import csv
import librosa
import djitw
import pretty_midi
import scipy
import random
import multiprocessing
import os
import warnings
import functools
import glob
import numpy as np

from multiprocessing.dummy import Pool as ThreadPool

# Audio/CQT parameters
FS = 22050.0
NOTE_START = 36
N_NOTES = 48
HOP_LENGTH = 1024

# DTW parameters
GULLY = 0.96


def compute_cqt(audio_data):
    """Compute the CQT and frame times for some audio data"""
    # Compute CQT
    cqt = librosa.cqt(
        audio_data,
        sr=FS,
        fmin=librosa.midi_to_hz(NOTE_START),
        n_bins=N_NOTES,
        hop_length=HOP_LENGTH,
        tuning=0.0,
    )
    # Compute the time of each frame
    times = librosa.frames_to_time(
        np.arange(cqt.shape[1]), sr=FS, hop_length=HOP_LENGTH
    )
    # Compute log-amplitude
    cqt = librosa.amplitude_to_db(cqt, ref=cqt.max())
    # Normalize and return
    return librosa.util.normalize(cqt, norm=2).T, times


# Had to change this to average chunks for large audio files for cpu reasons
def load_and_run_dtw(input_files):
    def calc_score(_midi_cqt, _audio_cqt):
        # Nearly all high-performing systems used cosine distance
        distance_matrix = scipy.spatial.distance.cdist(
            _midi_cqt, _audio_cqt, "cosine"
        )

        # Get lowest cost path
        p, q, score = djitw.dtw(
            distance_matrix,
            GULLY,  # The gully for all high-performing systems was near 1
            np.median(
                distance_matrix
            ),  # The penalty was also near 1.0*median(distance_matrix)
            inplace=False,
        )
        # Normalize by path length, normalize by distance matrix submatrix within path
        score = score / len(p)
        score = (
            score / distance_matrix[p.min() : p.max(), q.min() : q.max()].mean()
        )

        return score

    # Load in the audio data
    audio_file, midi_file = input_files
    audio_data, _ = librosa.load(audio_file, sr=FS)
    audio_cqt, audio_times = compute_cqt(audio_data)

    midi_object = pretty_midi.PrettyMIDI(midi_file)
    midi_audio = midi_object.fluidsynth(fs=FS)
    midi_cqt, midi_times = compute_cqt(midi_audio)

    # Truncate to save on compute time for long tracks
    MAX_LEN = 10000
    total_len = midi_cqt.shape[0]
    if total_len > MAX_LEN:
        idx = 0
        scores = []
        while idx < total_len:
            scores.append(
                calc_score(
                    _midi_cqt=midi_cqt[idx : idx + MAX_LEN, :],
                    _audio_cqt=audio_cqt[idx : idx + MAX_LEN, :],
                )
            )
            idx += MAX_LEN

        max_score = max(scores)
        avg_score = sum(scores) / len(scores) if scores else 1.0
    else:
        avg_score = calc_score(_midi_cqt=midi_cqt, _audio_cqt=audio_cqt)
        max_score = avg_score

    return midi_file, avg_score, max_score


# I changed wav with mp3 in here :/
def get_matched_files(audio_dir: str, mid_dir: str, audio_file_list: str=None, midi_file_list: str=None):
    # We assume that the files have the same path relative to their directory
    res = []

    if audio_file_list is None and midi_file_list is None:
        audio_file_list = glob.glob(os.path.join(audio_dir, "**/*.mp3"), recursive=True)
        midi_file_list = glob.glob(os.path.join(mid_dir, "**/*.mid"), recursive=True)

    print(f"found {len(audio_file_list)} mp3 files")

    for audio_path in audio_file_list:
        input_rel_path = os.path.relpath(audio_path, audio_dir)
        mid_path = os.path.join(
            mid_dir, os.path.splitext(input_rel_path)[0] + ".mid"
        )
        if os.path.isfile(mid_path):
            res.append((audio_path, mid_path))

    print(f"found {len(res)} matched mp3-midi pairs")

    return res


def abortable_worker(func, *args, **kwargs):
    timeout = kwargs.get("timeout", None)
    p = ThreadPool(1)
    res = p.apply_async(func, args=args)
    try:
        out = res.get(timeout)
        return out
    except multiprocessing.TimeoutError:
        return None, None, None
    except Exception as e:
        print(e)
        return None, None, None
    finally:
        p.close()
        p.join()


def run(
        output_file,
        audio_dir,
        mid_dir,
        audio_file_list=None,
        midi_file_list=None,
        output_mode="a"
):
    """
    Processes audio and MIDI files to compute DTW scores and writes the results to a CSV file.

    This function matches audio and MIDI file pairs
    and calculates DTW scores. Existing results are loaded from the output file to avoid recomputation.
    New results are computed in parallel using a pool of worker processes. The scores are written
    continuously to a CSV file in either 'append' or 'write' mode, depending on the output_mode parameter.

    Args:
        audio_dir (str): The directory containing audio files.
        mid_dir (str): The directory containing MIDI files.
        audio_file_list (list): List of audio files to process. Default is None.
            If none, then all mp3 files in audio_dir will be processed.
        midi_file_list (list): List of MIDI files to process. Default is None.
            If none, then all mid files in mid_dir will be processed.
        output_file (str): The file path where the results CSV will be written.
        output_mode (str): Mode for opening the output file ('a' for append and 'w' for write). Default is 'a'.

    Processes:
        - Loads existing results from the output file if it exists to prevent reprocessing.
        - Matches audio files with MIDI files based on filenames.
        - Skips processing for matches already present in the results.
        - Utilizes multiprocessing to handle time-intensive dynamic time warping computations.
        - Outputs progress updates and writes results incrementally to the output file.
        - Handles potential timeouts in computation and skips entries as necessary.

    Outputs:
        A CSV file at the specified output_file path containing columns for MIDI path, average score,
        and maximum score of the matched files.
    """

    multiprocessing.set_start_method("fork")
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        message="amplitude_to_db was called on complex input",
    )

    matched_files = get_matched_files(
        audio_dir=audio_dir, mid_dir=mid_dir, audio_file_list=audio_file_list, midi_file_list=midi_file_list
    )
    results = {}
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results[row["mid_path"]] = {
                    "avg_score": row["avg_score"],
                    "max_score": row["max_score"],
                }

    matched_files = [
        (audio_path, mid_path)
        for audio_path, mid_path in matched_files
        if mid_path not in results.keys()
    ]
    random.shuffle(matched_files)
    print(f"loaded {len(results)} results")
    print(f"calculating scores for {len(matched_files)}")
    needs_header = True
    if (os.path.exists(output_file) and output_mode == "a"):
        needs_header = False

    score_csv = open(output_file, output_mode)
    csv_writer = csv.writer(score_csv)
    if needs_header:
        csv_writer.writerow(["mid_path", "avg_score", "max_score"])

    with multiprocessing.Pool() as pool:
        abortable_func = functools.partial(
            abortable_worker, load_and_run_dtw, timeout=15000
        )
        scores = pool.imap_unordered(abortable_func, matched_files)

        skipped = 0
        processed = 0
        for mid_path, avg_score, max_score in scores:
            if avg_score is not None and max_score is not None:
                csv_writer.writerow([mid_path, avg_score, max_score])
                score_csv.flush()
            else:
                print(f"timeout")
                skipped += 1

            processed += 1
            if processed % 10 == 0:
                print(f"PROCESSED: {processed}/{len(matched_files)}")
                print(f"***")

        print(f"skipped: {skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--audio_dir", help="dir containing .wav files")
    parser.add_argument("-m", "--mid_dir", help="dir containing .mid files", default=None)
    parser.add_argument("-o", "--output_file", help="path to output file", default=None)
    args = parser.parse_args()
    run(args.output_file, args.audio_dir, args.mid_dir)