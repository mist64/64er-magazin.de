#!/usr/bin/env python3

from bs4 import BeautifulSoup
import time
import os

GROUP_SIZE = 2
input_file_path = 'out/test/i21_delayed_index/index_all.html'
output_dir_path = '/tmp/'

def update_navigation(soup, prev_file_name, next_file_name):
    newer_link = soup.find(id="link_newer")
    older_link = soup.find(id="link_older")

    if prev_file_name:
        newer_link['href'] = os.path.join(output_dir_path, prev_file_name)
    else:
        newer_link.decompose()

    if next_file_name:
        older_link['href'] = os.path.join(output_dir_path, next_file_name)
    else:
        older_link.decompose()

# Load the HTML content
with open(input_file_path, 'r') as file:
    html_content = file.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Filter out 'article_link' tags in the future
for tag in soup.find_all(class_='article_link'):
    if int(tag['data-pubdate']) > time.time():
        tag.decompose()

# Create a list of valid 'article_link' tags (those that are left)
valid_article_links = soup.find_all(class_='article_link')

# Calculate the number of files needed
num_files = len(valid_article_links) // GROUP_SIZE + (1 if len(valid_article_links) % GROUP_SIZE else 0)

for i in range(num_files):
    # Make a deep copy of the modified soup for this iteration
    iter_soup = BeautifulSoup(str(soup), 'html.parser')

    # Determine the range of tags to keep for this file
    start_index = i * GROUP_SIZE
    end_index = start_index + GROUP_SIZE

    # Remove 'article_link' tags outside the current range
    for j, tag in enumerate(iter_soup.find_all(class_='article_link')):
        if not (start_index <= j < end_index):
            tag.decompose()

    # Update navigation links
    prev_file_name = f'article_group_{i}.html' if i > 0 else None
    next_file_name = f'article_group_{i+2}.html' if i < num_files - 1 else None
    update_navigation(iter_soup, prev_file_name, next_file_name)

    # Save the new HTML file
    output_file_path = os.path.join(output_dir_path, f'article_group_{i+1}.html')
    with open(output_file_path, 'w') as file:
        file.write(str(iter_soup))
