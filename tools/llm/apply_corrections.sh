#!/bin/bash

# Check arguments
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <corrections_file> <target_file>"
    echo ""
    echo "Apply corrections from a pipe-separated corrections file to a target markdown file."
    echo "Skips lines that contain two or more '|' characters (indicating errors or multiple corrections)."
    echo ""
    echo "Correction file format:"
    echo "  original|correction           - Apply to all occurrences"
    echo "  line:original|correction      - Apply only to specific line number"
    echo ""
    echo "Arguments:"
    echo "  corrections_file   File containing corrections in format 'original|correction' or 'line:original|correction'"
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
while IFS='|' read -r original correction rest; do
    # Skip empty lines
    if [[ -z "$original" ]]; then
        continue
    fi

    # Skip if correction is empty
    if [[ -z "$correction" ]]; then
        echo "Skipping empty correction for: $original"
        continue
    fi

    # Check if original has line number prefix (format: 123:word)
    if [[ "$original" =~ ^([0-9]+):(.+)$ ]]; then
        line_num="${BASH_REMATCH[1]}"
        word="${BASH_REMATCH[2]}"

        # Escape special characters for sed
        word_escaped=$(printf '%s\n' "$word" | sed 's/[[\.*^$()+?{|]/\\&/g')
        correction_escaped=$(printf '%s\n' "$correction" | sed 's/[[\.*^$()+?{|]/\\&/g')

        echo "Replacing on line $line_num: '$word' -> '$correction'"
        sed -i.tmp "${line_num}s/$word_escaped/$correction_escaped/g" "$TARGET_FILE"
        rm -f "$TARGET_FILE.tmp"
    else
        # No line number, apply to all occurrences
        # Escape special characters for sed
        original_escaped=$(printf '%s\n' "$original" | sed 's/[[\.*^$()+?{|]/\\&/g')
        correction_escaped=$(printf '%s\n' "$correction" | sed 's/[[\.*^$()+?{|]/\\&/g')

        echo "Replacing globally: '$original' -> '$correction'"
        sed -i.tmp "s/$original_escaped/$correction_escaped/g" "$TARGET_FILE"
        rm -f "$TARGET_FILE.tmp"
    fi

done < "$CORRECTIONS_FILE"

echo "Corrections applied to $TARGET_FILE"
