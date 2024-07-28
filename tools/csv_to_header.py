import csv
import sys

def generate_meta_tags(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) < 4:
                continue  # Skip rows that do not have enough columns
            issue = row[0]
            page_number = row[1]
            title = row[4]
            category = f"{row[2]}|{row[3]}"
            print(f'{issue}, S.{page_number}')
            print(f'    <meta name="64er.index_title" content="{title}">')
            print(f'    <meta name="64er.index_category" content="{category}">')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_meta_tags.py <csv_file_path>")
        sys.exit(1)

    csv_file_path = sys.argv[1]
    generate_meta_tags(csv_file_path)