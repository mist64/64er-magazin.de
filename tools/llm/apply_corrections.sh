#!/bin/bash

# Check arguments
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <corrections_file> <target_file>"
    echo ""
    echo "Apply corrections from a pipe-separated corrections file to a target markdown file."
    echo "Skips lines that contain two or more '|' characters (indicating errors or multiple corrections)."
    echo ""
    echo "Arguments:"
    echo "  corrections_file   File containing corrections in format 'original|correction'"
    echo "  target_file        Markdown file to apply corrections to"
    echo ""
    echo "Example:"
    echo "  $0 corrections.txt document.md"
    exit 1
fi

CORRECTIONS_FILE="$1"
TARGET_FILE="$2"

# Check if files exist
if [[ ! -f "$CORRECTIONS_FILE" ]]; then
    echo "Error: Corrections file '$CORRECTIONS_FILE' not found"
    exit 1
fi

if [[ ! -f "$TARGET_FILE" ]]; then
    echo "Error: Target file '$TARGET_FILE' not found"
    exit 1
fi

# Process corrections
while IFS='|' read -r original correction; do
    # Skip empty lines
    if [[ -z "$original" ]]; then
        continue
    fi
    
    # Skip lines with two or more '|' characters (count remaining fields after first split)
    remaining="${correction#*|}"
    if [[ "$remaining" != "$correction" ]]; then
        echo "Skipping line with multiple separators: $original|$correction"
        continue
    fi
    
    # Skip if correction is empty
    if [[ -z "$correction" ]]; then
        echo "Skipping empty correction for: $original"
        continue
    fi
    
    # Apply correction using sed
    # Escape special characters for sed
    original_escaped=$(printf '%s\n' "$original" | sed 's/[[\.*^$()+?{|]/\\&/g')
    correction_escaped=$(printf '%s\n' "$correction" | sed 's/[[\.*^$()+?{|]/\\&/g')
    
    echo "Replacing: '$original' -> '$correction'"
    sed -i.tmp "s/$original_escaped/$correction_escaped/g" "$TARGET_FILE"
    rm -f "$TARGET_FILE.tmp"
    
done < "$CORRECTIONS_FILE"

echo "Corrections applied to $TARGET_FILE"
