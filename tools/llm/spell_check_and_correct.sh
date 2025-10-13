#!/bin/bash

# Parse arguments
DEBUG=0
if [[ "$1" == "--debug" ]]; then
    DEBUG=1
    shift
fi

# Check arguments
if [[ $# -ne 3 ]]; then
    echo "Usage: $0 [--debug] <server_url> <model_name> <filename>"
    echo ""
    echo "Run aspell on specified file and process each misspelled word using an AI model"
    echo "to add missing spaces while preserving original German spelling from 1984."
    echo ""
    echo "Arguments:"
    echo "  --debug      Optional: Show prompts sent to LLM on stderr"
    echo "  server_url   Server URL (e.g., http://mimac:1234)"
    echo "  model_name   Model name (e.g., nexveridian/gpt-oss-120b)"
    echo "  filename     File to spell check (e.g., document.md)"
    echo ""
    echo "Example:"
    echo "  $0 http://localhost:1234 nexveridian/gpt-oss-120b document.md"
    echo "  $0 --debug http://localhost:1234 nexveridian/gpt-oss-120b document.md"
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

    # Extract context around the word (3 lines before and after)
    context=$(grep -i -B 3 -A 3 "$word" "$FILENAME" | head -20)

    # Build the prompt (for display)
    prompt_display="The following word is from a Text from 1984 (old German spelling!) and has been flagged as unknown by a spell checker: \`$word\`.

Context from the text:
\`\`\`
$context
\`\`\`

When typing in the text, sometimes one or several spaces were omitted, but everything else is perfect. Are one or multiple spaces missing here? If yes, add them. Do not change any letter, do not change upper case or lower case, do not add or remove hyphens. Be careful that the result is correct old spelling German, so the capitalization of the result has to be correct, too. If you are absolutely sure that just adding one or more spaces while leaving all other characters identical (do not make anything upper case) fixes the word, print the corrected version. Otherwise, do not print anything. Do not print anything else, just the result."

    # Debug output
    if [[ $DEBUG -eq 1 ]]; then
        echo "========================================" >&2
        echo "Word: $word" >&2
        echo "----------------------------------------" >&2
        echo "$prompt_display" >&2
        echo "========================================" >&2
        echo "" >&2
    fi

    # Build the user prompt
    user_content="The following word is from a Text from 1984 (old German spelling!) and has been flagged as unknown by a spell checker: \`$word\`.

Context from the text:
\`\`\`
$context
\`\`\`

When typing in the text, sometimes one or several spaces were omitted, but everything else is perfect. Are one or multiple spaces missing here? If yes, add them. Do not change any letter, do not change upper case or lower case, do not add or remove hyphens. Be careful that the result is correct old spelling German, so the capitalization of the result has to be correct, too. If you are absolutely sure that just adding one or more spaces while leaving all other characters identical (do not make anything upper case) fixes the word, print the corrected version. Otherwise, do not print anything. Do not print anything else, just the result."

    # Build JSON payload using jq for proper escaping
    json_payload=$(jq -n \
        --arg model "$MODEL" \
        --arg content "$user_content" \
        '{
            model: $model,
            messages: [
                {role: "system", content: "You are a helpful assistant."},
                {role: "user", content: $content}
            ],
            temperature: 0.0
        }')

    # Run curl and capture both response and errors
    response=$(curl -s "$SERVER/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "$json_payload")

    # Parse JSON response, suppress jq errors
    result=$(echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null)

    # Debug: show response if jq failed and we're in debug mode
    if [[ $? -ne 0 && $DEBUG -eq 1 ]]; then
        echo "JSON parse error for word: $word" >&2
        echo "Response was: $response" >&2
        echo "" >&2
    fi
    
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