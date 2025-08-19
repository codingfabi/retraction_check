import bibtexparser
import requests
import sys
import csv
import io
import difflib
from typing import List, Literal, TypedDict, Set, Optional

RETRACTION_WATCH_CSV = "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv"
MATCH_TYPE = Literal['doi', 'fuzzy']

class BibEntry(TypedDict, total=False):
    title: str
    author: str
    journal: str
    year: str
    doi: str
    # Add more fields as needed

def parse_bib_file(bib_path: str) -> List[BibEntry]:
    with open(bib_path, 'r') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    return bib_database.entries

def download_retraction_watch_csv() -> list:
    response = requests.get(RETRACTION_WATCH_CSV)
    response.raise_for_status()
    csvfile = io.StringIO(response.text)
    reader = csv.DictReader(csvfile)
    return list(reader)

def build_retraction_lookup(csv_rows):
    titles = set()
    dois = set()
    for row in csv_rows:
        title = row.get('Title', '').strip()
        if title:
            titles.add(title)
        if row.get('OriginalPaperDOI'):
            dois.add(row['OriginalPaperDOI'].strip())
    return titles, dois

def fuzzy_title_match(title, titles):
    if not title:
        return False
    matches = difflib.get_close_matches(title.strip(), titles, n=1)
    return bool(matches)

def is_retracted(entry: BibEntry, titles: Set[str], dois: Set[str]) -> Optional[MATCH_TYPE]:
    try:
        title = entry.get('title', '').strip()
        doi = entry.get('doi', '').strip()
    except Exception as e:
        print(f"Invalid entry encountered: {entry}. Error: {e}")
        return None
    if doi and doi in dois:
        return 'doi'
    if fuzzy_title_match(title, titles):
        return 'fuzzy'
    return None

def check_entry(entry, titles=None, dois=None):
    """
    Standalone function to check a single bibtex entry dict for retraction status.
    Downloads and builds lookup if titles/dois are not provided.
    Returns 'doi', 'fuzzy', or None.
    """
    if titles is None or dois is None:
        csv_rows = download_retraction_watch_csv()
        titles, dois = build_retraction_lookup(csv_rows)
    return is_retracted(entry, titles, dois)

def check_bib_file(bib_path: str):
    entries = parse_bib_file(bib_path)
    csv_rows = download_retraction_watch_csv()
    titles, dois = build_retraction_lookup(csv_rows)
    matches = {'doi': [], 'fuzzy': []}
    for entry in entries:
        match_type = is_retracted(entry, titles, dois)
        if match_type:
            matches[match_type].append(entry.get('title', 'Unknown Title'))
    if matches['doi']:
        print("Retracted papers found (DOI match):")
        for t in matches['doi']:
            print(f"- {t}")
    if matches['fuzzy']:
        print("\nRetracted papers found (fuzzy title match):")
        for t in matches['fuzzy']:
            print(f"- {t}")
    if not matches['doi'] and not matches['fuzzy']:
        print("No retracted papers found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m retraction_check.check_bib yourfile.bib")
        sys.exit(1)
    check_bib_file(sys.argv[1])
