import os
import subprocess

with open('widths.txt', 'w') as outfile:
    # List all files in the current directory
    for filename in os.listdir('.'):
        # Check if the file is a PNG (case-insensitive)
        if filename.lower().endswith('.jpg'):
            # Get the filename without the extension
            name_without_ext = os.path.splitext(filename)[0]
            try:
                # Use ImageMagick's identify command to get the width
                result = subprocess.check_output(['identify', '-format', '%w', filename])
                width = result.decode('utf-8')
                # Write to widths.txt in the specified format
                outfile.write(f"{name_without_ext}: {width}\n")
            except subprocess.CalledProcessError as e:
                print(f"Error processing {filename}: {e}")
