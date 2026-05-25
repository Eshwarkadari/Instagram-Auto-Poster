"""
sheet_manager.py
Read Pinterest links and update status in Google Sheet
Author: Kadari Eshwar

Sheet format:
  Col A: pinterest_url
  Col B: custom_description (optional)
  Col C: status (pending / posted / error)
  Col D: posted_date
"""

import requests
from datetime import datetime

# Google Sheets API (no auth needed if sheet is public)
SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

def get_pending_links(sheet_id: str, api_key: str, limit: int = 3) -> list:
    """
    Get up to `limit` pending Pinterest links from Google Sheet.
    Returns list of dicts: [{row, url, description}, ...]
    """
    url = f"{SHEETS_BASE}/{sheet_id}/values/A:D"
    r = requests.get(url, params={"key": api_key})
    data = r.json()

    if "values" not in data:
        print(f"❌ Sheet error: {data}")
        return []

    rows = data["values"]
    pending = []

    for i, row in enumerate(rows):
        if i == 0:
            continue  # skip header
        if len(row) < 1:
            continue

        url_val    = row[0].strip() if len(row) > 0 else ""
        desc_val   = row[1].strip() if len(row) > 1 else ""
        status_val = row[2].strip().lower() if len(row) > 2 else "pending"

        if url_val and status_val == "pending" and "pinterest" in url_val.lower():
            pending.append({
                "row":         i + 1,  # 1-indexed for Sheets API
                "url":         url_val,
                "description": desc_val,
            })

        if len(pending) >= limit:
            break

    print(f"✅ Found {len(pending)} pending links")
    return pending


def mark_as_posted(sheet_id: str, api_key: str, access_token_sheets: str, row: int):
    """Mark a row as posted in Google Sheet."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    url = f"{SHEETS_BASE}/{sheet_id}/values/C{row}:D{row}"
    body = {"values": [["posted", now]]}
    r = requests.put(
        url,
        params={"valueInputOption": "RAW", "key": api_key},
        headers={"Authorization": f"Bearer {access_token_sheets}"},
        json=body
    )
    if r.status_code == 200:
        print(f"✅ Row {row} marked as posted")
    else:
        print(f"❌ Could not update row {row}: {r.text}")


def mark_as_error(sheet_id: str, api_key: str, access_token_sheets: str, row: int, error: str):
    """Mark a row as error in Google Sheet."""
    url = f"{SHEETS_BASE}/{sheet_id}/values/C{row}:D{row}"
    body = {"values": [["error", error[:50]]]}
    requests.put(
        url,
        params={"valueInputOption": "RAW", "key": api_key},
        headers={"Authorization": f"Bearer {access_token_sheets}"},
        json=body
    )
