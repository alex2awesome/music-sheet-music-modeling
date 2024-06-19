import os
import random
import math

def getFiles(directory):
    krn_files = []
    counter = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.krn'):
                krn_files.append(os.path.relpath(os.path.join(root, file), directory))

    return krn_files

def split_files_to_datasets(directory):
    # Get all .krn file paths

    krn_files = getFiles(directory)
    print(krn_files)
    # Shuffle the file list
    random.shuffle(krn_files)
    # krn_files = krn_files[:1000]
    # Calculate split sizes
    total_files =  len(krn_files)
    test_size = math.ceil(total_files * 0.10)
    validation_size = math.ceil(total_files * 0.10)
    train_size = total_files - test_size - validation_size

    # Split the file list
    train_files = krn_files[:train_size]
    validation_files = krn_files[train_size:train_size + validation_size]
    test_files = krn_files[train_size + validation_size:]

    # Create partition directory if it doesn't exist
    partition_dir = os.path.join(directory, 'partition')
    os.makedirs(partition_dir, exist_ok=True)

    # Write to text files
    with open(os.path.join(partition_dir, 'train.txt'), 'w') as train_file:
        for file_path in train_files:
            train_file.write(file_path + '\n')

    with open(os.path.join(partition_dir, 'validation.txt'), 'w') as validation_file:
        for file_path in validation_files:
            validation_file.write(file_path + '\n')

    with open(os.path.join(partition_dir, 'test.txt'), 'w') as test_file:
        for file_path in test_files:
            test_file.write(file_path + '\n')


# Usage example
split_files_to_datasets('Data/GrandStaff')
