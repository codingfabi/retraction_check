import bibtexparser
import requests
import sys
import csv
import io
import difflib
from typing import List, Literal, TypedDict, Set, Optional

RETRACTION_WATCH_CSV = (
    "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv"
)
MATCH_TYPE = Literal["doi", "fuzzy"]


class BibEntry(TypedDict, total=False):
    title: str
    author: str
    journal: str
    year: str
    doi: str


def parse_bib_file(bib_path: str) -> List[BibEntry]:
    try:
        with open(bib_path, "r", encoding="utf-8") as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
        if not bib_database.entries:
            print(
                f"Error: The .bib file '{bib_path}' is empty or contains no "
                f"valid entries."
            )
            return []
        return bib_database.entries  # type: ignore[no-any-return]
    except FileNotFoundError:
        print(f"Error: The .bib file '{bib_path}' was not found.")
        return []
    except UnicodeDecodeError:
        print(f"Error: The .bib file '{bib_path}' could not be decoded with utf-8.")
        return []
    except Exception as e:
        print(f"Error parsing .bib file '{bib_path}': {e}")
        return []


def download_retraction_watch_csv() -> list:
    try:
        response = requests.get(RETRACTION_WATCH_CSV)
        response.raise_for_status()
        csvfile = io.StringIO(response.text)
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        # Check for required columns
        fieldnames = reader.fieldnames or []
        if (
            not rows
            or "Title" not in fieldnames
            or "OriginalPaperDOI" not in fieldnames
        ):
            print(
                "Error: Retraction Watch CSV is missing required columns or "
                "is corrupted."
            )
            return []
        return rows
    except requests.RequestException as e:
        print(
            f"Error: Could not fetch Retraction Watch CSV file. "
            f"Connectivity issue or URL unreachable. Details: {e}"
        )
        return []
    except UnicodeDecodeError:
        print("Error: The Retraction Watch CSV file could not be decoded with utf-8.")
        return []
    except Exception as e:
        print(f"Error reading Retraction Watch CSV: {e}")
        return []


def build_retraction_lookup(
    csv_rows: list[dict[str, str]],
) -> tuple[set[str], set[str]]:
    titles = set()
    dois = set()
    for row in csv_rows:
        title = row.get("Title", "").strip()
        if title:
            titles.add(title)
        if row.get("OriginalPaperDOI"):
            dois.add(row["OriginalPaperDOI"].strip())
    return titles, dois


def fuzzy_title_match(title: str, titles: set[str]) -> bool:
    if not title:
        return False
    matches = difflib.get_close_matches(title.strip(), titles, n=1)
    return bool(matches)


def is_retracted(
    entry: BibEntry, titles: Set[str], dois: Set[str]
) -> Optional[MATCH_TYPE]:
    try:
        title = entry.get("title", "").strip()
        doi = entry.get("doi", "").strip()
    except Exception as e:
        print(f"Invalid entry encountered: {entry}. Error: {e}")
        return None
    if doi and doi in dois:
        return "doi"
    if fuzzy_title_match(title, titles):
        return "fuzzy"
    return None


def check_entry(
    entry: BibEntry,
    titles: Optional[set[str]] = None,
    dois: Optional[set[str]] = None,
) -> Optional[MATCH_TYPE]:
    """
    Standalone function to check a single bibtex entry dict for retraction status.
    Downloads and builds lookup if titles/dois are not provided.
    Returns 'doi', 'fuzzy', or None.
    """
    if titles is None or dois is None:
        csv_rows = download_retraction_watch_csv()
        titles, dois = build_retraction_lookup(csv_rows)
    return is_retracted(entry, titles, dois)


def check_bib_file(bib_path: str) -> None:
    entries = parse_bib_file(bib_path)
    csv_rows = download_retraction_watch_csv()
    titles, dois = build_retraction_lookup(csv_rows)
    matches: dict[str, list[str]] = {"doi": [], "fuzzy": []}
    for entry in entries:
        match_type = is_retracted(entry, titles, dois)
        if match_type:
            matches[match_type].append(entry.get("title", "Unknown Title"))
    if matches["doi"]:
        print("Retracted papers found (DOI match):")
        for t in matches["doi"]:
            print(f"- {t}")
    if matches["fuzzy"]:
        print("\nRetracted papers found (fuzzy title match):")
        for t in matches["fuzzy"]:
            print(f"- {t}")
    if not matches["doi"] and not matches["fuzzy"]:
        print("No retracted papers found.")


def main() -> None:
    """CLI entry point for the retraction-check command."""
    if len(sys.argv) < 2:
        print("Usage: retraction-check yourfile.bib")
        sys.exit(1)
    check_bib_file(sys.argv[1])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m retraction_check.check_bib yourfile.bib")
        sys.exit(1)
    check_bib_file(sys.argv[1])
