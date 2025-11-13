#!/bin/bash

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <d64_file1> [d64_file2 ...]"
    echo "Example: $0 S8506A.D64 S8506B.D64"
    echo "Output: prg/ directory and prg.html file"
    exit 1
fi

# All arguments are D64 files - convert to absolute paths
D64_FILES=()
for file in "$@"; do
    # Convert to absolute path
    if [[ "$file" = /* ]]; then
        # Already absolute
        D64_FILES+=("$file")
    else
        # Make it absolute
        D64_FILES+=("$(cd "$(dirname "$file")" && pwd)/$(basename "$file")")
    fi
done

# Hardcoded output directory
OUTPUT_DIR="prg"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Create del subdirectory for deleted files
mkdir -p "$OUTPUT_DIR/del"

# Process each D64 file
for D64_FILE in "${D64_FILES[@]}"; do
    echo "Processing $D64_FILE..." >&2

    # Create temp directory
    TMP_DIR="$OUTPUT_DIR/tmp"
    mkdir -p "$TMP_DIR"

    # Extract all files from D64 into tmp
    echo "  Extracting files..." >&2
    cd "$TMP_DIR"
    c1541 "$D64_FILE" -extract >/dev/null 2>&1

    # Add .prg suffix to all extracted files in tmp
    echo "  Adding .prg suffix to extracted files..." >&2
    for file in *; do
        [ -f "$file" ] || continue

        # Add .prg if not already present
        if [[ ! "$file" =~ \.prg$ ]]; then
            mv "$file" "$file.prg"
        fi
    done

    # Process each .prg file with petcat (while in tmp)
    echo "  Processing files with petcat..." >&2
    for prgfile in *.prg; do
        [ -f "$prgfile" ] || continue

        txtfile="${prgfile%.prg}.txt"

        # Run petcat
        petcat "$prgfile" > "$txtfile" 2>&1

        # Read the output
        header=""
        content_lines=()
        in_header=true

        while IFS= read -r line; do
            # Skip blank lines
            [[ -z "$line" ]] && continue

            if [ "$in_header" = true ]; then
                # First non-blank line is the header
                header="$line"
                in_header=false
            else
                # These are content lines
                content_lines+=("$line")
            fi
        done < "$txtfile"

        keep_txt=true

        # Check if header has load address
        if [[ ! $header =~ ==([0-9a-fA-F]+)== ]]; then
            # No load address found, not a valid BASIC program
            keep_txt=false
        else
            # Check if load address ends in 01
            hex_addr="${BASH_REMATCH[1]}"
            if [[ ! $hex_addr =~ 01$ ]]; then
                # Doesn't end in 01, not a BASIC program
                keep_txt=false
            fi
        fi

        # Check if less than 3 content lines AND contains 'sys' followed by number
        if [ "$keep_txt" = true ] && [ ${#content_lines[@]} -lt 3 ]; then
            for line in "${content_lines[@]}"; do
                if [[ $line =~ sys[[:space:]]*[0-9]+ ]]; then
                    # Found sys with number, not a real BASIC program
                    keep_txt=false
                    break
                fi
            done
        fi

        # Keep txt or prg, move the other to del
        if [ "$keep_txt" = true ]; then
            mv "$prgfile" "../del/"
            echo "    Kept: $(basename "$txtfile")" >&2
        else
            mv "$txtfile" "../del/"
            echo "    Kept: $(basename "$prgfile")" >&2
        fi
    done

    # Move remaining files (the kept ones) to parent directory
    mv * .. 2>/dev/null
    cd ../..

    # Clean up tmp directory
    rm -rf "$TMP_DIR"
done

echo "Generating HTML..." >&2

# Generate HTML for all D64 files and write to prg.html
{
    for D64_FILE in "${D64_FILES[@]}"; do
        # Add comment with D64 filename
        echo ""
        echo "<!-- $D64_FILE -->"
        echo ""

        # Get the directory listing from c1541
        c1541 "$D64_FILE" -list 2>&1 | grep '"' | while IFS= read -r line; do
            # Extract filename and type from the listing
            if [[ $line =~ \"([^\"]+)\"[[:space:]]+(prg|del|seq|usr|rel) ]]; then
                filename="${BASH_REMATCH[1]}"
                filetype="${BASH_REMATCH[2]}"

                # Convert "/" to "_" for filesystem
                filename_alt="${filename//\//_}"

                found=false

                # Check for .txt file (BASIC listing)
                if [ -f "${OUTPUT_DIR}/${filename_alt}.txt" ]; then
                    echo "<figure><pre data-filename=\"${filename}\" data-name=\"XXXXXXXXXXXX\"></pre><figcaption>YYYYYYYYYYYYY</figcaption></figure>"
                    found=true
                fi

                # Check for .prg file (MSE listing & binary download)
                if [ -f "${OUTPUT_DIR}/${filename_alt}.prg" ]; then
                    echo "<figure><pre data-filename=\"${filename_alt}.prg\" data-name=\"XXXXXXXXXXXX\" data-mse=mse1></pre><figcaption>YYYYYYYYYYYYY</figcaption></figure>"
                    echo "<div class=\"binary_download\" data-filename=\"${filename_alt}.prg\" data-name=\"XXXXXXXXXXXXXXX\"></div>"
                    found=true
                fi

                # If no file was found, add HTML comment
                if [ "$found" = false ]; then
                    echo ""
                    echo "<!-- ${line} -->"
                    echo ""
                fi
            fi
        done
    done
} > prg.html

echo "Done! Output written to prg.html" >&2
