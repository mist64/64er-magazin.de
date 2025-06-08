# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a retro web project recreating the 64'er Magazin website exactly 40 years after the original publication. It's a static site generator written in Python that converts magazine articles from HTML with metadata into a full website with search functionality, RSS feeds, and modern web features.

## Key Commands

### Development & Building
```bash
# Build the website
./generate.py

# Build and start local development server
./generate.py local

# Build with future issues included (for testing)
./generate.py --future local

# Deploy to production server
./generate.py upload

# Validate HTML output
./validate_html.sh
```

### Dependencies Setup
```bash
# Install system dependencies (macOS)
brew install imagemagick vice

# Python dependencies (use virtual environment)
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Architecture Overview

### Core Components

**Main Generator (`generate.py`)**
- Entry point that orchestrates the entire build process
- Parses CLI arguments and manages build configuration
- Handles three main modes: local development, production upload, and future content inclusion

**Article Database (`ArticleDatabase` class)**
- Scans `issues/` directory for magazine content
- Each issue is a subdirectory (e.g., `8404`, `8405`, `SH8501` for special issues)
- Parses HTML articles with structured metadata in `<meta>` tags
- Builds relationships between issues, articles, and categories

**Issue Structure (`Issue` class)**
- Each issue contains: articles (HTML), table of contents (`toc.txt`), publication date (`pubdate.txt`), PDF, and program listings
- Articles have metadata: issue number, pages, categories (TOC vs index), titles, downloads
- Supports both regular issues (`8404`) and special issues (`SH8501`)

### Content Processing Pipeline

1. **Article Parsing**: HTML files with embedded metadata are processed
2. **Image Conversion**: PNG images converted to AVIF/JPG with caching
3. **Listing Processing**: BASIC programs converted from petcat format to PRG files
4. **PDF Extraction**: Individual article PDFs extracted from full issue PDFs
5. **Static Generation**: Complete website with navigation, search index, RSS feeds

### Key File Types

**Article HTML**: Contains metadata in `<meta>` tags:
- `64er.issue`: Issue number (e.g., "4/84")  
- `64er.pages`: Page numbers (e.g., "10-11")
- `64er.toc_category`: Table of contents category
- `64er.id`: Unique article identifier

**Listings**: BASIC programs in petcat format with special metadata:
- `<pre data-filename="program.txt">` for BASIC listings
- Converted to downloadable .PRG files using VICE's petcat tool
- Support for checksummer format and MSE (machine language editor) format

**Configuration Files**:
- `toc.txt`: Defines category order for each issue
- `pubdate.txt`: Publication date in YYYY-MM-DD format
- `requirements.txt`: Python dependencies

## Development Workflow

### Adding New Issues
1. Create new directory under `issues/` (format: `YYMM` or `SHYYMM` for special issues)
2. Add `pubdate.txt` with publication date
3. Add `toc.txt` with category ordering
4. Add article HTML files with proper metadata
5. Include PDF and any program listings

### Working with Articles
- Articles use semantic HTML with embedded metadata
- Images should be PNG (will be auto-converted to AVIF/JPG)
- Program listings use `<pre>` tags with `data-filename` attributes
- Each article needs unique ID and proper categorization

### Testing Changes
- Use `./generate.py local` for local development
- Use `--future` flag to include unreleased content
- Validate output with `./validate_html.sh`
- Check generated search index and RSS feeds

## Special Features

**Retro Authenticity**: Website mimics 1984 design and includes original typos/errors
**Modern Enhancements**: Search functionality, RSS feeds, comment system (Isso), social sharing
**Accessibility**: Proper semantic HTML, alt text for images, keyboard navigation
**Performance**: AVIF image format, gzipped assets, efficient caching

## Build Output Structure
- `out/`: Generated website files
- `cache/`: Cached converted images and PDFs
- Issue directories contain: articles, images, PDFs, program downloads
- Global files: CSS, JavaScript, search indexes, RSS feeds

## Important Notes
- The project maintains historical accuracy by preserving original text including errors
- Publication dates are critical for RSS feed generation and content release scheduling
- Image conversion uses ImageMagick with specific quality settings for retro aesthetic
- Program listings support multiple formats (petcat, checksummer, MSE) for accuracy