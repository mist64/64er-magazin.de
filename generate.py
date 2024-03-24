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
from collections import defaultdict
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import quote
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from PyPDF2 import PdfReader, PdfWriter

#
# Settings
#
LANG='de'
OUT_DIRECTORY = 'out'
SERVER = 'www.64er-magazin.de'
IMAGE_CONVERSION_TOOL = 'imagemagick' # 'guetzli'
EXTRACT_PDF_PAGES = True # disable for speed when testing
ARTICLES_PER_PAGE = 20
NEW_DOWNLOADS = 15

#
# Parse arguments
#
DEPLOY=None
if len(sys.argv) > 1:
    if sys.argv[1] == "local":
        DEPLOY = "local"
    elif sys.argv[1] == "upload":
        DEPLOY = "upload"
    else:
        print("Unknown command.")
        exit()

#
# if we're on "main", we will deploy to production, otherwise into a subdirectory
#
branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
RELEASE = branch_name == "main"
if RELEASE:
    BASE_DIR = ''
else:
    BASE_DIR = 'test/' + branch_name + '/'
if LANG != "de":
    BASE_DIR += '/' + LANG

if RELEASE and DEPLOY == "upload":
    response = input("Deploy to production? [Y/N]: ").strip()
    if response.lower() != 'y':
        print("Exiting.")
        exit()

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
  LABEL_CURRENT_ISSUE = "Das aktuelle Magazin"
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
  CATEGORY_TYPE_IN = "Programme zum Abtippen"
  TOPICS = [
      (LABEL_NEWS, ["Aktuell"]),
      (LABEL_HARDWARE, ["Hardware"]),
      (LABEL_TESTS, ["Test", "Spiele-Test"]),
      (LABEL_SOFTWARE, ["Software"]),
      (LABEL_GAMES, ["Programme zum Abtippen|Spiele"]),
      (LABEL_PROGRAMS, ["Programme zum Abtippen|Anwendungen", "Programme zum Abtippen|Grafik", "Programme zum Abtippen|Tips & Tricks"]),
      (LABEL_TUTORIALS, ["Kurse"]),
      (LABEL_IN_PRACTICE, ["So machen's andere"]),
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

  HTML_404 = """
    <main class="fehlerteufelchen">
    <h1>Seite nicht gefunden</h1>
    <img src="fehlerteufelchen.svg" alt="Fehlerteufelchen">
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
  LABEL_ALL_ARTICLES = "All Articles"
  LABEL_ALL_LISTINGS = "All Listings"
  LABEL_CURRENT_ISSUE = "Current Issue"
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
  CATEGORY_TYPE_IN = "Type-in Programs"
  TOPICS = [
    (LABEL_NEWS, ["News"]),
    (LABEL_HARDWARE, ["Hardware"]),
    (LABEL_TESTS, ["Test", "Game Tests"]),
    (LABEL_SOFTWARE, ["Software"]),
    (LABEL_GAMES, ["Type-in Programs|Games"]),
    (LABEL_PROGRAMS, ["Type-in Programs|Applications", "Type-in Programs|Graphics", "Type-in Programs|Tips & Tricks"]),
    (LABEL_TUTORIALS, ["Tutorials"]),
    (LABEL_IN_PRACTICE, ["How Others Do It"]),
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

  HTML_404 = """
    <main class="fehlerteufelchen">
    <h1>Page Not Found</h1>
    <img src="fehlerteufelchen.svg" alt="Error Devil">
    </main>
    """

LOGO = f'<img src="/{BASE_DIR}logo.svg" alt="{MAGAZINE_NAME}">'

###
### DATABASE
###

def first_page_number(pages_str):
    try:
        return int(pages_str.split(',')[0].split('-')[0])
    except ValueError:
        return float('inf')

def key_to_datetime(issue_key):
    month, year = map(int, issue_key.split('/'))
    # Handle century break properly if necessary
    year += 1900 if year >= 50 else 2000
    return datetime(year, month, 1)  # Assuming the first of the month

class ArticleDatabase:
    @staticmethod
    def __read_html(html_file_path):
        """Parses an HTML file for article metadata and includes the filename."""
        with open(html_file_path, 'r', encoding='utf-8') as file:
            contents = file.read()
        soup = BeautifulSoup(contents, 'html.parser')

        metadata = {
            'filename': os.path.basename(html_file_path), # XXX old
            'title': soup.find('title').text if soup.find('title') else 'No Title',
            'issue': soup.find('meta', attrs={'name': '64er.issue'})['content'] if soup.find('meta', attrs={'name': '64er.issue'}) else 'No Issue',
            'pages': soup.find('meta', attrs={'name': '64er.pages'})['content'] if soup.find('meta', attrs={'name': '64er.pages'}) else 'No Pages',
            'head1': soup.find('meta', attrs={'name': '64er.head1'})['content'] if soup.find('meta', attrs={'name': '64er.head1'}) else None,
            'head2': soup.find('meta', attrs={'name': '64er.head2'})['content'] if soup.find('meta', attrs={'name': '64er.head2'}) else None,
            'toc_title': soup.find('meta', attrs={'name': '64er.toc_title'})['content'] if soup.find('meta', attrs={'name': '64er.toc_title'}) else None,
            'toc_category': soup.find('meta', attrs={'name': '64er.toc_category'})['content'] if soup.find('meta', attrs={'name': '64er.toc_category'}) else None,
            'index_title': soup.find('meta', attrs={'name': '64er.index_title'})['content'] if soup.find('meta', attrs={'name': '64er.index_title'}) else None,
            'index_category': soup.find('meta', attrs={'name': '64er.index_category'})['content'] if soup.find('meta', attrs={'name': '64er.index_category'}) else None,
            'category': soup.find('meta', attrs={'name': '64er.category'})['content'] if soup.find('meta', attrs={'name': '64er.category'}) else None,
            'id': soup.find('meta', attrs={'name': '64er.id'})['content'] if soup.find('meta', attrs={'name': '64er.id'}) else None,
        }

        metadata['target_filename'] = os.path.basename(metadata['id']) + '.html'

        # Extract downloads information
        downloads_div = soup.find('aside', class_='downloads')
        downloads = []
        if downloads_div:
            for a in downloads_div.find_all('a', href=True):
                label = a.text.strip()
                url = a['href'].strip()
                downloads.append((label, url))
        metadata['downloads'] = downloads

        # Extract article description
        intro_div = soup.find('p', {"class": "intro"})
        metadata['description'] = intro_div.text.strip() if intro_div else None

        # Extract all image URLs with their *source* names
        src_img_urls = [img['src'] for img in soup.find_all('img') if img.get('src')]
        metadata['src_img_urls'] = src_img_urls

        # In the HTML, change all img src paths from PNG to JPG
        for img_tag in soup.find_all('img'):
            img_src = img_tag['src']
            if img_src.lower().endswith('.png'):
                img_tag['src'] = img_src[:-4] + '.jpg'

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

    @classmethod
    def __extract_issue_data(cls, issue_directory_path):
        """Extracts all relevant data from an issue directory, including HTML file paths."""
        articles_metadata = []
        toc_order = []
        pdf_path = None
        pdf_filename = None
        issue_path = issue_directory_path  # Capture the issue directory path
        issue_dir_name = os.path.basename(issue_directory_path)
        issue_key = None

        for root, dirs, files in os.walk(issue_directory_path):
            for file in files:
                if file.endswith('.html'):
                    article_path = os.path.join(root, file)
                    article_metadata = cls.__read_html(article_path)
                    article_metadata['path'] = article_path  # Include full path in metadata
                    articles_metadata.append(article_metadata)
                    if not issue_key:
                        issue_key = article_metadata['issue']
                    else:
                        assert(issue_key == article_metadata['issue'])
                elif file == 'toc.txt':
                    toc_order = cls.__read_toc_order(os.path.join(root, file))
                elif file == 'pubdate.txt':
                    pubdate = cls.__read_pubdate(os.path.join(root, file))
                elif file.endswith('.pdf'):
                    pdf_path = os.path.join(root, file)
                    pdf_filename = os.path.basename(pdf_path)

        return {
            'articles_metadata': articles_metadata,
            'toc_order': toc_order,
            'pubdate': pubdate,
            'pdf_filename': pdf_filename,
            'issue_dir_name': issue_dir_name,
            'issue_key': issue_key
        }

    def __init__(self, in_directory):
        self.issues = {}  # Change to dictionary
        self.articles = []
        for issue_dir_name in os.listdir(in_directory):
            issue_dir_path = os.path.join(in_directory, issue_dir_name)
            if os.path.isdir(issue_dir_path) and re.match(r'^\d{4}$', issue_dir_name):
                issue_data = self.__extract_issue_data(issue_dir_path)
                # Map issue key to issue data
                self.issues[issue_data['issue_key']] = {
                    'issue_dir_name': issue_dir_name,
                    'toc_order': issue_data['toc_order'],
                    'pubdate': issue_data['pubdate'],
                    'pdf_filename': issue_data['pdf_filename']
                }

                # Sort articles by page number within this issue before assigning indexes
                sorted_articles = sorted(issue_data['articles_metadata'], key=lambda x: first_page_number(x['pages']))

                for index, article in enumerate(sorted_articles):
                    # Modify to include issue key directly
                    article['issue_key'] = issue_data['issue_key']
                    article['out_filename'] = article['id'] + '.html'
                    # Assign an index based on sorted order
                    article['index'] = index
                    self.articles.append(article)

    def latest_issue_key(self):
        return max(self.issues.keys(), key=key_to_datetime)

    def articles_by_toc_categories(self, toc_categories, issue_key=None):
        filtered_articles = [article for article in self.articles if article.get('toc_category') in toc_categories and (issue_key is None or article['issue_key'] == issue_key)]
        return sorted(filtered_articles, key=lambda x: first_page_number(x['pages']))

    def toc_with_articles(self, issue_key):
        issue_data = self.issues[issue_key]
        toc_entries = []

        toc_order = [""] + issue_data['toc_order'] # prepend empty category
        for toc in toc_order:
            articles = self.articles_by_toc_categories([toc], issue_key)
            articles_sorted = sorted(articles, key=lambda x: first_page_number(x['pages']))
            toc_entries.append({
                'category': toc,
                'articles': articles_sorted
            })

        return toc_entries

    def articles_with_downloads(self):
        return [article for article in self.articles if article.get('index_category') and article.get('index_category').startswith(CATEGORY_TYPE_IN + '|') and article['downloads']]

    def all_type_in_articles_grouped_by_index_category(self):
        # Initialize a dictionary to hold articles by category
        articles_by_category = defaultdict(list)

        # Filter articles with downloads and organize them
        for article in self.articles:
            index_category = article.get('index_category')
            if index_category and index_category.startswith(CATEGORY_TYPE_IN + '|') and article.get('downloads'):
                index_category = index_category[index_category.find('|') + 1:]
                articles_by_category[index_category].append(article)

        # Sort articles in each category by issue and then by first page number
        for category, articles_list in articles_by_category.items():
            articles_by_category[category] = sorted(articles_list,
                                                    key=lambda x: (x['issue'],  first_page_number(x['pages'])))

        return dict(articles_by_category)

### Helpers

def full_url(path):
    return RSS_BASE_URL + quote(BASE_DIR + path)

def article_path(issue_data, article, prepend_issue_dir=False):
    article_path = article['out_filename']
    issue_dir = issue_data['issue_dir_name'] if prepend_issue_dir else None
    if issue_dir:
        article_path = os.path.join(issue_dir, article_path)
    return article_path

def article_link(db, article, title, prepend_issue_dir=False):
    issue_data = db.issues[article['issue_key']]
    path = article_path(issue_data, article, prepend_issue_dir)
    return f"<a href='{path}'>{title}</a>"

def prg_link(issue_data, download):
    label, url = download
    url = os.path.join(issue_data['issue_dir_name'], url)
    return f"<a href='{url}'>{label}</a>"

def index_title(article):
  index_title = article.get('index_title')
  toc_title = article.get('toc_title')
  title = article['title']
  return index_title if index_title else toc_title if toc_title else title

def toc_title(article):
  toc_title = article.get('toc_title')
  title = article['title']
  return toc_title if toc_title else title

def share_on_mastodon_link(title, url):
    mastodon_message = quote(f"{title}\n{url}\n{MASTODON_HASHTAGS}")
    return f"/{BASE_DIR}tootpick.html#text={mastodon_message}"

### Reusable HTML generation

def html_generate_latest_issue(db):
    latest_issue_key = db.latest_issue_key()
    latest_issue_data = db.issues[latest_issue_key]
    issue_dir_name = os.path.basename(latest_issue_data['issue_dir_name'])
    latest_title_image = os.path.join(issue_dir_name, "title.jpg")
    latest_html = f'''
<h2>{LABEL_CURRENT_ISSUE}</h2>\n
<hr>
<a href="{issue_dir_name}">
    <img src="{latest_title_image}">
</a>
<p class="current-issue-download">Ausgabe {latest_issue_key}</p>\n
<p><a href="{issue_dir_name}" class="download-button">{LABEL_DOWNLOAD}</a></p>'''
    return latest_html

def html_generate_latest_downloads(db):
    articles_with_downloads = db.articles_with_downloads()
    sorted_articles = sorted(articles_with_downloads, key=lambda x: (x['issue_key'], first_page_number(x['pages'])), reverse=True)[:NEW_DOWNLOADS]
    html_parts = [f"<h2>{LABEL_LATEST_LISTINGS}</h2><hr><ul>"]

    for article in sorted_articles:
        link = article_link(db, article, index_title(article), True)
        html_parts.append(f"<li>{link}</li>")

    html_parts.append("</ul>")

    return ''.join(html_parts)

def html_generate_title_image(db, issue_key, width, prepend_issue_dir=False):
    issue_data = db.issues[issue_key]
    title_jpg_path = "title.jpg"
    issue_dir = issue_data['issue_dir_name'] if prepend_issue_dir else None
    if issue_dir:
        title_jpg_path = os.path.join(issue_dir, title_jpg_path)
    return f"<img src=\"{title_jpg_path}\" width=\"{width}\" alt='{MAGAZINE_NAME} {issue_key}>\n"


def html_generate_toc(db, issue_key, heading_level=1, prepend_issue_dir=False):
    html_parts = []
    html_parts.append(f"<main>\n")
    html_parts.append(f"<h{heading_level}>{LABEL_ISSUE} {issue_key}</h{heading_level}>\n")
    pdf_filename = db.issues[issue_key]['pdf_filename']
    issue_data = db.issues[issue_key]
    issue_dir = issue_data['issue_dir_name'] if prepend_issue_dir else None
    if issue_dir:
        pdf_filename = os.path.join(issue_dir, pdf_filename)
    title_image = html_generate_title_image(db, issue_key, 300, prepend_issue_dir)
    title_image = f"""
<div class="download_full_pdf">
    <a href="{pdf_filename}">
        {title_image}
        <p>
            <div class=\"download_full_pdf_button\">
                <img src="/{BASE_DIR}pdf.svg" alt="PDF">
                {LABEL_DOWNLOAD_ISSUE_PDF}
            </div>
        </p>
    </a>
</div>\n
"""
    html_parts.append(title_image)

    issue_data = db.issues[issue_key]
    toc_entries = db.toc_with_articles(issue_key)

    last_category = None

    for entry in toc_entries:
        if len(entry['articles']):
          category, subcategory = (entry['category'].split('|', 1) + [None])[:2] if '|' in entry['category'] else (entry['category'], None)
          if category != last_category:
              html_parts.append(f"<h3>{category}</h3>\n")
              last_category = category
          if subcategory:
              html_parts.append(f"<h4>{subcategory}</h4>\n")
          html_parts.append("<ul>\n")
          for article in entry['articles']:
              link = article_link(db, article, toc_title(article), prepend_issue_dir)
              html_parts.append(f"<li>{link}</li>\n")
          html_parts.append("</ul>\n")
    html_parts.append(f"</main>\n")
    return ''.join(html_parts)

### HTML file content creation

def html_generate_tocs_all_issues(db):
    html_parts = []
    html_parts.append(f"<main>\n")

    html_parts.append(f"<h1>{LABEL_ALL_ISSUES}</h1>\n")

    # top: all issue title images
    for issue_key in sorted(db.issues.keys(), key=lambda x: key_to_datetime(x), reverse=True):
        title_image = html_generate_title_image(db, issue_key, 200, True)
        issue_dir = db.issues[issue_key]['issue_dir_name']
        html_parts.append(f"<a href=\"{issue_dir}\">{title_image}</a>\n")

    html_parts.append("<hr>\n")

    # below: all TOCs
    for issue_key in sorted(db.issues.keys(), key=lambda x: key_to_datetime(x), reverse=True):
        html_parts.append(html_generate_toc(db, issue_key, 2, True))
        html_parts.append("<hr>\n")

    html_parts.append(f"</main>\n")
    return ''.join(html_parts)

def html_generate_articles_for_categories(db, toc_categories, alphabetical, issue_key=None, append_issue_number=False):
    articles = db.articles_by_toc_categories(toc_categories, issue_key)
    if not articles:
        return None
    if alphabetical:
        articles = sorted(articles, key=lambda article: index_title(article).lower())

    html_parts = []
    html_parts.append(f"<ul>\n")
    for article in articles:
        issue_data = db.issues[article['issue_key']]
        if append_issue_number:
            issue_number = f" [{article['issue']}]"
        else:
            issue_number = ""
        link = article_link(db, article, index_title(article), True)
        html_parts.append(f"<li>{link}{issue_number}</li>\n")
    html_parts.append("</ul>\n")
    return ''.join(html_parts)

def html_generate_all_articles_by_category(db):
    category_order = [
        "Aktuell",
        "Hardware",
        "Test",
        "Software",
        "Spiele-Test",
        "Programme zum Abtippen|Anwendungen",
        "Programme zum Abtippen|Grafik",
        "Programme zum Abtippen|Spiele",
        "Programme zum Abtippen|Tips & Tricks",
        "Kurse",
        "Wettbewerbe",
        "So machen's andere",
        "Rubriken"
    ]

    html_parts = []
    html_parts.append(f"<main>\n")

    last_h2_title = None

    for toc_category in category_order:
        if '|' in toc_category:
            h2_title, h3_title = toc_category.split('|', 1)  # Split into h2 and h3 titles
        else:
            h2_title, h3_title = toc_category, None

        html = html_generate_articles_for_categories(db, [toc_category], True, None, True)
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
            issue_key = article['issue_key']
            issue_data = db.issues[issue_key]

            # Construct the list of downloads
            downloads_list = ""
            for download in article['downloads']:
                downloads_list += f"<li>{prg_link(issue_data, download)}</li>\n"

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
    description = article.get('description', '')
    category = article.get('toc_category', 'Uncategorized')
    issue_key = article['issue_key']
    issue_data = db.issues[issue_key]
    issue_dir_name = issue_data['issue_dir_name']
    pages = article['pages']
    img_src = next((url for url in article.get('img_urls', [])), None)
    html_parts.append(f"<div class=\"article_link\">\n")
    if img_src:
        img_src = os.path.join(issue_dir_name, img_src)
        link_img = article_link(db, article, f"<img src='{img_src}'>\n", True)
        html_parts.append(link_img)
    html_parts.append(f"<h2>{link_title}</h2>\n")
    html_parts.append(f"<hr>\n")
    html_parts.append(f"<p>{description}</p>\n")
    html_parts.append(f"<p class=\"article_category\">{category}</p>\n")
    html_parts.append(f"<p class=\"article_issue_and_pages\">{issue_key} {LABEL_PAGE} {pages}</p>\n")
    html_parts.append("</div>\n")
    return ''.join(html_parts)


def html_generate_all_article_previews(db):
    articles = sorted(db.articles, key=lambda x: (x['issue_key'], first_page_number(x['pages'])), reverse=True)
    # skip articles without category or description
    articles = [article for article in articles if article.get('toc_category')]
    articles = [article for article in articles if article.get('description')]
    articles = [article for article in articles if article['title'] != "Vorschau"] #XXX

    html_articles = []

    for article in articles:
        html_articles.append(html_generate_article_preview(db, article))

    return html_articles

### Write full HTML files

def write_full_html_file(db, path, title, preview_img, body_html, body_class, comments=False):
    latest_issue_path = db.issues[db.latest_issue_key()]['issue_dir_name']
    impressum_path = os.path.join(latest_issue_path, f"{FILENAME_IMPRINT}.html")

    isso_id = path.removeprefix(OUT_DIRECTORY) # hack :(
    url = RSS_BASE_URL + isso_id[1:]           # hack :(

    if comments:
      isso_html1 = f"""
    <script
      data-isso="/isso/"
      data-isso-avatar="false"
      data-isso-lang="{LANG}"
      src="/isso/js/embed.min.js"
    ></script>
    <link rel="stylesheet" href="/isso/css/isso.css" />
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

    mastodon_link = share_on_mastodon_link(title, url)

    full_html = f"""
<!DOCTYPE html>
<html lang="{LANG}">
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="{title}" />
    <meta property="og:image" content="{preview_img}" />
    <title>{title}</title>
    <link rel="stylesheet" href="/{BASE_DIR}style.css">
    <script>
      const BASE_DIR = '{BASE_DIR}';
    </script>
    <script src="/{BASE_DIR}lunr.js"></script>
    <script src="/{BASE_DIR}search.js"></script>
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
        <a href="{mastodon_link}">
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
  <span class="left-text">© 1984 Markt & Technik Verlag Aktiengesellschaft</span>
  <nav class="right-nav">
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
    write_full_html_file(db, os.path.join(out_directory, f'{FILENAME_ISSUES}.html'), f'{LABEL_ALL_ISSUES} | {MAGAZINE_NAME}', None, body_html, 'alle_ausgaben')

def generate_issues_toc_html(db, issue_key, out_directory):
    body_html = html_generate_toc(db, issue_key, 1, False)
    issue_dest_path = os.path.join(out_directory, db.issues[issue_key]['issue_dir_name'])
    write_full_html_file(db, os.path.join(issue_dest_path, 'index.html'), f'{LABEL_TOC_ISSUE} {issue_key} | {MAGAZINE_NAME}', 'title.jpg', body_html, 'eine_ausgabe', True)

def generate_issues_tocs_html(db, out_directory):
    for issue_key in sorted(db.issues.keys(), key=lambda x: key_to_datetime(x), reverse=True):
        generate_issues_toc_html(db,  issue_key, out_directory)

def generate_all_topics_html(db, out_directory):
    body_html = html_generate_all_articles_by_category(db)
    write_full_html_file(db, os.path.join(out_directory, f'{FILENAME_ARTICLES}.html'), f'{LABEL_ALL_ARTICLES} | {MAGAZINE_NAME}', None, body_html, 'alle_artikel')

def generate_topic_htmls(db, out_directory):
    for topic, toc_topics in TOPICS:
        filename = topic.lower() + ".html"

        html_parts = []
        html_parts.append(f"<main>\n")
        html_parts.append(f"<h1>{topic}</h1>\n")

        for issue_key in sorted(db.issues.keys(), key=lambda x: key_to_datetime(x), reverse=True):
            html = html_generate_articles_for_categories(db, toc_topics, False, issue_key);
            if html:
                html_parts.append(f"<h2>{LABEL_ISSUE} {issue_key}</h2>\n")
                html_parts.append(html)
        html_parts.append(f"</main>\n")

        body_html = ''.join(html_parts)
        write_full_html_file(db, os.path.join(out_directory, filename), f'{topic} | {MAGAZINE_NAME}', None, body_html, 'ein_thema')

def generate_all_downloads_html(db, out_directory):
    body_html = html_generate_all_downloads(db)
    write_full_html_file(db, os.path.join(out_directory, f'{FILENAME_LISTINGS}.html'), f'{LABEL_ALL_LISTINGS} | {MAGAZINE_NAME}', None, body_html, 'alle_listings')

def index_filename(i):
    if i == 1:
        return 'index.html'
    else:
        return f'new{i}.html'

def generate_all_article_links_html(db, out_directory, articles_per_page):
    html_articles = html_generate_all_article_previews(db)

    html_article_chunks = [html_articles[i:i + articles_per_page] for i in range(0, len(html_articles), articles_per_page)]

    for i, article_link_html in enumerate(html_article_chunks, start=1):
        html_parts = []
        html_parts.append(f"<main>\n")

        html_parts.append("<div class=\"column1\">\n")
        html_parts.append(''.join(article_link_html))

        # Navigation links
        if i > 1 or i < len(html_article_chunks): # There is a need for Navigation
            html_parts.append("<div class=\"article_navigation\">\n")

        if i > 1:  # There's a previous page
            prev_page_link = index_filename(i-1)
            html_parts.append(f"<a href='{prev_page_link}'>{LABEL_NEWER}</a>")
        if i < len(html_article_chunks):  # There's a next page
            next_page_link = index_filename(i+1)
            html_parts.append(f"<a href='{next_page_link}'>{LABEL_OLDER}</a>")

        if i > 1 or i < len(html_article_chunks): # There is a need for Navigation
            html_parts.append("</div>")

        html_parts.append("</div>") # Closing div for 'column1'


        html_parts.append("<div class=\"column2\">\n")
        html_parts.append("<div class=\"current_sidebox\">\n");
        html_parts.append(html_generate_latest_issue(db))
        html_parts.append("</div>")
        html_parts.append("<div class=\"listings_sidebox\">\n");
        html_parts.append(html_generate_latest_downloads(db))
        html_parts.append("</div>")
        html_parts.append("</div>") # Closing div for 'column2'

        html_parts.append(f"</main>\n")


        body_html = ''.join(html_parts)

        write_full_html_file(db, os.path.join(out_directory, index_filename(i)), MAGAZINE_NAME_FULL, None, body_html, 'landing_pages')

def generate_privacy_page(db, out_directory):
        html_dest_path = os.path.join(out_directory, f"{FILENAME_PRIVACY}.html")
        title = LABEL_PRIVACY
        write_full_html_file(db, html_dest_path, title, None, HTML_PRIVACY, 'datenschutz')

def generate_404_page(db, out_directory):
        html_dest_path = os.path.join(out_directory, f"{FILENAME_404}.html")
        title = LABEL_404
        write_full_html_file(db, html_dest_path, title, None, HTML_404, 'page404')

### RSS

def generate_rss_feed(db, out_directory):
    rss_items = []

    sorted_articles = db.articles # XXX

    for article in sorted_articles:
        title = article['title']
        issue_data = db.issues[article['issue_key']]
        link = full_url(article_path(issue_data, article, True))
        description = article['description']
        img_src = article['img_urls'][0] if article['img_urls'] else None
        if img_src:
            img_src = full_url(os.path.join(issue_data['issue_dir_name'], img_src))
            img = f"<img src='{img_src}'/><br/>"
            if description:
                description = img + description
            else:
                description = img
        if description:
            description = html.escape(description)
        else:
            description = ""

        pubdate = issue_data['pubdate']
        # Add index as half-days to the date
        pubdate += timedelta(hours=12 * article['index'])
        pub_date = pubdate.strftime("%a, %d %b %Y %H:%M:%S %z")[:-5] + "GMT"

        rss_item_template = '''<item>
    <title>{title}</title>
    <link>{link}</link>
    <description>{description}</description>
    <pubDate>{pub_date}</pubDate>
</item>'''
        rss_items.append(rss_item_template.format(title=title, link=link, description=description, pub_date=pub_date))

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

def extract_pages_from_pdf(source_pdf_path, dest_pdf_path, page_descriptions):
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

def convert_and_copy_image(img_path, issue_dest_path):
    dest_img_name = os.path.splitext(os.path.basename(img_path))[0] + '.jpg'
    dest_img_path = os.path.join(issue_dest_path, dest_img_name)

    try:
        if IMAGE_CONVERSION_TOOL == 'guetzli':
            # Guetzli for optimizing JPG images
            subprocess.run(['guetzli', '--quality', '84', img_path, dest_img_path], check=True)
        elif IMAGE_CONVERSION_TOOL == 'imagemagick':
            # ImageMagick for converting and/or optimizing images
            subprocess.run(['convert', img_path, '-quality', '85', dest_img_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {IMAGE_CONVERSION_TOOL} for image {img_path}: {e}")

def copy_and_modify_html(article, html_dest_path, pdf_path, prev_page_link, next_page_link):
    """Modifies, and writes an HTML file directly to the destination."""
    soup = article['html']
    issue_number = article['issue']
    head1 = article.get('head1')
    head2 = article.get('head2')
    pages = article.get('pages')

    # Parse navigation HTML and prepare for insertion
    body = soup.find('body')

    # Insert the custom div after the navigation, if head1 or head2 is present
    head1 = head1 if head1 else ""
    head2 = head2 if head2 else ""
    custom_div_html = f'''
<div class="head_line">
<div class="head_line_head2">{head2}</div>
<div class="head_line_head1">{head1}</div>
<div class="head_line_logo">{LOGO}</div>
<div class="head_line_issue">{issue_number}, {LABEL_PAGE} {pages}</div>
</div>
'''
    custom_div_soup = BeautifulSoup(custom_div_html, 'html.parser')
    body.insert(0, custom_div_soup)

    download_pdf_html = f'''
<div class="article_action">
<a href="{pdf_path}">
<img src="/{BASE_DIR}pdf.svg" alt="PDF">
{LABEL_DOWNLOAD_ARTICLE_PDF}
</a>
</div>'''

    url = RSS_BASE_URL + html_dest_path.removeprefix(OUT_DIRECTORY)[1:] # hack :(

    mastodon_link = share_on_mastodon_link(article['title'], url)
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
        # prev_page_link = index_filename(i-1)
        nav_parts.append(f"<a href='{prev_page_link}'>{LABEL_PREVIOUS_ARTICLE}</a>")
    if next_page_link:
        # next_page_link = index_filename(i+1)
        nav_parts.append(f"<a href='{next_page_link}'>{LABEL_NEXT_ARTICLE}</a>")

    nav_parts.append("</div>")
    nav_soup = BeautifulSoup(''.join(nav_parts), 'html.parser')
    body.append(nav_soup)

    body_html = str(soup.body)
    body_html = body_html[6:-7] # remove '<body>' and '</body>'
    title = f"{article['title']} | {MAGAZINE_NAME}"
    preview_img = next((url for url in article.get('img_urls', [])), None)


    write_full_html_file(db, html_dest_path, title, preview_img, body_html, 'ein_artikel', True)

def copy_articles_and_assets(db, in_directory, out_directory):
    if not os.path.exists(out_directory):
        os.makedirs(out_directory)

    # copy globals: images, stylesheet, javascript and fonts
    shutil.copy(os.path.join(in_directory, 'logo.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'logo.png'), out_directory)
    shutil.copy(os.path.join(in_directory, 'fehlerteufelchen.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'mastodon.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'mastodon_blue.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'rss.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'pdf.svg'), out_directory)
    shutil.copy(os.path.join(in_directory, 'style.css'), out_directory)
    shutil.copy(os.path.join(in_directory, 'search.js'), out_directory)
    shutil.copy(os.path.join(in_directory, 'lunr.js'), out_directory)
    shutil.copy('filter_rss.py', out_directory)
    shutil.copy('tootpick.html', out_directory)

    # Copy the complete "fonts" folder
    fonts_source_path = os.path.join(in_directory, "fonts")
    fonts_dest_path = os.path.join(out_directory, "fonts")
    if os.path.exists(fonts_source_path):
        shutil.copytree(fonts_source_path, fonts_dest_path, dirs_exist_ok=True)

    for issue_key in db.issues.keys():
        issue_data = db.issues[issue_key]
        issue_source_path = os.path.join(in_directory, issue_data['issue_dir_name'])
        issue_dest_path = os.path.join(out_directory, issue_data['issue_dir_name'])
        issue_dest_path_prg = os.path.join(issue_dest_path, 'prg')

        # Create sub-folder for each issue
        os.makedirs(issue_dest_path)
        os.makedirs(issue_dest_path_prg)

        # Copy title image
        shutil.copy(os.path.join(issue_source_path, TITLE_IMAGE_NAME), issue_dest_path)

        # Copy full PDF
        shutil.copy(os.path.join(issue_source_path, issue_data['pdf_filename']), issue_dest_path)

        # Copy all images of all articles of the issue and downloads
        articles = [article for article in db.articles if article['issue_key'] == issue_key]
        article_index = 0
        for article in articles:
            # Copy images found in article metadata
            img_srcs = article.get('src_img_urls', [])
            for img_src in img_srcs:
                img_path = os.path.join(issue_source_path, img_src)
                if os.path.exists(img_path):
                    convert_and_copy_image(img_path, issue_dest_path)

            # Copy files from the downloads
            downloads = article['downloads']
            for _, download_url in downloads:
                # Assuming download_url is a relative path; adjust logic if it's a URL
                download_path = os.path.join(issue_source_path, download_url)
                shutil.copy(download_path, issue_dest_path_prg)

            pages = article['pages']

            # create PDF with just the article
            pdf_filename = issue_data['pdf_filename']
            source_pdf_path = os.path.join(issue_source_path, pdf_filename)
            pdf_path = pdf_filename[:-4] + '_' + pages + '.pdf'
            dest_pdf_path = os.path.join(issue_dest_path, pdf_path)
            if EXTRACT_PDF_PAGES:
                extract_pages_from_pdf(source_pdf_path, dest_pdf_path, pages)

            if article_index > 0:
                prev_page_link = articles[article_index - 1]['target_filename']
            else:
                prev_page_link = None
            if article_index < len(articles) - 1:
                next_page_link = articles[article_index + 1]['target_filename']
            else:
                next_page_link = None

            # Process and copy HTML files with navigation header etc.
            html_dest_path = os.path.join(issue_dest_path, article['target_filename'])
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
        issue_key = article['issue_key']
        issue_data = db.issues[issue_key]
        issue_dir_name = issue_data['issue_dir_name']
        title = index_title(article)
        article_dict = {
            'categories': article.get('toc_category'),
            'content': article['txt'],
            'href': f"/{BASE_DIR}{issue_dir_name}/{article['id']}.html",  # Construct link with issue ID and filename
            'title': f"{title} [64'er {article['issue_key']}]"
        }
        articles_info.append(article_dict)

    # Save the array as JSON
    with open(os.path.join(out_directory, 'search.json'), 'w', encoding='utf-8') as f:
        json.dump(articles_info, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    print("*** Generating")

    db = ArticleDatabase(IN_DIRECTORY)

    if os.path.exists(OUT_DIRECTORY):
        shutil.rmtree(OUT_DIRECTORY)
    os.makedirs(OUT_DIRECTORY)

    out_directory = os.path.join(OUT_DIRECTORY, BASE_DIR)

    copy_articles_and_assets(db, IN_DIRECTORY, out_directory)
    generate_all_issues_with_tocs_html(db, out_directory)
    generate_issues_tocs_html(db, out_directory)
    generate_all_topics_html(db, out_directory)
    generate_topic_htmls(db, out_directory)
    generate_all_downloads_html(db, out_directory)
    generate_all_article_links_html(db, out_directory, ARTICLES_PER_PAGE)
    generate_rss_feed(db, out_directory)
    generate_privacy_page(db, out_directory)
    generate_404_page(db, out_directory)
    generate_search_json(db, out_directory)

    if DEPLOY == "upload":
        print("*** Uploading")
        command = f"rsync -Pa {OUT_DIRECTORY}/* local@{SERVER}:/var/www/html/"
        print("    " + command)
        ret = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        url = f"https://{SERVER}/{BASE_DIR}"
        print(url)
        subprocess.run(f"open {url}", check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    elif DEPLOY == "local":
        PORT = 8000
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=OUT_DIRECTORY, **kwargs)
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}/{BASE_DIR}"
            print(url)
            subprocess.run(f"open {url}", check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            httpd.serve_forever()

