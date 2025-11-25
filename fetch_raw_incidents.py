#!/usr/bin/env python3
"""
fetch_raw_incidents.py
Fetches incidents from a provided ServiceNow API URL (no preprocessing).
Writes:
 - raw JSON file
 - CSV with the specified columns (if present in JSON)
Config via .env: SN_API_URL, SN_PAT OR SN_USER+SN_PASS, CSV_OUTPUT, JSON_OUTPUT, PAGE_SIZE
"""

import os, time, csv, logging, json
from urllib.parse import urljoin
import requests
from dotenv import load_dotenv

load_dotenv()

SN_API_URL = os.getenv("SN_API_URL")  # Full API URL (use your provided URL)
SN_PAT = os.getenv("SN_PAT")
SN_USER = os.getenv("SN_USER")
SN_PASS = os.getenv("SN_PASS")
CSV_OUTPUT = os.getenv("CSV_OUTPUT", "./raw_incidents.csv")
JSON_OUTPUT = os.getenv("JSON_OUTPUT", "./raw_incidents.json")
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "200"))

if not SN_API_URL:
    raise SystemExit("Set SN_API_URL in .env (full API URL to fetch).")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("fetch_raw")

# Setup session / auth
sess = requests.Session()
headers = {"Accept": "application/json"}
if SN_PAT:
    headers["Authorization"] = f"Bearer {SN_PAT}"
    logger.info("Using SN_PAT for auth.")
elif SN_USER and SN_PASS:
    sess.auth = (SN_USER, SN_PASS)
    logger.info("Using Basic Auth.")
else:
    logger.info("No auth provided; attempting unauthenticated GET (may fail).")
sess.headers.update(headers)

def fetch_once(url):
    logger.info("GET %s", url)
    r = sess.get(url, timeout=60)
    logger.info("Status %s", r.status_code)
    r.raise_for_status()
    return r.json()

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Saved raw JSON to %s", path)

def save_csv_from_results(results, path, fields=None):
    if not isinstance(results, list):
        logger.warning("Expected list for results; got %s", type(results))
        return
    if not results:
        logger.info("No records to write to CSV.")
        return
    # Default fields if not provided
    if not fields:
        fields = ["number","sys_id","short_description","priority","state","assignment_group","assigned_to","opened_by","company","sys_created_on","sys_updated_on","link","age_days"]
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for rec in results:
            # write as-is; if nested objects exist (like assignment_group dict), dump them as string
            row = {}
            for fld in fields:
                val = rec.get(fld, "")
                # If value is dict or list, stringify it
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                row[fld] = val
            writer.writerow(row)
    logger.info("Saved CSV to %s", path)

def main():
    # If the API URL returns a top-level 'result' key (ServiceNow standard), use that.
    data = fetch_once(SN_API_URL)
    # auto-detect results array
    if isinstance(data, dict) and "result" in data:
        results = data["result"]
    elif isinstance(data, list):
        results = data
    else:
        # fallback: store full response in JSON and try to extract 'records' key if any
        results = []
        # Save raw anyway
    save_json(data, JSON_OUTPUT)
    # If we have results list, write CSV
    if isinstance(results, list):
        save_csv_from_results(results, CSV_OUTPUT)
    else:
        logger.info("No list of results found in response; JSON saved for inspection.")

if __name__ == "__main__":
    main()
