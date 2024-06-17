import os

def delete_files_with_text(directory, text):
    for filename in os.listdir(directory):
        if text in filename:
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")

# Set the current directory
directory = os.getcwd()  # This sets the directory to the current directory
text = 'grandstaff_dataset'

delete_files_with_text(directory, text)