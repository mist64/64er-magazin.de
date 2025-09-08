#!/bin/bash

# Check arguments
if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <server_url> <model_name> <filename>"
    echo ""
    echo "Find hyphenation cases in specified file and process them using an AI model"
    echo "to undo hyphenation where appropriate while preserving German spelling from 1984."
    echo ""
    echo "Searches for patterns:"
    echo "  -[a-z]         : hyphen followed by lowercase letter"
    echo "  [A-Z]-[A-Z][A-Z] : uppercase letter, hyphen, two uppercase letters"
    echo ""
    echo "Arguments:"
    echo "  server_url   Server URL (e.g., http://mimac:1234)"
    echo "  model_name   Model name (e.g., nexveridian/gpt-oss-120b)"
    echo "  filename     File to check for hyphenation (e.g., document.md)"
    echo ""
    echo "Example:"
    echo "  $0 http://localhost:1234 nexveridian/gpt-oss-120b document.md"
    exit 1
fi

SERVER="$1"
MODEL="$2"
FILENAME="$3"

# Find words matching hyphenation patterns and process each one
grep -oE '\S*-[a-z]\S*|\S*[A-Z]-[A-Z][A-Z]\S*' "$FILENAME" | grep -v '^-' | sort | uniq | while read -r word; do
    # Skip empty lines
    if [[ -z "$word" ]]; then
        continue
    fi
    
    # Run curl quietly and capture the result
    result=$(curl -s "$SERVER/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "'"$MODEL"'",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "The following word is from a German text from 1984 (old German spelling!) and contains a hyphen that might be from hyphenation at line breaks: `'"$word"'`. If this is a case of hyphenation that should be undone (i.e., the hyphen was added only because the word was split across lines), remove the hyphen to make it one word. Do NOT remove hyphens from compound words (like \"Ost-West\" or \"CD-ROM\") or from constructions like \"auf- oder zumachen\" (which should become \"auf- oder\"). Only remove hyphens that were added for line-breaking hyphenation. Do not change any letters, do not change upper case or lower case. If you are absolutely sure that removing the hyphen creates a valid German word from 1984 spelling, print the corrected version. Otherwise, do not print anything. Do not print anything else, just the result."}
            ],
            "temperature": 0.0
        }' | jq -r '.choices[0].message.content')
    
    # Only do checks if result is not empty
    if [[ -n "$result" ]]; then
        # Check if result only differs by hyphen removal or space addition
        # Remove all hyphens and spaces from both words for comparison
        word_clean=$(echo "$word" | tr -d '-' | tr -d ' ')
        result_clean=$(echo "$result" | tr -d '-' | tr -d ' ')
        
        if [[ "$word_clean" != "$result_clean" ]]; then
            # Characters were changed beyond hyphen/space modifications
            result="$result|XXX"
        fi
    fi
    
    # Print the original word and the correction separated by |
    echo "$word|$result"
done