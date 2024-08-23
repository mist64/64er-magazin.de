import csv
import html
import sys

# top level categories in sort order
categories = [
    'Aktuell',
    'Listings zum Abtippen',
    'Hardware-Test',
    'Hardware',
    'Kurse',
    'Spiele-Test',
    'So machen’s andere',
    'Software-Test',
    'Software',
    'Wettbewerbe'
]

def print_table_row(entry):
    print('    <tr>')

    for v in entry:
        if v == '':
            v = '<br>'

        print(f'      <td>\n        <p>{v}</p>\n      </td>')

    print('    </tr>')

def generate_index_html(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        entries = []
        for row in reader:
            if len(row) < 4:
                continue  # Skip rows that do not have enough columns
            issue = row[0]
            page_number = row[1]
            title = row[4]
            category = row[2].split('|')
            category[0] = categories.index(category[0])
            if len(category) == 1:
                category.append('')
            category.append(row[3])

            # entry as list in sort key order
            entries.append([category, title, issue, page_number])

    entries.sort()

    active_category = ['' for _ in range(4)]

    print('<table border="1">\n  <tbody>')

    for entry in entries:
        category = entry[0]
        category[0] = categories[category[0]]
        for i in range(2):
            if category[i] != '' and category[i] != active_category[i]:
                print_table_row(['', f'<b>{html.escape(category[i])}</b>', '', ''])

        issue = f'{int(entry[2][2:])}/{entry[2][:2]}'
        row = [html.escape(category[2]), html.escape(entry[1]), entry[3], issue]

        if category[2] == active_category[2]:
            row[0] = ''

        active_category = category

        print_table_row(row)

    print('  </tbody>\n</table>\n<p><br></p>\n</body>\n</html>')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_index_html.py <csv_file_path>")
        sys.exit(1)

    csv_file_path = sys.argv[1]
    generate_index_html(csv_file_path)