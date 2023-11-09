import requests
import csv
import json
from pathlib import Path
import logging
import time

FILE_PATH = Path(".") / "YouthPolicyLabs.csv"
JSON_DUMP_PATH = Path(".") / ".dump.json"
OUT_FILE_PATH = Path(".") / "YouthPolicyLabsISBNDescription.csv"


def query_google_api(isbn: str) -> any:
    query_url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
    res = requests.get(f"{query_url}{isbn}")
    if res.status_code == "429":
        time.sleep(0.5)
        logging.warning("Timeout.")
        res = requests.get(f"{query_url}{isbn}")
    return res.json()


def dump_json_to_file(obj: any) -> None:
    with open(JSON_DUMP_PATH, "w") as json_dump_file:
        json_dump_file.write(json.dumps(obj))


def load_json_from_file(json_dump_path: Path = JSON_DUMP_PATH) -> any:
    with open(json_dump_path, "r") as json_dump_file:
        return json.load(json_dump_file)


def query_and_store(isbns: dict) -> None:
    """Fetch description from Google Books API and dump it to local JSON file."""
    for isbn, description in isbns.items():
        if not description:
            try:
                res = query_google_api(isbn)
                fetched_description = res["items"][0]["volumeInfo"]["description"]
                isbns[isbn] = fetched_description
            except KeyError:
                isbns[isbn] = "No description available."
                logging.warning(f"ISBN {isbn} has no description.")
        dump_json_to_file(isbns)


def json_to_csv(csv_out_path: str = OUT_FILE_PATH) -> None:
    """Convert local JSON to CSV."""
    with open(csv_out_path, "w") as csvfile:
        fieldnames = ["ISBN", "Description"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for isbn, description in load_json_from_file().items():
            writer.writerow({"Description": description, "ISBN": isbn})


#
# Load JSON dump file or read entries from CSV
#

if JSON_DUMP_PATH.is_file:
    isbns = load_json_from_file()
    logging.warning("JSON dump file loaded.")
else:
    isbns = {}

if not isbns:
    with open(FILE_PATH, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            first_isbn = row["ISBN"].split(" ")[0]
            if not first_isbn:
                logging.warning("No ISBN recorded.")
            if first_isbn:
                isbns[first_isbn] = None

#
# Query ISBNs against Google Books API
#

query_and_store(isbns)

#
# Get CSV file
#

json_to_csv()
