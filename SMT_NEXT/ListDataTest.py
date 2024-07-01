import os
from itertools import islice

def list_first_n_files(directory, n):
    with os.scandir(directory) as entries:
        for entry in islice(entries, n):
            print(entry.name)

directory = 'Data/GrandStaff/grandstaff_dataset'  # Replace with your directory
n = 1000  # Number of files to list

list_first_n_files(directory, n)