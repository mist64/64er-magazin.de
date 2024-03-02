#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from datetime import datetime
import pytz

def filter_rss_entries(input_file, output_file):
    # Parse the input RSS file
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Define the current datetime with UTC timezone for comparison
    current_datetime = datetime.now(pytz.utc)

    # Find all <item> elements
    for item in root.findall('.//item'):
        # Parse the publication date of the current item
        pubDate = item.find('pubDate').text
        # Convert the pubDate string to a datetime object
        pubDate_datetime = datetime.strptime(pubDate, '%a, %d %b %Y %H:%M:%S %z GMT')

        # Remove the item if its publication date is in the future
        if pubDate_datetime > current_datetime:
            root.find('.//channel').remove(item)

    # Write the modified tree to a new RSS file
    tree.write(output_file)

# Example usage
input_file = '64er_all.rss'
output_file = '64er.rss'
filter_rss_entries(input_file, output_file)
