# This takes a singe HTML as input and writes individual HTMLs, one per article,
# with the proper header/footer.
# * Every <h1> tag should end in the "64er.pages" information in '['/']', e.g.
#   <h1>Vorschau [164]<h1>
#   This will be put into the <meta name="64er.pages"> tag, and removed from the <h1>
# * All paragraphs starting with '(' and ending with ')' are considered authors,
#   they are collected into the <meta name="author"> tag, and changed into
#   <address class="author">.
# * The title is copied into the <title> tag.
# * The issue number (from the command line) is put into <meta name="64er.issue">.

import sys
import re

def sanitize_filename(name):
    """Sanitize the filename by replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*+]', '_', name)

def remove_id_attributes(html_content):
    """Remove all id= attributes from HTML tags."""
    return re.sub(r'\s+id=["\'][^"\']*["\']', '', html_content)

def split_html(input_file, issue):
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the content by <h1> to identify sections
    sections = re.split(r'(<h1[^>]*>.*?</h1>)', content, flags=re.DOTALL)
    if len(sections) < 3:
        print("No <h1> tags found or content is improperly formatted.")
        return

    html_template_start = """<!DOCTYPE html>
<html lang="de">

<head>
    <title>XXX</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="../style.css">
    <meta name="author" content="XXX">
    <meta name="64er.issue" content="{issue}">
    <meta name="64er.pages" content="XXX">
    <!-- <meta name="64er.toc_category" content="XXX"> -->
    <!-- <meta name="64er.toc_title" content="XXX"> -->
    <meta name="64er.id" content="XXX">
</head>

<body>
    <article>
"""
    html_template_end = """
    </article>
</body>
</html>
"""

    for i in range(1, len(sections), 2):  # Every second section is a <h1>
        h1 = sections[i]
        body = sections[i + 1] if i + 1 < len(sections) else ""

        # Extract the page numbers and remove them from the <h1>
        h1_text = re.search(r'<h1[^>]*>(.*?)</h1>', h1, re.DOTALL).group(1).strip()
        page_match = re.search(r'\[(.*?)\]$', h1_text)
        if not page_match:
            print(f"Warning: No page specification found in <h1>: {h1_text}")
            continue
        pages = page_match.group(1)
        h1_cleaned = re.sub(r'\s*\[.*?\]$', '', h1_text)

        # Determine the file name
        first_page = pages.split(',')[0].split('-')[0].strip()
        sanitized_name = sanitize_filename(f"{first_page} {h1_cleaned}.html")

        # Collect all unique authors from matching <p> tags
        author_matches = re.findall(r'<p>\(([^)]*?)\)</p>', body, re.DOTALL)
        unique_authors = set()
        for author_content in author_matches:
            # Normalize author content (replace '/' with ', ')
            normalized_author = author_content.strip().replace('/', ', ')
            unique_authors.add(normalized_author)
            # Convert the <p> to <address>
            body = body.replace(
                f'<p>({author_content})</p>',
                f'<address class="author">({author_content})</address>',
                1  # Replace one occurrence at a time
            )

        # Generate the output HTML
        output_html = html_template_start.format(issue=issue)
        output_html += f"        <h1>{h1_cleaned}</h1>\n"

        # Add content after <h1>, or a placeholder if none exists
        if body.strip():
            # Remove id attributes from the body content
            clean_body = remove_id_attributes(body.strip())
            output_html += clean_body
        else:
            output_html += "        <p>No additional content.</p>\n"

        # Add the closing template
        output_html += html_template_end

        # Update metadata
        output_html = re.sub(r'<title>XXX</title>', f'<title>{h1_cleaned}</title>', output_html)
        output_html = re.sub(r'<meta name="64er.pages" content="XXX">',
                             f'<meta name="64er.pages" content="{pages}">', output_html)
        if unique_authors:
            # Join unique authors into a single string
            authors_meta = ', '.join(sorted(unique_authors))  # Sort for consistent order
            output_html = re.sub(r'<meta name="author" content="XXX">',
                                 f'<meta name="author" content="{authors_meta}">', output_html)

        # Write the output file
        with open(sanitized_name, 'w', encoding='utf-8') as output_file:
            output_file.write(output_html)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_file> <64er.issue>")
    else:
        split_html(sys.argv[1], sys.argv[2])