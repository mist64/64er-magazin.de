#!/usr/bin/env python3

from bs4 import BeautifulSoup
import time
import os

FILTER_BY_DATE = True
GROUP_SIZE = 20
input_file_path = 'index_all.html'

def filename(i):
    if i == 0:
        return 'index.html'
    else:
        return f'index{i+1}.html'

def update_navigation(soup, prev_file_name, next_file_name):
    newer_link = soup.find(id="link_newer")
    older_link = soup.find(id="link_older")

    if prev_file_name:
        newer_link['href'] = prev_file_name
    else:
        newer_link.decompose()

    if next_file_name:
        older_link['href'] = next_file_name
    else:
        older_link.decompose()

# Load the HTML content
with open(input_file_path, 'r') as file:
    soup = BeautifulSoup(file.read(), 'html.parser')

# Filter out 'article_link' tags in the future
if FILTER_BY_DATE:
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
    prev_file_name = filename(i-1) if i > 0 else None
    next_file_name = filename(i+1) if i < num_files - 1 else None
    update_navigation(iter_soup, prev_file_name, next_file_name)

    # Save the new HTML file
    with open(filename(i), 'w') as file:
        file.write(str(iter_soup))
