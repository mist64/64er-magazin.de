#!/bin/bash

# Check arguments
if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <server_url> <model_name> <filename>"
    echo ""
    echo "Process markdown file paragraph by paragraph to find and correct OCR errors"
    echo "while preserving German spelling from 1984 and understanding 1980s computing context."
    echo ""
    echo "Focus on typical OCR errors:"
    echo "  1/l/I mixups    : 1 vs l vs I confusion"
    echo "  O vs 0 mixups   : O (letter) vs 0 (digit) confusion"
    echo "  Other common OCR character recognition errors"
    echo ""
    echo "Context awareness for:"
    echo "  - Commodore 64 and 1980s computing terminology"
    echo "  - BASIC programming language keywords and syntax"
    echo "  - Assembly language and 6502 processor terms"
    echo "  - German computing terms from 1984"
    echo ""
    echo "Arguments:"
    echo "  server_url   Server URL (e.g., http://mimac:1234)"
    echo "  model_name   Model name (e.g., nexveridian/gpt-oss-120b)"
    echo "  filename     Markdown file to check for OCR errors"
    echo ""
    echo "Example:"
    echo "  $0 http://localhost:1234 nexveridian/gpt-oss-120b document.md"
    exit 1
fi

SERVER="$1"
MODEL="$2"
FILENAME="$3"

# Check if file exists
if [[ ! -f "$FILENAME" ]]; then
    echo "Error: File '$FILENAME' not found"
    exit 1
fi

# Process file paragraph by paragraph
# Split on double newlines to get paragraphs, then process each non-empty paragraph
awk 'BEGIN{RS="\n\n"; ORS="\n\n"} NF {print NR "|" $0}' "$FILENAME" | while IFS='|' read -r para_num paragraph; do
    # Skip empty paragraphs
    if [[ -z "$paragraph" ]]; then
        continue
    fi
    
    # Skip markdown headers, code blocks, and other special formatting
    if [[ "$paragraph" =~ ^[[:space:]]*# ]] || [[ "$paragraph" =~ ^\`\`\` ]] || [[ "$paragraph" =~ ^\* ]] || [[ "$paragraph" =~ ^\- ]]; then
        continue
    fi
    
    echo "Processing paragraph $para_num..."
    
    # Escape the paragraph content for JSON
    paragraph_escaped=$(printf '%s' "$paragraph" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | tr '\n' '\001' | sed 's/\001/\\n/g')
    
    # Create the JSON payload
    json_payload=$(cat <<EOF
{
    "model": "$MODEL",
    "messages": [
        {"role": "system", "content": "You are an expert in 1980s computing, especially Commodore 64, BASIC programming, Assembly language, and the 6502 processor. You understand German computing terminology from 1984 and can identify OCR errors in technical texts."},
        {"role": "user", "content": "The following paragraph is from a German computer magazine from 1984 (64er magazine) and may contain OCR character recognition errors. ONLY fix obvious OCR misrecognition of individual characters within words, such as:\n- 1/l/I confusion (digit 1, letter l, letter I) within a word\n- O/0 confusion (letter O, digit 0) within a word\n- Similar single character misrecognition errors\n\nDO NOT fix or change:\n- Abbreviations or acronyms (Btx, BBS, etc. are correct as written)\n- Complete words even if they seem wrong (Musipack vs Musicpack - both could be valid)\n- Numbers or phone numbers (5309, 0 22 25, (04 21) are formatted correctly)\n- Spacing in any context\n- Technical terms or product names (C 116 could be a valid model number)\n- Any words or rewording\n- Typos or spelling mistakes\n- Orthography modernization (keep pre-1997 German with ß, not ss)\n- Word substitutions\n- Upper/lower case changes\n- Capitalization changes\n\nONLY fix cases where you are 100% certain a single character was misrecognized by OCR within an existing word, and the fix results in a known German word or established technical term from 1984.\n\nConsider 1980s computing context: Commodore 64, BASIC, Assembly, 6502 processor.\n\nParagraph:\n$paragraph_escaped\n\nFor each definitive OCR CHARACTER misrecognition error you find, output ONLY the correction in format \"incorrect_text|correct_text\". Each correction on separate line. If no clear OCR character errors found, output nothing. No explanations. Be extremely conservative."}
    ],
    "temperature": 0.0
}
EOF
)
    
    # Run curl quietly and capture the raw response
    raw_response=$(curl -s "$SERVER/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "$json_payload")
    
    # Check if we got a valid JSON response
    if ! echo "$raw_response" | jq empty 2>/dev/null; then
        echo "Error: Invalid JSON response for paragraph $para_num. Raw response:"
        echo "$raw_response"
        continue
    fi
    
    # Extract the result
    result=$(echo "$raw_response" | jq -r '.choices[0].message.content')
    
    # Only output if result is not empty and doesn't contain error messages
    if [[ -n "$result" && "$result" != "null" && ! "$result" =~ ^[[:space:]]*$ ]]; then
        # Filter out lines that don't contain exactly one pipe character
        echo "$result" | while IFS= read -r line; do
            if [[ -n "$line" && $(echo "$line" | tr -cd '|' | wc -c) -eq 1 ]]; then
                IFS='|' read -r original correction <<< "$line"
                if [[ -n "$original" && -n "$correction" && "$original" != "$correction" ]]; then
                    # Verify that the original text actually exists in the paragraph
                    if grep -qF "$original" <<< "$paragraph"; then
                        echo "$original|$correction"
                    fi
                fi
            fi
        done
    fi
    
done