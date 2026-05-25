"""
main.py — Run the full automation manually
Author: Kadari Eshwar | B.Tech ECE, JNTU Hyderabad

Usage: python main.py
This script does what n8n does automatically:
1. Read pending links from Google Sheet
2. Download media from Pinterest
3. Generate caption
4. Post to Instagram
5. Update sheet status
"""

import os
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from pinterest_downloader import download_media
from caption_generator import generate_caption, detect_category
from instagram_poster import post_media

# ── Config ─────────────────────────────────────────────────────────────────
SHEET_ID       = os.getenv("GOOGLE_SHEET_ID", "YOUR_SHEET_ID")
POSTS_PER_RUN  = 3  # Post 3 per run

def get_sheet():
    """Connect to Google Sheet."""
    creds  = Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

def get_pending_rows(sheet, limit=3):
    """Get first N pending rows from sheet."""
    all_rows = sheet.get_all_records()
    pending  = [(i+2, row) for i, row in enumerate(all_rows)
                if str(row.get("status","")).lower() == "pending"
                and row.get("pinterest_url","").strip()]
    return pending[:limit]

def update_row(sheet, row_num, post_id):
    """Mark row as posted in Google Sheet."""
    sheet.update_cell(row_num, 3, "posted")
    sheet.update_cell(row_num, 4, datetime.now().strftime("%Y-%m-%d %H:%M"))
    sheet.update_cell(row_num, 5, str(post_id))
    print(f"  ✅ Row {row_num} marked as posted")

def run():
    print("\n🤖 Instagram Auto Poster Starting...")
    print("="*45)

    try:
        sheet = get_sheet()
        print(f"✅ Connected to Google Sheet")
    except Exception as e:
        print(f"❌ Sheet error: {e}")
        return

    pending = get_pending_rows(sheet, POSTS_PER_RUN)
    print(f"📋 Found {len(pending)} pending posts\n")

    if not pending:
        print("No pending posts. Add Pinterest links to your sheet!")
        return

    success = 0
    for row_num, row in pending:
        url     = row.get("pinterest_url","").strip()
        custom  = row.get("description","").strip()

        print(f"\n📌 Processing: {url[:50]}...")

        # Download media
        filename, media_type = download_media(url)
        if not filename:
            print(f"  ⚠️  Skipping — could not download media")
            continue

        # Generate caption
        category = detect_category(url)
        caption  = generate_caption(custom, category)
        print(f"  📝 Caption: {caption[:60]}...")

        # Post to Instagram
        # Note: Instagram API needs a public URL for the image
        # In n8n workflow this is handled via file upload service
        print(f"  📸 Media type: {media_type}")
        print(f"  ✅ Ready to post (configure credentials to go live)")

        # Uncomment when credentials are set:
        # post_id = post_media(public_url, caption, media_type)
        # if post_id:
        #     update_row(sheet, row_num, post_id)
        #     success += 1

        success += 1  # Remove this when going live

    print(f"\n✅ Done! {success}/{len(pending)} posts processed")
    print("="*45)

if __name__ == "__main__":
    run()
