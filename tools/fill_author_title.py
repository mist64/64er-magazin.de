import sys
import re

def update_html_metadata(filenames):
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()

        # Update the title only if it's currently 'XXX'
        title_match = re.search(r'<h1>(.*?)</h1>', content, re.DOTALL)
        current_title_match = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
        if title_match and current_title_match and current_title_match.group(1).strip() == "XXX":
            title = title_match.group(1).strip()
            content = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', content, flags=re.DOTALL)

        # Update the author only if it's currently 'XXX'
        author_match = re.search(r'<p>\(([^)]*?)\)</p>', content, re.DOTALL)
        current_author_match = re.search(r'<meta name="author" content="(.*?)">', content)
        if author_match:
            author = author_match.group(1).replace('/', ', ').strip()
            if current_author_match:
                # Replace existing author
                if current_author_match.group(1).strip() == "XXX":
                    content = re.sub(
                        r'<meta name="author" content=".*?">',
                        f'<meta name="author" content="{author}">',
                        content
                    )
            else:
                # Add the <meta name="author"> tag if it doesn't exist
                head_close_tag = '</head>'
                meta_tag = f'    <meta name="author" content="{author}">\n'
                content = content.replace(head_close_tag, meta_tag + head_close_tag)

            # Change <p> to <address class="author">
            original_p_tag = author_match.group(0)  # The entire <p>(author)</p>
            updated_address_tag = re.sub(r'^<p>', '<address class="author">', original_p_tag)
            updated_address_tag = re.sub(r'</p>$', '</address>', updated_address_tag)
            content = content.replace(original_p_tag, updated_address_tag)

        # Save the updated HTML
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <file1> <file2> ...")
    else:
        update_html_metadata(sys.argv[1:])