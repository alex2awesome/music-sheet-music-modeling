#!/bin/bash

# Convert all .krn files in kern-files to .mid files in std-midi-files
for input_file in kern-files/*.krn; 
do
    if [ -f "$input_file" ]; then  # Check if there are any .krn files
        output_file="midi-files/$(basename "$input_file" .krn).mid"
        hum2mid "$input_file" -o "$output_file"
        echo "Converted $input_file to $output_file"
    else
        echo "No .krn files found in kern-files"
    fi
done
