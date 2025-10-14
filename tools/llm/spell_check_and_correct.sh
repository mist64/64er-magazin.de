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

# Create temp file to track processed words
PROCESSED_WORDS=$(mktemp)
trap "rm -f $PROCESSED_WORDS" EXIT

# Split file into paragraphs (separated by blank lines) and process each
# Track line numbers properly
awk 'BEGIN {para_num=0}
     /^$/ {in_para=0; next}
     !in_para {para_num++; para_line[para_num]=NR; in_para=1}
     {para_text[para_num] = para_text[para_num] (para_text[para_num] ? "\n" : "") $0}
     END {for (i=1; i<=para_num; i++) print para_line[i] "|||" para_text[i]}' "$FILENAME" |
while IFS='|||' read -r line_num para_text; do
    # Skip empty paragraphs
    if [[ -z "$para_text" ]]; then
        continue
    fi

    # Get misspelled words in this paragraph (using de-alt for old German spelling from 1901-1996)
    misspelled=$(echo "$para_text" | aspell list -d de-alt | sort | uniq)

    # Skip if no misspelled words
    if [[ -z "$misspelled" ]]; then
        continue
    fi

    # Get context: use the paragraph text itself as context
    # Extract a unique snippet from middle of paragraph for finding surrounding context
    snippet=$(echo "$para_text" | tr '\n' ' ' | cut -c 1-50)
    if [[ -n "$snippet" ]]; then
        context=$(grep -B 5 -A 5 -F "$snippet" "$FILENAME" 2>/dev/null || echo "$para_text")
    else
        context="$para_text"
    fi

    # Process each misspelled word
    echo "$misspelled" | while read -r word; do
        # Skip empty lines
        if [[ -z "$word" ]]; then
            continue
        fi

        # Skip if we've already processed this word
        if grep -q -F -x "$word" "$PROCESSED_WORDS" 2>/dev/null; then
            continue
        fi
        echo "$word" >> "$PROCESSED_WORDS"

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
            echo "Line: $line_num" >&2
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
                spell_errors=$(echo "$result" | aspell list -d de-alt)
                if [[ -n "$spell_errors" ]]; then
                    result="$result|YYY"
                fi
            fi
        fi

        # Print line number, the original word and the correction separated by |
        echo "$line_num:$word|$result"
    done
done
