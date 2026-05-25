"""
main.py — Main automation script
Run by n8n 3 times daily (9AM, 1PM, 6PM IST)
Author: Kadari Eshwar

Set these environment variables in n8n or Render:
  SHEET_ID              — Google Sheet ID
  GOOGLE_API_KEY        — Google Sheets API key
  GOOGLE_ACCESS_TOKEN   — OAuth token for writing to sheet
  FB_PAGE_ID            — Facebook Page ID
  FB_PAGE_ACCESS_TOKEN  — Facebook Page Access Token
  IG_USER_ID            — Instagram Business User ID
"""

import os, sys, tempfile, requests
from pinterest_downloader import get_pinterest_media
from caption_generator     import generate_caption
from instagram_poster      import post_image, post_video
from sheet_manager         import get_pending_links, mark_as_posted, mark_as_error

# ── Config from environment variables ────────────────────────────────────
SHEET_ID     = os.environ.get("SHEET_ID", "")
GOOGLE_KEY   = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN", "")
FB_PAGE_ID   = os.environ.get("FB_PAGE_ID", "")
ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
IG_USER_ID   = os.environ.get("IG_USER_ID", "")
IMGBB_KEY    = os.environ.get("IMGBB_API_KEY", "")  # free image hosting

def upload_to_imgbb(file_path: str) -> str:
    """Upload image to imgbb.com (free) to get a public URL for Instagram API."""
    with open(file_path, "rb") as f:
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_KEY},
            files={"image": f}
        )
    data = r.json()
    if data.get("success"):
        url = data["data"]["url"]
        print(f"✅ Uploaded to imgbb: {url}")
        return url
    else:
        print(f"❌ imgbb upload failed: {data}")
        return ""

def run():
    print("\n🚀 Instagram Auto Poster Starting...")
    print("=" * 45)

    if not all([SHEET_ID, GOOGLE_KEY, ACCESS_TOKEN, IG_USER_ID]):
        print("❌ Missing environment variables! Check setup/04_run.md")
        sys.exit(1)

    # Step 1: Get 3 pending links from Google Sheet
    pending = get_pending_links(SHEET_ID, GOOGLE_KEY, limit=3)
    if not pending:
        print("⚠️  No pending links found in Google Sheet.")
        print("   Add more Pinterest links with status=pending")
        return

    # Step 2: Process each link
    posted_count = 0
    for item in pending:
        print(f"\n📌 Processing: {item['url']}")
        try:
            # Download from Pinterest
            with tempfile.TemporaryDirectory() as tmpdir:
                media = get_pinterest_media(item["url"], tmpdir)

                if not media["path"]:
                    mark_as_error(SHEET_ID, GOOGLE_KEY, GOOGLE_TOKEN, item["row"], "download failed")
                    continue

                # Generate caption
                caption = generate_caption(
                    title=media.get("title", ""),
                    custom=item.get("description", "")
                )
                print(f"📝 Caption: {caption[:60]}...")

                # Upload to imgbb for public URL
                public_url = upload_to_imgbb(media["path"])
                if not public_url:
                    mark_as_error(SHEET_ID, GOOGLE_KEY, GOOGLE_TOKEN, item["row"], "upload failed")
                    continue

                # Post to Instagram
                if media["type"] == "video":
                    result = post_video(IG_USER_ID, ACCESS_TOKEN, public_url, caption)
                else:
                    result = post_image(IG_USER_ID, ACCESS_TOKEN, public_url, caption)

                if "id" in result:
                    mark_as_posted(SHEET_ID, GOOGLE_KEY, GOOGLE_TOKEN, item["row"])
                    posted_count += 1
                    print(f"✅ Posted successfully! ({posted_count}/3)")
                else:
                    mark_as_error(SHEET_ID, GOOGLE_KEY, GOOGLE_TOKEN, item["row"], str(result)[:50])

        except Exception as e:
            print(f"❌ Error: {e}")
            mark_as_error(SHEET_ID, GOOGLE_KEY, GOOGLE_TOKEN, item["row"], str(e)[:50])

    print(f"\n🎉 Done! Posted {posted_count} posts today.")

if __name__ == "__main__":
    run()
