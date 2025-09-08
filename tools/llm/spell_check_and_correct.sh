#!/bin/bash

# Check arguments
if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <server_url> <model_name> <filename>"
    echo ""
    echo "Run aspell on specified file and process each misspelled word using an AI model"
    echo "to add missing spaces while preserving original German spelling from 1984."
    echo ""
    echo "Arguments:"
    echo "  server_url   Server URL (e.g., http://mimac:1234)"
    echo "  model_name   Model name (e.g., nexveridian/gpt-oss-120b)"
    echo "  filename     File to spell check (e.g., document.md)"
    echo ""
    echo "Example:"
    echo "  $0 http://localhost:1234 nexveridian/gpt-oss-120b document.md"
    exit 1
fi

SERVER="$1"
MODEL="$2"
FILENAME="$3"

# Run aspell on specified file and process each misspelled word
aspell -l de_DE-1901 --list < "$FILENAME" | sort | uniq | while read -r word; do
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
                {"role": "user", "content": "The following word is from a Text from 1984 (old German spelling!) and has been flagged as unknown by a spell checker: `'"$word"'`. When typing in the text, sometimes one or several spaces were omitted, but everything else is perfect. Are one or multiple spaces missing here? If yes, add them. Do not change any letter, do not change upper case or lower case, do not add or remove hyphens. Be careful that the result is correct old spelling German, so the capitalization of the result has to be correct, too. If you are absolutely sure that just adding one or more spaces while leaving all other characters identical (do not make anything upper case) fixes the word, print the corrected version. Otherwise, do not print anything. Do not print anything else, just the result."}
            ],
            "temperature": 0.0
        }' | jq -r '.choices[0].message.content')
    
    # Only do checks if result is not empty
    if [[ -n "$result" ]]; then
        # Check if removing spaces from result makes it different from original word
        result_no_spaces=$(echo "$result" | tr -d ' ')
        if [[ "$result_no_spaces" != "$word" ]]; then
            result="$result|XXX"
        else
            # Check if the result still has spelling errors
            spell_errors=$(echo "$result" | aspell -l de_DE-1901 --list)
            if [[ -n "$spell_errors" ]]; then
                result="$result|YYY"
            fi
        fi
    fi
    
    # Print the original word and the correction separated by |
    echo "$word|$result"
done