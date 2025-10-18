# This script cleans up an HTML file written by macOS TextEdit

import argparse
import re

parser = argparse.ArgumentParser(description='Clean up HTML tables from macOS TextEdit')
parser.add_argument('input_file', help='Input HTML file to clean')
parser.add_argument('output_file', help='Output file for cleaned HTML')
args = parser.parse_args()

with open(args.input_file, "r") as f:
    content = f.read()

# Apply all the sed transformations:
content = re.sub(r'\sclass="[^"]*"', '', content)                      # remove class="..."
content = re.sub(r'\svalign="[^"]*"', '', content)                     # remove valign="..."
content = re.sub(r'<span class="[^"]*">', '', content)                 # remove <span class="...">
content = re.sub(r'<span>', '', content)                               # remove <span>
content = re.sub(r'</span>', '', content)                              # remove </span>
content = re.sub(r'<b></b>', '', content)                              # remove empty <b></b>
content = re.sub(r'<td>\s*\n\s*<p>', '<td>', content)                  # join <td>\n <p> → <td>
content = re.sub(r'</p>\s*\n\s*</td>', '</td>', content)
content = re.sub(r'</p>\s*\n\s*<p>', '<br>', content)
content = re.sub(r'</ol>\s*\n\s*<p>', '</ol>', content)
content = re.sub(r'\s*cellspacing="0"\s+cellpadding="0"', '', content)

content = re.sub(r'\t+', ' ', content)

# False-positive lists
# 1. Remove opening <ol> tag
content = re.sub(r'\s*<ol>\s*', '', content)
# 2. Replace the first <li>...</li> with its inner content + <br>
content = re.sub(r'<li>(.*?)</li>', r'\1<br>', content, count=1)
# 3. Replace remaining <li>...</li> with ...<br>
content = re.sub(r'<li>(.*?)</li>', r'\1<br>', content)
# 4. Remove closing </ol> tag
content = re.sub(r'\s*</ol>\s*', '', content)

with open(args.output_file, "w") as f:
    f.write(content)