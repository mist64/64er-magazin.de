#!/bin/bash

# This script does not do multiple files in parallels, because
# * It's completely memory-bound because rotating a huge file
#   is catastrophic for the cache.
# * Each instance of magick uses about 20 GB of RAM, so multiple
#   magick processes would easily overflow a typical machine's
#   RAM.
# In short, I tried, and two processes in parallel were about
# the same speed on a 2019 MacBook Pro.

# Get the current directory name
dir_name=${PWD##*/}

# Remove '-scan' suffix if present
dir_name=${dir_name%-scan}

# Output directories
dir_rotated="../${dir_name}-png"
dir_thumb="${dir_rotated}/thumb"

# Create output directories if they don't exist
mkdir -p "$dir_rotated"
mkdir -p "$dir_thumb"

# Process each TIFF file
for file in *.tiff; do
    output_rotated="$dir_rotated/${file%.tiff}.png"
    output_scaled="$dir_thumb/${file%.tiff}.png"

    # Check if both output files already exist
    if [ -f "$output_rotated" ] && [ -f "$output_scaled" ]; then
        echo "Output exists, skipping $file"
        continue
    fi

    echo "Processing $file"

    # Use ImageMagick to process the image once and output two files
    magick "$file" -alpha off -units PixelsPerInch -density 2400 \
        \( -clone 0 -rotate 270 +write "$output_rotated" \) \
        \( -clone 0 -scale 6.25% -units PixelsPerInch -density 150 -rotate 270 +write "$output_scaled" \) \
        null:
done
