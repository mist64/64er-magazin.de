# This script cleans up an HTML file written by macOS TextEdit

import re

with open("/Users/mist/Desktop/SH8504_tables.html", "r") as f:
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

with open("SH8504_clean.tables", "w") as f:
    f.write(content)