#!/bin/bash

# List of common installation directories for Anaconda/Miniconda
declare -a check_dirs=("$HOME/anaconda3" "$HOME/miniconda3" "/usr/local/anaconda3"
"/usr/local/miniconda3")

# Flag to indicate if found 
found=0

for dir in "${check_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "Found Anaconda/Miniconda installation at $dir"
        found=1
        break
    fi
done

if [ $found -eq 0 ]; then
    echo "Anaconda/Miniconda is not installed or not in the common directories."
fi
