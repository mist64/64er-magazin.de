#!/usr/bin/env python3

import sys
import re
import os
import shutil
import pprint
import subprocess
import json
import html
import subprocess
import http.server
import socketserver
import hashlib
import urllib.parse
import pytz
import argparse
import gzip
import lunr
from tools import mse, checksummer
from dataclasses import dataclass, field
from collections import defaultdict, OrderedDict
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import quote
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from PyPDF2 import PdfReader, PdfWriter

#
# Parse arguments
#

### CONFIG Class

@dataclass
class BuildConfig():
    source_dir: str = "issues" # where to look for files
    build_dir: str = "out" # where to put the output
    cache_dir: str = "cache"

    server: str = "www.64er-magazin.de" # where to put the files so others can see

    base_dir: str = "" # base directory: updated from command line arguments and branch name

    # cli arguments
    deploy: bool = False # set via cli argument "upload": upload to server
    build_future: bool = False # set via cli flag "--future": helper for disabling unfinished categories
    start_local_server: bool = True # set via cli flag "--join": helper for not starting a local server every time
    lang: str = "de" # set via cli flag "--lang": change language between english and german

    # git status
    git_has_changes: bool = True # set in setup
    git_branch_name: str = "main" # set in setup


# If outputfile == None, returns (byte array, basicversion)
# If outputfile given, returns (None, basicversion)
# exits on subprocess error
def petcat2prg(listing, output_file_name = None) -> tuple[None | bytes, str]:

    regex = r"^;.*==([0-9A-Fa-f]{4})=="
    load_address = re.findall(regex, listing, re.MULTILINE)
    if load_address:
        load_address = load_address[0]
    else:
        load_address = '0801'

    pattern = r"^;version=(.*)$"
    match = re.search(pattern, listing, re.MULTILINE)
    version = match.group(1) if match else None
    if not version:
        version = '2'

    # Prepare the command
    command = ['petcat', f'-w{version}', '-l', load_address, f'-{version}']
    if output_file_name:
        command += ['-o', output_file_name]

    # Execute the command, piping the listing into it
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    prg, _ = process.communicate(input=listing.encode('utf-8'))

    # Check if petcat executed successfully
    if process.returncode != 0:
        print(f"Failed to process: {key}")
        exit()

    if output_file_name:
        prg = None

    return prg, version

def parse_cli_into_config():

    # supported command line arguments
    parser = argparse.ArgumentParser(description=f"Generate the magazine")
    parser.add_argument("deploy_mode", choices=["upload", "local"], nargs='?', default="local", help="the deploy mode (default: %(default)s)")
    parser.add_argument("--issues", action='extend', nargs='+', type=str, help="only build specified issues (yymm)" )
    parser.add_argument("--future", action='store_true', help="also build issues with release dates in the future")
    parser.add_argument("--lang", choices=['de', 'en'], nargs='?', const='de', default='de', help="[WIP] build a different language version (default: %(default)s)")
    parser.add_argument("--join", action='store_true', help="open page locally without starting a server ")

    # parsing command line arguments
    args = parser.parse_args()

    config = BuildConfig()
    config.deploy = args.deploy_mode == "upload"
    config.build_issues = args.issues
    config.build_future = args.future
    config.lang = args.lang
    config.start_local_server = not args.join

    # get git status
    f = os.popen(f'git ls-files -m | wc -l')
    if int(f.read()) <= 0:
      config.git_has_changes = False

    git_branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
    config.git_branch_name = git_branch_name


    ##
    ## SETUP
    ##
    print("*** Setup")

    is_on_main = git_branch_name == 'main'

    # adjust base dir for the current build destination and branches
    if is_on_main:
        if not (config.build_future or config.build_issues):
            config.base_dir = ''
        else:
            config.base_dir = 'test/'
    else:
        config.base_dir = 'test/' + config.git_branch_name + '/'

    if config.lang != 'de':
        config.base_dir += '/' + config.lang

    git_status = ''
    if config.git_has_changes:
      git_status = '+'

    print(f"  > branch '{config.git_branch_name}'{git_status} -> '{config.base_dir}'")

    # if the current build should be uploaded: do some sanity checking
    if config.deploy:

      # if config.git_has_changes:
      #   print("Generating and upload failed:")
      #   print("There are uncommited changes in the working copy.")
      #   exit()

      if is_on_main and not (config.build_future or config.build_issues):
          response = input("Deploy to production? [Y/N]: ").strip()
          if response.lower() != 'y':
              print("Exiting.")
              exit()

    return config


CONFIG = parse_cli_into_config()

git_status =  '\n  <!!!> Has uncommited changes!' if CONFIG.git_has_changes else ''

print(f"""
    > base_dir: {CONFIG.base_dir}
    > deploy: {CONFIG.deploy}
    > build_issues: {CONFIG.build_issues}
    > build_future: {CONFIG.build_future}
    > start_local_server: {CONFIG.start_local_server}
{git_status}
""")


#
# Settings
#

OUT_DIRECTORY = CONFIG.build_dir
CACHE_DIRECTORY = CONFIG.cache_dir
SERVER = CONFIG.server

BASE_DIR = CONFIG.base_dir
LANG = CONFIG.lang

NEW_DOWNLOADS = 20

RSS_BASE_URL = "https://www.64er-magazin.de/"
MASTODON_HASHTAGS = "#c64 #retrocomputing #64er"
TITLE_IMAGE_NAME = "title.jpg"

#
# Localization
#
if LANG == "de":
  IN_DIRECTORY = 'issues'
  MAGAZINE_NAME = "64'er Magazin"
  MAGAZINE_NAME_FULL = "64'er – Das Magazin für Computer-Fans"
  LABEL_ISSUES = "Ausgaben"
  LABEL_ARTICLES = "Artikel"
  LABEL_LISTINGS = "Listings"
  LABEL_SEARCH = "Suchen"
  LABEL_NEWS = "Aktuell"
  LABEL_HARDWARE = "Hardware"
  LABEL_TESTS = "Test"
  LABEL_SOFTWARE = "Software"
  LABEL_GAMES = "Spiele"
  LABEL_PROGRAMS = "Programme"
  LABEL_TUTORIALS = "Kurse"
  LABEL_IN_PRACTICE = "Praxis"
  LABEL_CONTACT = "Kontakt"
  LABEL_IMPRINT = "Impressum"
  LABEL_PRIVACY = "Datenschutzerklärung"
  LABEL_404 = "404 - Seite nicht gefunden"
  LABEL_ISSUE = "Ausgabe"
  LABEL_PAGE = "S."
  LABEL_DOWNLOAD_ISSUE_PDF = "PDF Downloaden"
  LABEL_DOWNLOAD_ARTICLE_PDF = "Diesen Artikel als PDF herunterladen"
  LABEL_SHARE_ON_MASTODON = "Diesen Artikel auf Mastodon teilen"
  LABEL_DOWNLOAD = "Download"
  LABEL_NEWER = "← Neuer"
  LABEL_OLDER = "Älter →"
  LABEL_PREVIOUS_ARTICLE = "← Vorheriger Artikel"
  LABEL_NEXT_ARTICLE = "Nächster Artikel →"
  LABEL_ALL_ISSUES = "Alle Ausgaben"
  LABEL_ALL_ARTICLES = "Alle Artikel"
  LABEL_ALL_LISTINGS = "Alle Listings"
  LABEL_CURRENT_REGULAR_ISSUE = "Das aktuelle Magazin"
  LABEL_CURRENT_SPECIAL_ISSUE = "Das aktuelle Sonderheft"
  LABEL_REGULAR_MAGAZINES = "Stammagazin"
  LABEL_SPECIAL_MAGAZINES = "Sonderhefte"
  LABEL_LATEST_LISTINGS = "Neueste Listings"
  LABEL_TOC_ISSUE = "Inhalt Ausgabe"
  LABEL_CATEGORY = "Kategorie"
  LABEL_ARTICLE = "Artikel"
  LABEL_DOWNLOADS = "Downloads"
  FILENAME_ISSUES = "ausgaben"
  FILENAME_ARTICLES = "artikel"
  FILENAME_LISTINGS = "listings"
  FILENAME_NEWS = "aktuell"
  FILENAME_HARDWARE = "hardware"
  FILENAME_TESTS = "test"
  FILENAME_SOFTWARE = "software"
  FILENAME_GAMES = "spiele"
  FILENAME_PROGRAMS = "programme"
  FILENAME_TUTORIALS = "kurse"
  FILENAME_IN_PRACTICE = "praxis"
  FILENAME_PRIVACY = "datenschutz"
  FILENAME_404 = "404"
  FILENAME_IMPRINT = "impressum"
  CATEGORY_TYPE_IN_1 = "Programme zum Abtippen"
  CATEGORY_TYPE_IN_2 = "Listings zum Abtippen"

  TOPICS = [ # Title + used prefix # these are the values used with "64er.index_category" for sorting the topics by prefix
      (LABEL_NEWS, ["Aktuell|"]),
      (LABEL_HARDWARE, ["Hardware|"]),
      (LABEL_TESTS, [ "Hardware-Test|",
                      "Software-Test|",
                      "Spiele-Test|"]),
      (LABEL_SOFTWARE, ["Software|"]),
      (LABEL_GAMES, ["Listings zum Abtippen|Spiel|"]),
      (LABEL_PROGRAMS, ["Listings zum Abtippen|Anwendung|",
                        "Listings zum Abtippen|Grafik|",
                        "Listings zum Abtippen|Tips & Tricks|"]),
      (LABEL_TUTORIALS, ["Kurse|"]),
      (LABEL_IN_PRACTICE, ["So machen's andere|"]),
  ]
  HTML_PRIVACY = """
    <main>
    <h1>Datenschutzerklärung</h1>
    <ul>
    <li>Beim Lesen dieser Website werden keine personenbezogenen Daten erhoben.</li>
    <li>Die Suche läuft lokal im Browser. Die Sucheingabe wird nicht an den Server übertragen.</li>
    <li>Beim Absenden eines Kommentars werden die eingegebenen Daten auf einem Server in der EU gespeichert.</li>
    </ul>
    </main>
    """

  HTML_IMG_FEHLERTEUFELCHEN= f"""
    <img src="/{BASE_DIR}fehlerteufelchen.svg" alt="Fehlerteufelchen">
  """

  HTML_IMG_FUTURETEUFELCHEN= f"""
    <img src="/{BASE_DIR}futureteufelchen.svg" alt="Futureteufelchen">
  """

  HTML_404 = f"""
    <main class="fehlerteufelchen">
    <h1>Seite nicht gefunden</h1>
    {HTML_IMG_FEHLERTEUFELCHEN}
    </main>
  """

elif LANG == "en":
  IN_DIRECTORY = 'en'
  MAGAZINE_NAME = "64'er Magazine"
  MAGAZINE_NAME_FULL = "64'er – The Magazine for Computer Fans"
  LABEL_ISSUES = "Issues"
  LABEL_ARTICLES = "Articles"
  LABEL_LISTINGS = "Listings"
  LABEL_SEARCH = "Search"
  LABEL_NEWS = "News"
  LABEL_HARDWARE = "Hardware"
  LABEL_TESTS = "Tests"
  LABEL_SOFTWARE = "Software"
  LABEL_GAMES = "Games"
  LABEL_PROGRAMS = "Programs"
  LABEL_TUTORIALS = "Tutorials"
  LABEL_IN_PRACTICE = "Practice"
  LABEL_CONTACT = "Contact"
  LABEL_IMPRINT = "Imprint"
  LABEL_PRIVACY = "Privacy"
  LABEL_404 = "404 - Page Not Found"
  LABEL_CATEGORY = "Category"
  LABEL_ISSUE = "Issue"
  LABEL_PAGE = "p."
  LABEL_DOWNLOAD_ISSUE_PDF = "Download PDF"
  LABEL_DOWNLOAD_ARTICLE_PDF = "Download this article in PDF format"
  LABEL_SHARE_ON_MASTODON = "Share this article on Mastodon"
  LABEL_DOWNLOAD = "Download"
  LABEL_NEWER = "← Newer"
  LABEL_OLDER = "Older →"
  LABEL_PREVIOUS_ARTICLE = "← Previous Article"
  LABEL_NEXT_ARTICLE = "Next Article →"
  LABEL_ALL_ISSUES = "All Issues"
  LABEL_ALL_ARTICLES = "All Articles"
  LABEL_ALL_LISTINGS = "All Listings"
  LABEL_CURRENT_REGULAR_ISSUE = "Current Issue"
  LABEL_CURRENT_SPECIAL_ISSUE = "Current Special Issue"
  LABEL_REGULAR_MAGAZINES = "Main Magazine"
  LABEL_SPECIAL_MAGAZINES = "Special Issues"
  LABEL_LATEST_LISTINGS = "Latest Listings"
  LABEL_TOC_ISSUE = "Table of Contents, Issue"
  LABEL_ARTICLE = "Article"
  LABEL_DOWNLOADS = "Downloads"
  FILENAME_ISSUES = "issues"
  FILENAME_ARTICLES = "articles"
  FILENAME_LISTINGS = "listings"
  FILENAME_NEWS = "news"
  FILENAME_HARDWARE = "hardware"
  FILENAME_TESTS = "tests"
  FILENAME_SOFTWARE = "software"
  FILENAME_GAMES = "games"
  FILENAME_PROGRAMS = "programs"
  FILENAME_TUTORIALS = "tutorials"
  FILENAME_IN_PRACTICE = "practice"
  FILENAME_PRIVACY = "privacy"
  FILENAME_404 = "404"
  FILENAME_IMPRINT = "imprint"
  CATEGORY_TYPE_IN_1 = "Type-in Programs"
  CATEGORY_TYPE_IN_2 = "Type-in Listings"

  # TODO XXX translate
  TOPICS = [ # Title + used prefix # these are the values used with "64er.index_category" for sorting the topics by prefix
      (LABEL_NEWS, ["Aktuell|"]),
      (LABEL_HARDWARE, ["Hardware|"]),
      (LABEL_TESTS, [ "Hardware-Test|",
                      "Software-Test|",
                      "Spiele-Test|"]),
      (LABEL_SOFTWARE, ["Software|"]),
      (LABEL_GAMES, ["Listings zum Abtippen|Spiel|"]),
      (LABEL_PROGRAMS, ["Listings zum Abtippen|Anwendung|",
                        "Listings zum Abtippen|Grafik|",
                        "Listings zum Abtippen|Tips & Tricks|"]),
      (LABEL_TUTORIALS, ["Kurse|"]),
      (LABEL_IN_PRACTICE, ["So machen's andere|"]),
  ]

  HTML_PRIVACY = """
    <main>
    <h1>Privacy Policy</h1>
    <ul>
    <li>No personal data is collected when reading this website.</li>
    <li>The search runs locally in the browser. The search input is not transmitted to the server.</li>
    <li>When submitting a comment, the entered data is stored on a server in the EU.</li>
    </ul>
    </main>
    """

  HTML_IMG_FEHLERTEUFELCHEN=f"""
    <img src="/{BASE_DIR}fehlerteufelchen.svg" alt="Error Devil">
    """

  HTML_IMG_FUTURETEUFELCHEN= f"""
    <img src="/{BASE_DIR}futureteufelchen.svg" alt="Future Devil">
  """

  HTML_404 = f"""
    <main class="fehlerteufelchen">
    <h1>Page Not Found</h1>
    {HTML_IMG_FEHLERTEUFELCHEN}
    </main>
    """

LOGO = f'<img src="/{BASE_DIR}logo.svg" alt="{MAGAZINE_NAME}">'

###
### DATABASE
###

# converts an img tag into a picture tag with AVIF and a JPEG fallback
def avif_picture_tag(soup, img_src, attrs=None):

    def image_tag(tag_src=img_src):
        img_tag = soup.new_tag('img')

        # Copy all attributes from the original <img> tag to the new one
        if attrs:
            for attr, value in attrs.items():
                img_tag[attr] = value

        # add an empty alt for now if there is none
        if 'alt' not in img_tag.attrs:
            img_tag['alt'] = ""

        img_tag['src'] = tag_src
        return img_tag

    # svg is unchanged
    if img_src[-4:] == '.svg':
        svg_tag = image_tag()
        return svg_tag

    # Create the <picture> tag
    picture_tag = soup.new_tag('picture')

    # Create the <source> tag for AVIF and add it to <picture>
    source_tag = soup.new_tag('source', srcset=img_src[:-4] + '.avif', type='image/avif')
    picture_tag.insert(0, source_tag)

    # Create a new <img> tag for the JPEG version
    # Update the src attribute to the JPEG version
    jpg_src = img_src[:-4] + '.jpg'
    new_img_tag =  image_tag(jpg_src)

    # Append the new <img> tag to the <picture> tag
    picture_tag.append(new_img_tag)
    return picture_tag


def calculate_sha1(filepath):
    sha1 = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()

class Article:

    def __init__(self, metadata):
        self.title = metadata['title']
#        self.issue = metadata['issue'] # XXX should we reference the issue directly?
        self.pages_raw = metadata['pages']
        self.pages = re.sub(r'[^\d,-]', '', metadata['pages'])
        self.id = metadata['id']
        self.issue_key = metadata['issue_key']
        self.head1 = metadata['head1']
        self.head2 = metadata['head2']
        self.toc_title = metadata['toc_title']
        self.toc_category = metadata['toc_category']
        self.index_title = metadata['index_title']
        self.index_category = metadata['index_category']
        self.target_filename = metadata['target_filename']
        self.downloads = metadata['downloads']
        self.description = metadata['description']
        self.src_img_urls = metadata['src_img_urls']
        self.html = metadata['html']
        self.txt = metadata['txt']
        self.img_urls = metadata['img_urls']
        self.path = metadata['path'] # nice for debugging
        self.sort_index = None # set later, after sorting all articles

    def first_page_number(self):
        try:
            return int(self.pages.split(',')[0].split('-')[0])
        except ValueError:
            raise SystemExit(f'\n---\nMetaDataError: pages tag is "{self.pages}"\n   File: "{self.path}"')

    def article_sort_key(self):
        return (self.first_page_number(), self.pages_raw)

    def out_filename(self):
        return self.id + '.html'

    def article_pubdate(self):
        issue = db.issues[self.issue_key]
        if self.issue_key.endswith("/84") and self.issue_key != "12/84":
            # until 8411: every 16 hours
            # (we can remove this code path once 11/84 is through)
            hours_per_article = 16
        else:
            # starting with 8412: spread over 30 days
            hours_per_article = int(30*24 / len(issue.articles))
        pubdate = issue.pubdate + timedelta(hours=hours_per_article * self.sort_index)
        return pubdate

    def is_category_listings(self):
        if not self.index_category:
            return False
        if not self.index_category.startswith(CATEGORY_TYPE_IN_1 + '|') and not self.index_category.startswith(CATEGORY_TYPE_IN_2 + '|'):
            return False
        if not self.downloads:
            return False
        return True

class Issue:
  def __init__(self, issue_directory_path):
      """Extracts all relevant data from an issue directory, including HTML file paths."""
      toc_order = []
      pdf_filename = None
      issue_dir_name = os.path.basename(issue_directory_path)
      issue_key = None
      pubdate = None
      articles = []

      pdf_filename = None

      # todo: XXX get listings and binaries from the articles instead of the prg folder
      # read all listings in petcat format (and other binaries)
      listings = {}
      listings_bin = {}
      binaries = []
      prg_path = os.path.join(issue_directory_path, 'prg')
      for root, _, files in os.walk(prg_path):
          for file in files:
              if file.endswith('.txt'):
                  file_path = os.path.join(root, file)
                  basename = os.path.splitext(file)[0]
                  with open(file_path, 'r') as file_obj:
                      listings[basename] = file_obj.read()
                  listings_bin[basename] = petcat2prg(listings[basename])
              elif file.endswith('.seq') or file.endswith('.prg'):
                  src_path = os.path.join(root, file)
                  file_path = os.path.join('prg', file)
                  with open(src_path, 'rb') as file_obj:
                      listings_bin[file] = (file_obj.read(), None)
                  binaries.append(file_path)

      for root, dirs, files in os.walk(issue_directory_path):
          for file in files:
              if file.endswith('.html'):
                  article_path = os.path.join(root, file)
                  article_metadata = Issue.__read_html(article_path, listings, listings_bin)
                  articles.append(Article(article_metadata))

              elif file == 'toc.txt':
                  toc_order = Issue.__read_toc_order(os.path.join(root, file))
              elif file == 'pubdate.txt':
                  pubdate = Issue.__read_pubdate(os.path.join(root, file))
              elif file.endswith('.pdf'):
                  pdf_path = os.path.join(root, file)
                  pdf_filename = os.path.basename(pdf_path)

      # sort articles by page number
      def sort_by_page_number_and_toc_category(article):
        if article.toc_category == '': # editorial
            category_index = -1
        elif article.toc_category:
            if article.toc_category in toc_order:
                category_index = toc_order.index(article.toc_category)
            else:
                category_index = len(toc_order)
                raise Exception(f"- [{issue_directory_path}] ERROR: category not in toc.txt: '{article.toc_category}' ({article.title})")
        else: # no toc_category
            category_index = len(toc_order)
        return (article.article_sort_key(), category_index, article.title)

      sorted_articles = sorted(articles, key=lambda x: sort_by_page_number_and_toc_category(x))

      for index, article in enumerate(sorted_articles):
          #print((index, article.article_sort_key(), article.toc_category, article.title))
          article.sort_index = index
      articles = sorted_articles

      # get the issue key from the articles and check that all of them match
      for article in articles:
          if not issue_key:
              issue_key = article.issue_key
          else:
              if issue_key != article.issue_key:
                print("BAD", issue_key, article.issue_key)
              assert(issue_key == article.issue_key)

      if not pubdate:
          # no system exit as this also triggers for empty folders (eg. after branch change)
          raise AssertionError(f"- [{issue_directory_path}] Skipping: no pubdate")
      elif not (CONFIG.build_future or CONFIG.build_issues):
        # Define the current datetime with UTC timezone for comparison
          current_datetime = datetime.now(pytz.utc)

          # Remove the item if its publication date is in the future
          if pubdate > current_datetime:
              # no system exit
              raise AssertionError(f"- [{issue_directory_path}] Skipping: pubdate in the future")

      if not pdf_filename:
          print(f"- [{issue_directory_path}] Warning: Missing PDF")

      # XXX used directly after init and then never again
      self.articles = articles
      self.issue_key = issue_key

      self.toc_order = toc_order
      self.pubdate = pubdate
      self.pdf_filename = pdf_filename
      self.issue_dir_name = issue_dir_name
      self.listings = listings
      self.listings_bin = listings_bin
      self.binaries = binaries


  @staticmethod
  def __read_html(html_file_path, listings, listings_bin):
      """Parses an HTML file for article metadata and includes the filename."""
      with open(html_file_path, 'r', encoding='utf-8') as file:
          contents = file.read()

      soup = BeautifulSoup(contents, 'html.parser')

      def find_meta(name, is_optional=True): # panic if non optional
          meta_tag = soup.find('meta', attrs={'name': name})
          if meta_tag:
              return meta_tag['content']
          elif is_optional:
              return None
          else:
              raise SystemExit(f'\n---\nMetaDataError: "{name}" meta tag is missing\n   File: "{html_file_path}"')

      def find_title(): # panic if no title
          title_tag = soup.find('title')
          if title_tag:
              return title_tag.text
          else:
              raise SystemExit(f'\n---\nMetaDataError: title tag is missing\n   File: "{html_file_path}"')

      metadata = {
          'filename': os.path.basename(html_file_path), # XXX old
          'title': find_title(),
          'issue_key': find_meta('64er.issue', False),
          'pages': find_meta('64er.pages', False),
          'id': find_meta('64er.id', False),
          'head1': find_meta('64er.head1'),
          'head2': find_meta('64er.head2'),
          'toc_title': find_meta('64er.toc_title'),
          'toc_category': find_meta('64er.toc_category'),
          'index_title': find_meta('64er.index_title'),
          'index_category': find_meta('64er.index_category'),
          'path' : html_file_path,  # Include full path in metadata
      }

      metadata['target_filename'] = os.path.basename(metadata['id']) + '.html'

      # Put listings into <pre> tags and collect downloads
      downloads = []
      a_tags = []
      pre_tags = soup.find_all("pre")
      for tag in pre_tags:
          data_filename = tag.get("data-filename")
          data_name = tag.get("data-name")
          data_range = tag.get("data-range")
          data_availability = tag.get("data-availability")
          data_checksummer = tag.get("data-checksummer")
          data_mse = tag.get("data-mse")
          if data_mse and data_filename:
              data = listings_bin[data_filename][0]
              start = data[0] | (data[1] << 8)
              end = start + (len(data) - 2)
              lines = mse.MSEversions[data_mse](data_filename, start, end, mse.Memory(data[2:]))
              listing = "\n".join(lines)
              tag.string = listing

          elif data_filename:
              listing_bin, basicver = listings_bin[data_filename]
              # remove ';', empty lines and leading spaces
              listing = listings[data_filename]
              listing = [line.lstrip() for line in listing.splitlines() if line.strip() and not line.lstrip().startswith(';')]
              if data_range:
                  ranges = [(int(part.split('-')[0]), int(part.split('-')[-1])) for part in data_range.split(',')]
                  filtered_lines = []
                  blank_line_added = True
                  for line in listing:
                      leading_number = int(line.split(' ')[0])
                      if any(start <= leading_number <= end for start, end in ranges):
                          filtered_lines.append(line)
                          blank_line_added = False
                      else:
                          if not blank_line_added:
                              filtered_lines.append('')
                          blank_line_added = True
                  listing = filtered_lines

              if data_checksummer and listing_bin:
                  listing_64er = checksummer.parse(listing_bin, int(data_checksummer), basicver)
                  listing_html = ""
                  for (lineno, content, checksum) in listing_64er:
                      if data_range and not any(start <= lineno <= end for start, end in ranges):
                          continue
                      content = content.replace("&", "&amp;")
                      content = content.replace("<", "&lt;")
                      content = content.replace("\u0346", "<span class='cbm'>")
                      content = content.replace("\u033a", "<span class='shift'>")
                      content = content.replace("\ue000", "</span>")
                      listing_html += f"<span data-chksum='<{checksum:03d}>'>{lineno: 3d} {content} </span>\n"
                  listing = "\n".join(listing)
                  listing = listing.replace("&", "&amp;")
                  listing = listing.replace("<", "&lt;")
                  newhtml = f"""<div class="listing"><span class="controls"><input type="checkbox" role="switch" class="toggle" checked="checked" /></span>
                    <pre class="listing-petcat">{listing}</pre>
                    <pre class="listing-checksummer">{listing_html}</pre></div>
                  """
                  tag.replace_with(BeautifulSoup(newhtml, 'html.parser'))
              else:
                  listing = "\n".join(listing)
                  tag.string = listing

              if not any(item[0] == data_name for item in downloads): # duplicates
                  if data_availability != "local":
                      data_filename_escaped = urllib.parse.quote(data_filename)
                      downloads.append((data_name, f"prg/{data_filename_escaped}.prg"))

      ## additional binary downloads from the Programmservicediskette
      div_downloads = soup.find_all("div", { "class" : "binary_download" } )
      for tag in div_downloads:
          data_filename = tag.get("data-filename")
          data_name = tag.get("data-name")
          data_filename_escaped = urllib.parse.quote(data_filename)
          downloads.append((data_name, f"prg/{data_filename_escaped}"))
          tag.decompose()

      metadata['downloads'] = downloads

      # and make a "downloads" aside
      if downloads:
          aside_tag = soup.new_tag("aside", attrs={"class": "downloads"})
          for (label, url) in downloads:
              a_tag = soup.new_tag("a", href=url)
              a_tag.string = label
              a_tags.append(a_tag)
              aside_tag.append(a_tag)
          article_tag = soup.find("article")
          article_tag.append(aside_tag)

      # Extract article description
      intro_div = soup.find('p', {"class": "intro"})
      if intro_div:
          metadata['description'] = intro_div.text.strip()
      else:
          first_p = soup.find('p')
          if first_p:
              # Extract text, split into words, take the first 64, and join them back into a string
              words = first_p.text.split()
              metadata['description'] = ' '.join(words[:64]) + '...'
          else:
              metadata['description'] = ''


      # Extract all image URLs with their *source* names
      src_img_urls = [img['src'] for img in soup.find_all('img') if img.get('src')]
      metadata['src_img_urls'] = src_img_urls

      # In the HTML, change all img src paths from PNG to AVIF, with a JPEG fallback
      for img_tag in soup.find_all('img'):
          img_src = img_tag['src']
          if img_src.lower().endswith('.png'):
              img_tag.replace_with(avif_picture_tag(soup, img_tag['src'], img_tag.attrs))

      metadata['html'] = soup
      metadata['txt'] = html_to_text_preserve_paragraphs(soup.body);

      # Extract all image URLs with their *destination* names
      img_urls = [img['src'] for img in soup.find_all('img') if img.get('src')]
      metadata['img_urls'] = img_urls

      return metadata

  @staticmethod
  def __read_toc_order(toc_file_path):
      """Reads the TOC order from toc.txt file."""
      with open(toc_file_path, 'r', encoding='utf-8') as file:
          toc_order = [line.strip() for line in file.readlines() if line.strip()]
      return toc_order

  def __read_pubdate(file_path):
      with open(file_path, 'r') as file:
          date_str = file.readline().strip()
      return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


class ArticleDatabase:

    def __init__(self, in_directory):
        self.issues = {}  # Change to dictionary
        self.authors = set(())
        self.articles = []
        for issue_dir_name in sorted(os.listdir(in_directory)):
            if CONFIG.build_issues and issue_dir_name not in CONFIG.build_issues:
                continue

            issue_dir_path = os.path.join(in_directory, issue_dir_name)
            if os.path.isdir(issue_dir_path) and (re.match(r'^\d{4}$', issue_dir_name) or re.match(r'^SH\d{4}$', issue_dir_name)):

                try:
                    issue = Issue(issue_dir_path)

                except AssertionError as error:
                    print(error)
                    continue

                # Map issue key to issue data
                issue_key = issue.issue_key
                self.issues[issue_key] = issue
                self.articles.extend(issue.articles)

    def latest_regular_issue_key(self):
        return max(
            (k for k in self.issues.keys() if k[0].isdigit()),
            key=lambda k: self.issues[k].pubdate,
            default=None
        )

    def latest_special_issue_key(self):
        return max(
            (k for k in self.issues.keys() if not k[0].isdigit()),
            key=lambda k: self.issues[k].pubdate,
            default=None
        )

    def articles_by_index_categories(self, index_categories, issue_key=None):
        # toc_category hacks for Rubriken and Aktuell
        if index_categories == ["Aktuell|"]:
          filtered_articles = [ article for article in self.articles if ((not article.index_category and article.toc_category and article.toc_category == "Aktuell") or (article.index_category and article.index_category.startswith("Aktuell"))) and (issue_key is None or article.issue_key == issue_key)]

        elif index_categories == ["Rubriken|"]:
            filtered_articles = [ article for article in self.articles if article.toc_category and article.toc_category == "Rubriken" and (issue_key is None or article.issue_key == issue_key)]

        else:
            index_categories = tuple(index_categories)
            filtered_articles = [ article for article in self.articles if article.index_category and article.index_category.startswith(index_categories) and (issue_key is None or article.issue_key == issue_key)]

        return sorted(filtered_articles, key=lambda x: x.article_sort_key())

    def articles_by_toc_categories(self, toc_categories, issue_key=None):
        filtered_articles = [article for article in self.articles if article.toc_category in toc_categories and (issue_key is None or article.issue_key == issue_key)]
        return sorted(filtered_articles, key=lambda x: x.article_sort_key())

    def toc_with_articles(self, issue_key):
        issue = self.issues[issue_key]
        toc_entries = []

        toc_order = [""] + issue.toc_order # prepend empty category
        for toc in toc_order:
            articles = self.articles_by_toc_categories([toc], issue_key)
            articles_sorted = sorted(articles, key=lambda x: x.article_sort_key())
            toc_entries.append({
                'category': toc,
                'articles': articles_sorted
            })

        return toc_entries

    def articles_with_downloads(self):
        return [article for article in self.articles if article.is_category_listings()]

    def all_type_in_articles_grouped_by_index_category(self):
        # Initialize a dictionary to hold articles by category
        articles_by_category = defaultdict(list)

        # Filter articles with downloads and organize them
        for article in self.articles:
            index_category = article.index_category
            if article.is_category_listings():
                index_category = index_category[index_category.find('|') + 1:]
                articles_by_category[index_category].append(article)

        # Sort articles in each category by issue and then by first page number
        for category, articles_list in articles_by_category.items():
            articles_by_category[category] = sorted(articles_list, key=lambda x: (x.issue_key, x.article_sort_key()))

        sorted_categories = sorted(articles_by_category.items(), key=lambda x: x[0])
        return OrderedDict(sorted_categories)

### Helpers

def full_url(path):
    return RSS_BASE_URL + quote(BASE_DIR + path)

def article_path(issue, article, prepend_issue_dir=False):
    article_path = optional_issue_prefix(article.out_filename(), issue, prepend_issue_dir)
    return article_path

def article_link(db, article, title, prepend_issue_dir=False):
    issue = db.issues[article.issue_key]
    path = article_path(issue, article, prepend_issue_dir)
    return f"<a href='{path}'>{title}</a>"

def prg_link(issue, download):
    label, url = download
    url = os.path.join(issue.issue_dir_name, url)
    return f"<a href='{url}'>{label}</a>"

def index_title(article):
  index_title = article.index_title
  toc_title = article.toc_title
  title = article.title
  ret = index_title if index_title else toc_title if toc_title else title
  return ret

def toc_title(article):
  toc_title = article.toc_title
  title = article.title
  return toc_title if toc_title else title

def share_on_mastodon_link(title, url):
    mastodon_message = quote(f"{title}\n{url}\n{MASTODON_HASHTAGS}")
    return f"/{BASE_DIR}tootpick.html#text={mastodon_message}"

def optional_issue_prefix(path, issue, prepend_issue_dir=False):
    if prepend_issue_dir:
        path = os.path.join(issue.issue_dir_name, path)
    return path

### Reusable HTML generation

def html_generate_latest_issue(db, special):
    if special:
        latest_issue_key = db.latest_special_issue_key()
        label_current_issue = LABEL_CURRENT_SPECIAL_ISSUE
    else:
        latest_issue_key = db.latest_regular_issue_key()
        label_current_issue = LABEL_CURRENT_REGULAR_ISSUE
    latest_issue = db.issues[latest_issue_key]
    issue_dir_name = os.path.basename(latest_issue.issue_dir_name)
    latest_title_image = os.path.join(issue_dir_name, "title.jpg")
    latest_html = f'''
<h2>{label_current_issue}</h2>\n
<hr>
<a href="{issue_dir_name}">
    <img src="{latest_title_image}" alt="">
</a>
<p class="current_issue_download">Ausgabe {latest_issue_key}</p>\n
<p><a href="{issue_dir_name}" class="download_button">{LABEL_DOWNLOAD}</a></p>'''
    return latest_html

def html_generate_latest_downloads(db):
    articles_with_downloads = db.articles_with_downloads()
    sorted_articles = sorted(articles_with_downloads, key=lambda x: x.article_pubdate(), reverse=True)[:NEW_DOWNLOADS]
    html_parts = [f"<h2>{LABEL_LATEST_LISTINGS}</h2><hr><ul>"]

    for article in sorted_articles:
        link = article_link(db, article, index_title(article), True)
        html_parts.append(f"<li>{link}</li>")

    html_parts.append("</ul>")

    return ''.join(html_parts)

def html_generate_title_image(db, issue, width, prepend_issue_dir=False):
    title_jpg_path = optional_issue_prefix("title.jpg", issue, prepend_issue_dir)
    return f"<img src=\"{title_jpg_path}\" width=\"{width}\" alt=\"{MAGAZINE_NAME} {issue.issue_key}\">\n"


def html_generate_toc(db, issue_key, heading_level=1, prepend_issue_dir=False):
    html_parts = []
    if heading_level == 1:
        html_parts.append(f"<main>\n")
    html_parts.append(f"<h{heading_level}>{LABEL_ISSUE} {issue_key}</h{heading_level}>\n")

    issue = db.issues[issue_key]
    pdf_filename = optional_issue_prefix(issue.pdf_filename, issue, prepend_issue_dir)
    title_image = html_generate_title_image(db, issue, 300, prepend_issue_dir)

    title_image = f"""
<div class="download_full_pdf">
    <a href="{pdf_filename}">
        {title_image}
        <br>
        <div class=\"download_full_pdf_button\">
          <div class="download_icon"><img src="/{BASE_DIR}pdf.svg" alt="PDF"></div>
          <div class="download_label">{LABEL_DOWNLOAD_ISSUE_PDF}</div>
        </div>
    </a>
</div>\n
"""
    html_parts.append('<div class="toc_container">')
    html_parts.append(title_image)

    toc_entries = db.toc_with_articles(issue_key)

    last_category = None
    last_subcategory = None

    html_parts.append('<div class="toc">')

    for entry in toc_entries:
        if len(entry['articles']):
          category, subcategory, subsubcategory = (entry['category'].split('|', 2) + [None])[:3] if '|' in entry['category'] else (entry['category'], None, None)
          if category != last_category:
              if category != "":
                  html_parts.append(f"<h3>{category}</h3>\n")
              last_category = category
              last_subcategory = None
          if subcategory != last_subcategory:
              if subcategory:
                  html_parts.append(f"<h4>{subcategory}</h4>\n")
              last_subcategory = subcategory
          if subsubcategory:
              html_parts.append(f"<h4>{subsubcategory}</h4>\n")
          html_parts.append('<ul>\n')
          for article in entry['articles']:

              # link = article_link(db, article, toc_title(article), prepend_issue_dir) # XXX remove
              issue = db.issues[article.issue_key]
              path = article_path(issue, article, prepend_issue_dir)
              title = toc_title(article)
              first_page = article.first_page_number()

              link = f"""
              <a href='{path}'>
              <span class="title">{title}<span class="leaders" aria-hidden="true"></span></span> <span class="page"><span class="visually-hidden">Page&nbsp;</span>{first_page}</span>
              </a>
              """

              html_parts.append(f"<li>{link}</li>\n")
          html_parts.append("</ul>\n")
    html_parts.append("</div>\n")
    html_parts.append("</div>\n")

    if heading_level == 1:
        html_parts.append(f"</main>\n")
    return ''.join(html_parts)

### HTML file content creation

def html_generate_images_all_issues(db, special):
    html_parts = []

    if special:
        issue_keys = (k for k in db.issues.keys() if not k[0].isdigit())
    else:
        issue_keys = (k for k in db.issues.keys() if k[0].isdigit())

    for issue_key in sorted(issue_keys, key=lambda x: db.issues[x].pubdate, reverse=True):
        issue = db.issues[issue_key]
        title_image = html_generate_title_image(db, issue, 200, True)
        html_parts.append(f"<a href=\"{issue.issue_dir_name}\">{title_image}</a>\n")
    return ''.join(html_parts)

def html_generate_tocs_all_issues(db):
    # Once we have many "Sonderheft" issues, we may consider splitting
    # them into a separate main tab, i.e.
    # Ausgaben – Sonderhefte – Artikel – Listings
    html_parts = []
    html_parts.append(f"<main>\n")

    html_parts.append(f"<h1>{LABEL_ALL_ISSUES}</h1>\n")

    # top: all issue title images (first regular, then special)
    if db.latest_special_issue_key():
        html_parts.append(f"<h2>{LABEL_REGULAR_MAGAZINES}</h2>\n")
    html_parts.append(html_generate_images_all_issues(db, False))
    html_parts.append("<hr>\n")
    if db.latest_special_issue_key():
        html_parts.append(f"<h2>{LABEL_SPECIAL_MAGAZINES}</h2>\n")
        html_parts.append(html_generate_images_all_issues(db, True))
        html_parts.append("<hr>\n")

    # below: all TOCs
    for issue_key in sorted(db.issues.keys(), key=lambda x: db.issues[x].pubdate, reverse=True):
        html_parts.append(html_generate_toc(db, issue_key, 2, True))
        html_parts.append("<hr>\n")

    html_parts.append(f"</main>\n")
    return ''.join(html_parts)

def html_generate_articles_for_categories(db, index_categories, alphabetical, issue_key=None, append_issue_number=False):
    articles = db.articles_by_index_categories(index_categories, issue_key)
    if not articles:
        return None
    if alphabetical:
        articles = sorted(articles, key=lambda x: index_title(x).lower())

    html_parts = []
    html_parts.append(f"<ul>\n")
    for article in articles:
        if append_issue_number:
            issue_number = f" [{article.issue_key}]"
        else:
            issue_number = ""
        link = article_link(db, article, index_title(article), True)
        html_parts.append(f"<li>{link}{issue_number}</li>\n")
    html_parts.append("</ul>\n")
    return ''.join(html_parts)

def html_generate_all_articles_by_category(db):
    category_order = [ # related to TOPICS #TODO XXX translate
        "Aktuell|",
        "Listings zum Abtippen|Anwendung|",
        "Listings zum Abtippen|Grafik|",
        "Listings zum Abtippen|Spiel|",
        "Listings zum Abtippen|Tips & Tricks|",
        "Hardware-Test|",
        "Hardware|",
        "Kurse|",
        "Spiele-Test|",
        "So machen's andere|",
        "Software-Test|",
        "Software|",
        "Rubriken|" # toc_category
    ]

    html_parts = []
    html_parts.append(f"<main>\n")

    last_h2_title = None

    for index_category in category_order:
        index_category_title = index_category[:-1] #remove trailing |
        if '|' in index_category_title:
            h2_title, h3_title = index_category_title.split('|', 1)  # Split into h2 and h3 titles
        else:
            h2_title, h3_title = index_category_title, None

        html = html_generate_articles_for_categories(db, [index_category], True, None, True)
        if html:
            if h2_title != last_h2_title or h3_title is not None:
                if h2_title != last_h2_title:
                    html_parts.append(f"<h2>{h2_title}</h2>\n")
                    last_h2_title = h2_title  # Update last <h2> title used

                # Add <h3> if there's a specific title for it
                if h3_title:
                    html_parts.append(f"<h3>{h3_title}</h3>\n")
            html_parts.append(html)

    html_parts.append(f"</main>\n")
    return ''.join(html_parts)

def html_generate_all_downloads(db):
    articles_by_category = db.all_type_in_articles_grouped_by_index_category()

    # Start the HTML table
    html_table = "<table>\n"
    html_table += f"<tr><th>{LABEL_CATEGORY}</th><th>{LABEL_ARTICLE}</th><th>{LABEL_DOWNLOADS}</th></tr>\n"

    # Iterate over each category and its articles
    for index_category, articles_list in articles_by_category.items():
        for article in articles_list:
            link = article_link(db, article, index_title(article), True)
            issue_key = article.issue_key
            issue = db.issues[issue_key]

            # Construct the list of downloads
            downloads_list = ""
            for download in article.downloads:
                downloads_list += f"<li>{prg_link(issue, download)}</li>\n"

            # Add a row to the table for this article
            html_table += f"""
            <tr>
                <td class=\"listings_category\">
                    {index_category}
                </td>
                <td class=\"listings_link\">
                    {link}
                    <div class="download_issue">{issue_key}</div>
                </td>
                <td class=\"listings_download\">
                    <ul>{downloads_list}</ul>
                </td>
            </tr>\n"""

    # Close the HTML table
    html_table += "</table>"

    return '<main>' + html_table + '</main>'

def html_generate_article_preview(db, article):
    html_parts = []
    link_title = article_link(db, article, index_title(article), True)
    title = index_title(article)
    description = article.description if article.description else ''
    category = article.toc_category if article.toc_category else '' # XXX 'Uncategorized'
    issue_key = article.issue_key
    issue = db.issues[issue_key]
    pages = article.pages
    img_src = next((url for url in (article.img_urls if article.img_urls else [])), None)
    pubdate_unix = int(article.article_pubdate().timestamp())
    html_parts.append(f"<div class=\"article_link\" data-pubdate=\"{pubdate_unix}\">\n")
    if img_src:
        img_src = os.path.join(issue.issue_dir_name, img_src)
        soup = BeautifulSoup('', 'html.parser')
        picture_tag = avif_picture_tag(soup, img_src)
        link_img = article_link(db, article, picture_tag, True)
        html_parts.append(link_img)
    html_parts.append(f"<h2>{link_title}</h2>\n")
    html_parts.append(f"<hr>\n")
    html_parts.append(f"<p>{description}</p>\n")
    html_parts.append(f"<p class=\"article_category\">{category}</p>\n")
    html_parts.append(f"<p class=\"article_issue_and_pages\">{issue_key} {LABEL_PAGE} {pages}</p>\n")
    html_parts.append("</div>\n")
    return ''.join(html_parts)


def html_generate_all_article_previews(db):
    # Filter out specific articles
    articles = [article for article in db.articles if article.title not in ["Impressum", "Vorschau"]]

    # Sort by 'pubdate'
    articles = sorted(articles, key=lambda x: x.article_pubdate(), reverse=True)

    html_articles = []

    for article in articles:
        html_articles.append(html_generate_article_preview(db, article))

    return html_articles

### Write full HTML files

def write_full_html_file(db, path, title, preview_img, body_html, body_class, comments=False, additional_head_tags=''):
    latest_issue_path = db.issues[db.latest_regular_issue_key()].issue_dir_name
    impressum_path = os.path.join(latest_issue_path, f"{FILENAME_IMPRINT}.html")

    isso_id = path.removeprefix(OUT_DIRECTORY) # XXX hack :(
    url = RSS_BASE_URL + isso_id[1:]           # XXX hack :(

    if comments:
      isso_html1 = f"""
    <script
      data-isso="/isso/"
      data-isso-avatar="false"
      data-isso-lang="{LANG}"
      src="/isso/js/embed.min.js"
    ></script>
    <link rel="stylesheet" href="/isso/css/isso.css">
"""
      isso_html2 = f"""
      <div class="comments">
        <div id="isso-thread" data-isso-id="{isso_id}"></div>
      </div>
"""
    else:
      isso_html1 = ""
      isso_html2 = ""

      if not preview_img:
        preview_img = "logo.png"

    if CONFIG.deploy:
      fav_icon_html = f"""
        <link rel="icon" href="/{BASE_DIR}favicon.ico" sizes="32x32">
        <link rel="icon" href="/{BASE_DIR}fav/icon.svg" type="image/svg+xml">
        <link rel="apple-touch-icon" href="/{BASE_DIR}fav/apple-touch-icon.png">
        """
    else:
      fav_icon_html = f"""
        <link rel="icon" href="/{BASE_DIR}favicon-dev.ico" sizes="32x32">
        <link rel="icon" href="/{BASE_DIR}fav/icon-dev.svg" type="image/svg+xml">
        <link rel="apple-touch-icon" href="/{BASE_DIR}fav/apple-touch-icon-dev.png">
        """

    full_html = f"""
<!DOCTYPE html>
<html lang="{LANG}">
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="{title}">
    <meta property="og:image" content="{preview_img}">
    <title>{title}</title>

    {fav_icon_html}

    <link rel="stylesheet" href="/{BASE_DIR}style.css">
    <script>
      const BASE_DIR = '{BASE_DIR}';
    </script>
    <script src="/{BASE_DIR}lunr.js"></script>
    <script src="/{BASE_DIR}search.js"></script>
    <script src="/{BASE_DIR}mathjax/es5/tex-mml-chtml.js"></script>
    <script>
      if (window.isSecureContext) document.addEventListener("DOMContentLoaded", (event) => {{
        let copyBtn = document.createElement("span")
        copyBtn.innerHTML = "📋"
        copyBtn.addEventListener("click", () => {{
          let el = copyBtn.parentNode.parentNode.querySelector("pre.listing-petcat")
          navigator.clipboard.writeText(el.innerText)
        }})
        document.querySelectorAll("div.listing span.controls").forEach( (el) => {{
            el.appendChild(copyBtn)
        }})
      }})
    </script>


    {additional_head_tags}

    {isso_html1}
</head>

<body class="{body_class}">
<header class="page_navigation">
  <div class="logo_container">
    <a href="/{BASE_DIR}index.html">
      <img src="/{BASE_DIR}logo.png" alt="Logo" class="logo_image">
    </a>
  </div>
  <div class="nav_container">
    <div class="overview_container">
      <nav class="links_overview">
        <a href="/{BASE_DIR}{FILENAME_ISSUES}.html">{LABEL_ISSUES}</a>
        <a href="/{BASE_DIR}{FILENAME_ARTICLES}.html">{LABEL_ARTICLES}</a>
        <a href="/{BASE_DIR}{FILENAME_LISTINGS}.html">{LABEL_LISTINGS}</a>
      </nav>
      <div class="social_and_search">
        <a rel="me" href="https://mastodon.social/@64er">
          <img src="/{BASE_DIR}mastodon.svg" alt="Mastodon" class="social_image">
        </a>
        <a href="/{BASE_DIR}64er.rss">
          <img src="/{BASE_DIR}rss.svg" alt="RSS" class="social_image">
        </a>
        <form id="search-form" name="searchForm" onsubmit="return false">
          <input autocomplete="off" placeholder="{LABEL_SEARCH}" id="search" class="search-input" aria-label="Search site" type="text" name="q">
        </form>
      </div>
    </div>
    <div class="topics_container">
      <nav class="links_topics">
        <a href="/{BASE_DIR}{FILENAME_NEWS}.html">{LABEL_NEWS}</a>
        <a href="/{BASE_DIR}{FILENAME_HARDWARE}.html">{LABEL_HARDWARE}</a>
        <a href="/{BASE_DIR}{FILENAME_TESTS}.html">{LABEL_TESTS}</a>
        <a href="/{BASE_DIR}{FILENAME_SOFTWARE}.html">{LABEL_SOFTWARE}</a>
        <a href="/{BASE_DIR}{FILENAME_GAMES}.html">{LABEL_GAMES}</a>
        <a href="/{BASE_DIR}{FILENAME_PROGRAMS}.html">{LABEL_PROGRAMS}</a>
        <a href="/{BASE_DIR}{FILENAME_TUTORIALS}.html">{LABEL_TUTORIALS}</a>
        <a href="/{BASE_DIR}{FILENAME_IN_PRACTICE}.html">{LABEL_IN_PRACTICE}</a>
      </nav>
    </div>
  </div>
</header>

<div class="main_content">
{body_html}
{isso_html2}
</div>

<footer class="page_footer">
  <span class="left_text">© 1985 Markt & Technik Verlag Aktiengesellschaft</span>
  <nav class="right_nav">
    <a href="https://github.com/mist64/64er-magazin.de">{LABEL_CONTACT}</a>
    <a href="/{BASE_DIR}{impressum_path}">{LABEL_IMPRINT}</a>
    <a href="/{BASE_DIR}{FILENAME_PRIVACY}.html">{LABEL_PRIVACY}</a>
  </nav>
</footer>
</body>
</html>"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(full_html)


def generate_all_issues_with_tocs_html(db, out_directory):
    body_html = html_generate_tocs_all_issues(db)
    write_full_html_file(db, os.path.join(out_directory, f'{FILENAME_ISSUES}.html'), f'{LABEL_ALL_ISSUES} | {MAGAZINE_NAME}', None, body_html, 'all_issues')

def generate_issues_toc_html(db, issue_key, out_directory):
    body_html = html_generate_toc(db, issue_key, 1, False)
    issue_dest_path = os.path.join(out_directory, db.issues[issue_key].issue_dir_name)
    write_full_html_file(db, os.path.join(issue_dest_path, 'index.html'), f'{LABEL_TOC_ISSUE} {issue_key} | {MAGAZINE_NAME}', 'title.jpg', body_html, 'one_issue', True)

def generate_issues_tocs_html(db, out_directory):
    for issue_key in sorted(db.issues.keys(), key=lambda x: db.issues[x].pubdate, reverse=True):
        generate_issues_toc_html(db,  issue_key, out_directory)

def generate_all_topics_html(db, out_directory):
    body_html = html_generate_all_articles_by_category(db)
    write_full_html_file(db, os.path.join(out_directory, f'{FILENAME_ARTICLES}.html'), f'{LABEL_ALL_ARTICLES} | {MAGAZINE_NAME}', None, body_html, 'all_articles')

def generate_topic_htmls(db, out_directory):
    for topic, index_topics in TOPICS:
        filename = topic.lower() + ".html"

        html_parts = []
        html_parts.append(f"<main>\n")
        html_parts.append(f"<h1>{topic}</h1>\n")

        if topic == LABEL_TUTORIALS:
          html = html_generate_articles_for_categories(db, index_topics, True, append_issue_number=True);
          if html:
              html_parts.append(html)

        else:
          for issue_key in sorted(db.issues.keys(), key=lambda x: db.issues[x].pubdate, reverse=True):
              html = html_generate_articles_for_categories(db, index_topics, False, issue_key);
              if html:
                  html_parts.append(f"<h2>{LABEL_ISSUE} {issue_key}</h2>\n")
                  html_parts.append(html)

        html_parts.append(f"</main>\n")

        body_html = ''.join(html_parts)
        write_full_html_file(db, os.path.join(out_directory, filename), f'{topic} | {MAGAZINE_NAME}', None, body_html, 'one_topic')

def generate_all_downloads_html(db, out_directory):
    body_html = html_generate_all_downloads(db)
    write_full_html_file(db, os.path.join(out_directory, f'{FILENAME_LISTINGS}.html'), f'{LABEL_ALL_LISTINGS} | {MAGAZINE_NAME}', None, body_html, 'all_listings')

def generate_landing_html(db, out_directory):
    html_articles = html_generate_all_article_previews(db)

    html_parts = []
    html_parts.append(f"<main>\n")

    html_parts.append("<div class=\"column1\">\n")
    html_parts.append(''.join(html_articles))

    # Navigation links
    html_parts.append("<div class=\"article_navigation\">\n")
    html_parts.append(f"<a href=\"\" id=\"link_newer\">{LABEL_NEWER}</a>")
    html_parts.append(f"<a href=\"\" id=\"link_older\">{LABEL_OLDER}</a>")
    html_parts.append("</div>")

    html_parts.append("</div>") # Closing div for 'column1'


    html_parts.append("<div class=\"column2\">\n")
    html_parts.append("<div class=\"current_sidebox\">\n");
    html_parts.append(html_generate_latest_issue(db, False))
    html_parts.append("</div>")
    if db.latest_special_issue_key():
        html_parts.append("<div class=\"current_sidebox\">\n");
        html_parts.append(html_generate_latest_issue(db, True))
        html_parts.append("</div>")
    html_parts.append("<div class=\"listings_sidebox\">\n");
    html_parts.append(html_generate_latest_downloads(db))
    html_parts.append("</div>")
    html_parts.append("</div>") # Closing div for 'column2'

    html_parts.append(f"</main>\n")


    body_html = ''.join(html_parts)

    write_full_html_file(db, os.path.join(out_directory, 'index_all.html'), MAGAZINE_NAME_FULL, None, body_html, 'landing_pages')

def generate_privacy_page(db, out_directory):
        html_dest_path = os.path.join(out_directory, f"{FILENAME_PRIVACY}.html")
        title = LABEL_PRIVACY
        write_full_html_file(db, html_dest_path, title, None, HTML_PRIVACY, 'privacy')

def generate_404_page(db, out_directory):
        html_dest_path = os.path.join(out_directory, f"{FILENAME_404}.html")
        title = LABEL_404
        write_full_html_file(db, html_dest_path, title, None, HTML_404, 'page404')

### RSS

def generate_rss_feed(db, out_directory):
    rss_items = []

    sorted_articles = sorted(db.articles, key=lambda x: x.article_pubdate(), reverse=True)

    for article in sorted_articles:
        title = html.escape(index_title(article))
        issue = db.issues[article.issue_key]
        link = full_url(article_path(issue, article, True))
        description = article.description if article.description else ''
        img_src = article.img_urls[0] if article.img_urls else None
        if img_src:
            img_src = full_url(os.path.join(issue.issue_dir_name, img_src))
            img = f"<img src='{img_src}'><br>"
            description = img + description
        description = html.escape(description)
        pubdate = article.article_pubdate().strftime("%a, %d %b %Y %H:%M:%S %z")[:-5] + "GMT"

        rss_item_template = '''<item>
    <title>{title}</title>
    <link>{link}</link>
    <description>{description}</description>
    <pubDate>{pubdate}</pubDate>
</item>'''
        rss_items.append(rss_item_template.format(title=title, link=link, description=description, pubdate=pubdate))

    rss_base_url = RSS_BASE_URL + BASE_DIR

    rss_template = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>{magazine_name}</title>
    <link>{rss_base_url}</link>
    <description>{magazine_name}</description>
    <language>{lang}</language>
    {items}
</channel>
</rss>'''.format(rss_base_url=rss_base_url, magazine_name=MAGAZINE_NAME, lang=LANG, items=''.join(rss_items))

    with open(os.path.join(out_directory, '64er_all.rss'), 'w', encoding='utf-8') as f:
        f.write(rss_template)

###

def extract_pages_from_pdf(source_pdf_path, dest_pdf_path, page_descriptions, article_path):
    if page_descriptions == '999' or page_descriptions == '':
        print(f"- Warning: No page numbers: {article_path}")
        return
    cache_path = os.path.join(CACHE_DIRECTORY, calculate_sha1(source_pdf_path) + os.path.basename(dest_pdf_path))
    if os.path.exists(cache_path):
        shutil.copy(cache_path, dest_pdf_path)
    else:
        print(f"Not cached: {dest_pdf_path}")
        reader = PdfReader(source_pdf_path)
        writer = PdfWriter()

        for part in page_descriptions.split(','):
            if '-' in part:  # Range of pages
                start_page, end_page = map(int, part.split('-'))
                for page in range(start_page - 1, end_page):  # Convert to 0-based index
                    writer.add_page(reader.pages[page])
            else:  # Single page
                page = int(part) - 1  # Convert to 0-based index
                writer.add_page(reader.pages[page])

        with open(dest_pdf_path, 'wb') as out_pdf:
            writer.write(out_pdf)
        shutil.copy(dest_pdf_path, cache_path)

def is_bilevel_image(file_path):
    with Image.open(file_path) as img:
        return img.mode == '1'

def convert_and_copy_image(img_path, dest_img_path):
    _, file_extension = os.path.splitext(dest_img_path)
    cache_path = os.path.join(CACHE_DIRECTORY, calculate_sha1(img_path) + file_extension)
    if os.path.exists(cache_path):
        shutil.copy(cache_path, dest_img_path)
    else:
        print(f"Not cached: {dest_img_path}")
        try:
            if file_extension == ".jpg":
                quality = '80'
                bg_color = 'wheat'
                subprocess.run(['magick', img_path, '-strip', '-quality', quality, '-background', bg_color, '-alpha', 'remove',  '-alpha', 'off', dest_img_path], check=True)
            elif file_extension == ".avif":
                quality = '60'
                subprocess.run(['magick', img_path, '-strip', '-quality', quality, dest_img_path], check=True)

        except subprocess.CalledProcessError as e:
            print(f"Error running convert for image {img_path}: {e}")
        shutil.copy(dest_img_path, cache_path)


def copy_and_modify_html(article, html_dest_path, pdf_path, prev_page_link, next_page_link):
    """Modifies, and writes an HTML file directly to the destination."""
    soup = article.html
    issue_number = article.issue_key
    head1 = article.head1
    head2 = article.head2
    pages = article.pages
    issue = db.issues[issue_number]

    # Parse navigation HTML and prepare for insertion
    body = soup.find('body')

    # Insert the custom div after the navigation, if head1 or head2 is present
    head1 = head1 if head1 else ""
    head2 = head2 if head2 else ""
    custom_div_html = f'''
<div class="head_line">
<div class="head_line_head2">{head2}</div>
<div class="head_line_head1">{head1}</div>
<div class="head_line_logo"><a href="/{BASE_DIR}{issue.issue_dir_name}">{LOGO}</a></div><!--
--><div class="head_line_issue"><a href="/{BASE_DIR}{issue.issue_dir_name}">{issue_number}, {LABEL_PAGE} {pages}</a></div>
</a>
</div>
'''
    custom_div_soup = BeautifulSoup(custom_div_html, 'html.parser')
    body.insert(0, custom_div_soup)

    # Augment the Fehlerteufelchen <asides> with a full size Fehlerteufelchen
    asides = soup.find_all("aside", { "class" : "fehlerteufelchen" } )
    if asides:
      for aside in asides:
        ft_tag = BeautifulSoup(HTML_IMG_FEHLERTEUFELCHEN, 'html.parser')
        aside.insert(0, ft_tag)
    # Same with Futureteufelchen
    asides = soup.find_all("aside", { "class" : "futureteufelchen" } )
    if asides:
      for aside in asides:
        ft_tag = BeautifulSoup(HTML_IMG_FUTURETEUFELCHEN, 'html.parser')
        aside.insert(0, ft_tag)

    # Insert actions for downloading the pdf and tooting to mastooton
    download_pdf_html = f'''
<div class="article_action">
<a href="{pdf_path}">
<img src="/{BASE_DIR}pdf.svg" alt="PDF">
{LABEL_DOWNLOAD_ARTICLE_PDF}
</a>
</div>'''

    url = RSS_BASE_URL + html_dest_path.removeprefix(OUT_DIRECTORY)[1:] # XXX hack :(

    mastodon_link = share_on_mastodon_link(article.title, url)
    mastodon_html = f'''
<div class="article_action">
<a href="{mastodon_link}">
<img src="/{BASE_DIR}mastodon_blue.svg" alt="Mastodon">
{LABEL_SHARE_ON_MASTODON}
</a>
</div>'''

    article_actions_html = f'''
<div class="actions">
{download_pdf_html}
{mastodon_html}
</div>'''

    article_actions_soup = BeautifulSoup(article_actions_html, 'html.parser')
    body.append(article_actions_soup) # pdf download and mastodon

    nav_parts = []
    nav_parts.append("<div class=\"article_navigation\">\n")
    if prev_page_link:
        nav_parts.append(f"<a href='{prev_page_link}'>{LABEL_PREVIOUS_ARTICLE}</a>")
    if next_page_link:
        nav_parts.append(f"<a href='{next_page_link}'>{LABEL_NEXT_ARTICLE}</a>")

    nav_parts.append("</div>")
    nav_soup = BeautifulSoup(''.join(nav_parts), 'html.parser')
    body.append(nav_soup)

    body_html = str(soup.body)
    body_html = body_html[6:-7] # remove '<body>' and '</body>'
    title = f"{article.title} | {MAGAZINE_NAME}"
    preview_img = next((url for url in (article.img_urls if article.img_urls else [])), None)


    # add ls-json schema.com information
    #! TODO: re-add the meta tags
    # metas = soup.find_all('meta', {"name": True})

    def create_ls_json(title, image_url, date_published, date_modified, authors):
        if not image_url:
            image_url = "logo.png"

        def author_tag(author_name, author_url):
            if not author_url:
              author_url = ""
              #! TODO: add author url:
              # ,
              # "url": "{author_url}"

            author_json = f'''
            {{
              "@type": "Person",
              "name": "{author_name}"
            }}
            '''
            return author_json

        # author information
        authors_meta_list = soup.find_all('meta', {"name": "author"})
        authors = []
        for authors_meta in authors_meta_list:
            authors.extend([ author.strip() for author in authors_meta["content"].split(',')])

        if authors:
            db.authors.update(authors)
            authors_json_list = [author_tag(author, "") for author in authors]
            authors_json = f''', "author": [{", ".join(authors_json_list)}]'''
        else:
            authors_json = ""

        ls_json = f'''
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "image": [ "{image_url}" ],
      "datePublished": "{date_published}",
      "dateModified": "{date_published}"
      {authors_json}
    }}
    '''
        return ls_json

    past_pubtime = article.article_pubdate() - relativedelta(years=40)
    iso_date_published = past_pubtime.strftime("%a, %d %b %Y %H:%M:%S %z")[:-5] + "GMT"
    ls_json = create_ls_json(article.title, preview_img, iso_date_published, iso_date_published, "")
    head_html = f'<script type="application/ld+json">{ls_json}</script>'

    write_full_html_file(db, html_dest_path, title, preview_img, body_html, 'one_article', True, head_html)

def copy_articles_and_assets(db, in_directory, out_directory):
    if not os.path.exists(out_directory):
        os.makedirs(out_directory)

    # copy globals: images, stylesheet, javascript and fonts
    shutil.copy(os.path.join(in_directory, 'logo.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'logo.png'), out_directory)
    shutil.copy(os.path.join(in_directory, 'fehlerteufelchen.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'futureteufelchen.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'mastodon.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'mastodon_blue.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'rss.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'pdf.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'style.css'), out_directory)
    shutil.copy(os.path.join(in_directory, 'search.js'), out_directory)
    shutil.copy(os.path.join(in_directory, 'lunr.js'), out_directory)

    fav_path = os.path.join(in_directory,'fav')
    fav_path_out = os.path.join(out_directory,'fav')

    if not os.path.exists(fav_path_out):
        os.makedirs(fav_path_out)

    if CONFIG.deploy:
        shutil.copy(os.path.join(in_directory, 'favicon.ico'), out_directory)
        shutil.copy(os.path.join(fav_path, 'apple-touch-icon.png'), fav_path_out)
        shutil.copy(os.path.join(fav_path, 'icon.svg'), fav_path_out)
    else:
        shutil.copy(os.path.join(in_directory, 'favicon-dev.ico'), out_directory)
        shutil.copy(os.path.join(fav_path, 'apple-touch-icon-dev.png'), fav_path_out)
        shutil.copy(os.path.join(fav_path, 'icon-dev.svg'), fav_path_out)

    shutil.copy('filter_rss.py', out_directory)
    shutil.copy('filter_index.py', out_directory)
    shutil.copy('tootpick.html', out_directory)
    shutil.copytree('mathjax', out_directory + '/mathjax/')

    # Copy the complete "fonts" folder
    fonts_source_path = os.path.join(in_directory, "fonts")
    fonts_dest_path = os.path.join(out_directory, "fonts")
    if os.path.exists(fonts_source_path):
        shutil.copytree(fonts_source_path, fonts_dest_path, dirs_exist_ok=True)

    for issue_key in db.issues.keys():
        issue = db.issues[issue_key]
        print(f"  *** Issue {issue_key}")
        issue_source_path = os.path.join(in_directory, issue.issue_dir_name)
        issue_dest_path = os.path.join(out_directory, issue.issue_dir_name)
        issue_dest_path_prg = os.path.join(issue_dest_path, 'prg')

        # Create sub-folder for each issue
        os.makedirs(issue_dest_path)
        os.makedirs(issue_dest_path_prg)

        # Copy title image
        title_image_path = os.path.join(issue_source_path, TITLE_IMAGE_NAME)
        if os.path.exists(title_image_path):
            shutil.copy(title_image_path, issue_dest_path)
        else:
            convert_and_copy_image(os.path.join(issue_source_path, 'title.png'), os.path.join(issue_dest_path, 'title.jpg'))

        pdf_filename = issue.pdf_filename
        if pdf_filename:
            # Copy full PDF
            shutil.copy(os.path.join(issue_source_path, pdf_filename), issue_dest_path)

        # Create .PRG from Petcat listings
        for key, listing in issue.listings.items():
            # Prepare the output file name
            output_file_name = os.path.join(issue_dest_path, 'prg', f"{key}.prg")
            petcat2prg(listing, output_file_name)


        for binary_path in issue.binaries:
            input_file_name = os.path.join(issue_source_path, binary_path)
            output_file_name = os.path.join(issue_dest_path, binary_path)
            shutil.copy(input_file_name, output_file_name)


        # Copy all images of all articles of the issue and downloads
        articles = [article for article in db.articles if article.issue_key == issue_key]
        article_index = 0
        for article in sorted(articles, key=lambda x: x.sort_index):
            # Copy images found in article metadata
            img_srcs = article.src_img_urls if article.src_img_urls else []
            for img_src in img_srcs:
                img_path = os.path.join(issue_source_path, img_src)
                if os.path.exists(img_path):
                    _, file_extension = os.path.splitext(img_path)
                    if file_extension == ".svg":
                        dest_img_name = os.path.basename(img_path)
                        dest_img_path = os.path.join(issue_dest_path, dest_img_name)
                        shutil.copy(img_path, dest_img_path)
                    else:
                        dest_img_name = os.path.splitext(os.path.basename(img_path))[0] + '.avif'
                        dest_img_path = os.path.join(issue_dest_path, dest_img_name)
                        convert_and_copy_image(img_path, dest_img_path)
                        dest_img_name = os.path.splitext(os.path.basename(img_path))[0] + '.jpg'
                        dest_img_path = os.path.join(issue_dest_path, dest_img_name)
                        convert_and_copy_image(img_path, dest_img_path)

            # Copy files from the downloads
#            for _, download_url in article.downloads:
#                # Assuming download_url is a relative path; adjust logic if it's a URL
#                download_path = os.path.join(issue_source_path, download_url)
#                shutil.copy(download_path, issue_dest_path_prg)

            pages = article.pages

            # create PDF with just the article
            if pdf_filename:
                source_pdf_path = os.path.join(issue_source_path, pdf_filename)
                pdf_path = pdf_filename[:-4] + '_' + pages + '.pdf'
                dest_pdf_path = os.path.join(issue_dest_path, pdf_path)

                extract_pages_from_pdf(source_pdf_path, dest_pdf_path, pages, article.path)

            if article_index > 0:
                prev_page_link = articles[article_index - 1].target_filename
            else:
                prev_page_link = None
            if article_index < len(articles) - 1:
                next_page_link = articles[article_index + 1].target_filename
            else:
                next_page_link = None

            # Process and copy HTML files with navigation header etc.
            html_dest_path = os.path.join(issue_dest_path, article.target_filename)
            copy_and_modify_html(article, html_dest_path, pdf_path, prev_page_link, next_page_link)
            article_index += 1

def html_to_text_preserve_paragraphs(soup):
    block_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'li', 'tr', 'td']
    text_parts = []

    def process_string(elem):
        clean_text = html.unescape(elem.strip())
        if clean_text:  # Avoid adding empty strings
            text_parts.append(clean_text)

    def process_block_element(elem):
        # Directly handle block elements without nested block tags
        clean_text = html.unescape(elem.get_text(separator=' ', strip=True))
        if clean_text:  # Add newline for block elements
            text_parts.append(clean_text + '\n')

    # Handle strings
    for string in soup.find_all(string=True):
        if isinstance(string, NavigableString):
            process_string(string)

    # Handle block elements
    for tag_name in block_tags:
        for elem in soup.find_all(tag_name):
            process_block_element(elem)

    # Ensure the final text does not have redundant newlines
    final_text = '\n'.join(filter(None, text_parts))
    return final_text.strip()

def generate_search_json(db, out_directory):
    articles_info = []

    for article in db.articles:
        issue_key = article.issue_key
        issue = db.issues[issue_key]
        title = index_title(article)
        article_dict = {
            'categories': article.toc_category,
            'content': article.txt,
            'href': f"/{BASE_DIR}{issue.issue_dir_name}/{article.id}.html",  # Construct link with issue ID and filename
            'title': f"{title} [64'er {issue_key}]"
        }
        articles_info.append(article_dict)

    # Save the array as JSON
    with open(os.path.join(out_directory, 'search.json'), 'w', encoding='utf-8') as f:
        json.dump(articles_info, f, ensure_ascii=False, indent=4)
    with gzip.open(os.path.join(out_directory, 'search.json.gz'), 'wt') as f:
        json.dump(articles_info, f, ensure_ascii=False, indent=4)

    idx = lunr.lunr(
        ref='href',
        fields=['title', 'categories', 'content'],
        documents=articles_info,
    )
    serialized_idx = idx.serialize()
    with open(os.path.join(out_directory, 'search_idx.json'), 'w', encoding='utf-8') as f:
        json.dump(serialized_idx, f, ensure_ascii=False)
    with gzip.open(os.path.join(out_directory, 'search_idx.json.gz'), 'wt') as f:
        json.dump(serialized_idx, f, ensure_ascii=False)

def generate_author_pages(db, out_directory):
    known_authors = {}
    known_authors["aa"] = "Albert Absmeier"
    known_authors["ev"] = "Volker Everts"
    known_authors["gk"] = "Georg Klinge"
    known_authors["kg"] = "Karin Gößlinghoff"
    known_authors["py"] = "Michael M. Pauly"
    known_authors["rg"] = "Christian Rogge"
    known_authors["sc"] = "Michael Scharfenberger"

    # the shorthands that are in the magazine but not in the imprint and
    # XXX is the marker for author tags that are not set
    unknown_authors = ["ai", "wg", "XXX"]

    found_authors = [author for author in sorted(db.authors) if author not in unknown_authors]
    #print(found_authors)


if __name__ == '__main__':
    print("*** Generating")

    db = ArticleDatabase(IN_DIRECTORY)

    if os.path.exists(OUT_DIRECTORY):
        shutil.rmtree(OUT_DIRECTORY)
    os.makedirs(OUT_DIRECTORY)
    if not os.path.exists(CACHE_DIRECTORY):
        os.makedirs(CACHE_DIRECTORY)

    out_directory = os.path.join(OUT_DIRECTORY, BASE_DIR)

    copy_articles_and_assets(db, IN_DIRECTORY, out_directory)

    print("  *** Navigation")
    generate_all_issues_with_tocs_html(db, out_directory)
    generate_issues_tocs_html(db, out_directory)
    generate_all_topics_html(db, out_directory)
    generate_topic_htmls(db, out_directory)
    generate_all_downloads_html(db, out_directory)
    generate_landing_html(db, out_directory)
    generate_rss_feed(db, out_directory)
    generate_privacy_page(db, out_directory)
    generate_404_page(db, out_directory)
    generate_search_json(db, out_directory)
    generate_author_pages(db, out_directory)

    print("*** Filtering")
    dir = f"{OUT_DIRECTORY}/{BASE_DIR}"
    subprocess.run(['./filter_rss.py'], cwd=dir)
    subprocess.run(['./filter_index.py'], cwd=dir)

    if CONFIG.deploy:
        print("*** Uploading")
        command = f"rsync -Pa {OUT_DIRECTORY}/* local@{SERVER}:/var/www/html/"
        print("    " + command)
        ret = subprocess.run(command, check=True, text=True, shell=True)
        url = f"https://{SERVER}/{BASE_DIR}"
        print(url)
        subprocess.run(f"open {url}", check=True, text=True, shell=True)

    elif CONFIG.start_local_server:
        PORT = 8000
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=OUT_DIRECTORY, **kwargs)
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}/{BASE_DIR}"
            print(url)
            subprocess.run(f"open {url}", check=True, text=True, shell=True)
            httpd.serve_forever()
    else:
      port = 8000
      url = f"http://localhost:{port}/{CONFIG.base_dir}"
      print(url)
      subprocess.run(f"open {url}", check=True, text=True, shell=True)


