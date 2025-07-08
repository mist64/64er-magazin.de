#!/usr/bin/env python3

import os
import re
import csv
from collections import defaultdict
from bs4 import BeautifulSoup

def extract_author_codes_from_impressum(file_path):
    """Extract author codes from a single Impressum HTML file."""
    author_codes = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find paragraphs containing "Redakteure" or author codes
        for p in soup.find_all('p'):
            text = p.get_text()
            
            # Look for lines with author code patterns like "aa = Name" or "(py)" or "py = Name"
            if 'Redakteure:' in text or '=' in text:
                # Extract codes like "aa = Albert Absmeier", "py = Michael Pauly", etc.
                # Pattern matches: code = Full Name (optionally with phone number in parentheses)
                pattern = r'([a-z]{2})\s*=\s*([^(,]+?)(?:\s*\([^)]*\))?(?:,|$)'
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for code, name in matches:
                    code = code.lower().strip()
                    name = name.strip()
                    if len(code) == 2 and code.isalpha():
                        author_codes[code] = name
            
            # Also look for Chefredakteur and Stellv. Chefredakteur with codes in parentheses
            if 'Chefredakteur:' in text:
                # Pattern like "Michael M. Pauly (py)" or "Michael Scharfenberger (sc)"
                pattern = r'([A-Z][^(]*?)\s*\(([a-z]{2})\)'
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for name, code in matches:
                    code = code.lower().strip()
                    name = name.strip()
                    # Remove "Chefredakteur: " or "Stellv. Chefredakteur: " prefixes
                    name = re.sub(r'^.*?:\s*', '', name)
                    if len(code) == 2 and code.isalpha():
                        author_codes[code] = name
                        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return author_codes

def main():
    """Extract all author codes from all Impressum files."""
    issues_dir = 'issues'
    all_codes = defaultdict(set)  # Use set to track different name variations
    
    # Find all Impressum files
    impressum_files = []
    for root, dirs, files in os.walk(issues_dir):
        for file in files:
            if 'impressum' in file.lower() and file.endswith('.html'):
                impressum_files.append(os.path.join(root, file))
    
    print(f"Found {len(impressum_files)} Impressum files")
    
    # Extract codes from each file
    for file_path in sorted(impressum_files):
        issue = os.path.basename(os.path.dirname(file_path))
        codes = extract_author_codes_from_impressum(file_path)
        
        if codes:
            print(f"\n{issue}: {codes}")
            for code, name in codes.items():
                all_codes[code].add(name)
    
    # Compile final mapping from extracted data only
    final_mapping = {}
    
    # Use only codes found in Impressum files
    for code, names in all_codes.items():
        # If multiple name variations, pick the longest/most complete one
        best_name = max(names, key=len) if names else ""
        final_mapping[code] = best_name
    
    # Write CSV file
    csv_file = 'known_authors.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['code', 'name'])
        
        for code in sorted(final_mapping.keys()):
            writer.writerow([code, final_mapping[code]])
    
    print(f"\n✅ Generated {csv_file} with {len(final_mapping)} author codes:")
    for code in sorted(final_mapping.keys()):
        print(f"  {code}: {final_mapping[code]}")

if __name__ == '__main__':
    main()