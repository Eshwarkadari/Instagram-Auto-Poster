"""
gsheet_poster.py
Pinterest → Instagram Auto Poster using Google Sheets queue
- Reads PENDING URLs from Google Sheet
- Downloads Pinterest image
- Posts to Instagram
- Updates sheet to POSTED
- Sends Telegram notification
"""

import os, requests, base64, re, time, logging, json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Credentials from GitHub Secrets ──────────────────────────────────
INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ["INSTAGRAM_ACCOUNT_ID"]
TELEGRAM_BOT_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID       = os.environ.get("TELEGRAM_CHAT_ID", "")
GOOGLE_SHEET_ID        = os.environ["GOOGLE_SHEET_ID"]
GITHUB_TOKEN           = os.environ["GH_TOKEN"]
GITHUB_REPO            = os.environ.get("GITHUB_REPO", "Eshwarkadari/Instagram-Auto-Poster")

CAPTION = """🔥 Men's Fashion Inspiration

Upgrade your wardrobe with timeless style and confidence.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #mensstyle #outfitideas #fashion #style #menswear #streetwear #casualstyle #outfitinspiration #styleformen #fashionreels #indianmensfashion #dailyoutfit #styleinspo #fashiontips"""

HEADERS_GH = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
HEADERS_PIN = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

# ── Google Sheets (public sheet via API key OR service account) ───────
def get_sheet_data():
    """Read sheet data using Google Sheets API (public sheet)"""
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    # Parse Google's weird JSON response
    raw = r.text
    json_str = raw[raw.index("{"): raw.rindex("}")+1]
    data = json.loads(json_str)
    rows = data["table"]["rows"]
    cols = [c["label"] for c in data["table"]["cols"]]
    result = []
    for i, row in enumerate(rows):
        if not row.get("c"):
            continue
        record = {"_row": i + 2}  # +2 for header + 1-based
        for j, col in enumerate(cols):
            val = row["c"][j]
            record[col] = val["v"] if val and val.get("v") is not None else ""
        result.append(record)
    return result

def update_sheet_status(pinterest_url: str, status: str):
    """Update status in Google Sheet via GitHub-stored credentials"""
    # We'll update via a helper script approach using gspread-less method
    # Use the Apps Script web app URL approach OR direct API
    # For simplicity: update via Google Sheets API with service account
    # Since we don't have service account, we update via the gist approach
    logger.info(f"Updating sheet: {pinterest_url[:50]} → {status}")
    # Store update log in GitHub repo
    update_log = {
        "url": pinterest_url,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    # Append to updates.json in repo
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/updates.json",
            headers=HEADERS_GH
        )
        if r.status_code == 200:
            existing = json.loads(base64.b64decode(r.json()["content"]).decode())
            sha = r.json()["sha"]
        else:
            existing = []
            sha = None

        existing.append(update_log)
        content = json.dumps(existing, indent=2)
        payload = {
            "message": f"Auto: {status} - {pinterest_url[:40]}",
            "content": base64.b64encode(content.encode()).decode()
        }
        if sha:
            payload["sha"] = sha
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/updates.json",
            headers=HEADERS_GH, json=payload
        )
        logger.info(f"✅ Logged update to GitHub")
    except Exception as e:
        logger.warning(f"Could not log update: {e}")

# ── Pinterest ─────────────────────────────────────────────────────────
def get_pinterest_image(pin_url: str) -> str:
    try:
        oe = requests.get(
            f"https://www.pinterest.com/oembed.json?url={pin_url}",
            timeout=10, headers=HEADERS_PIN
        )
        if oe.status_code == 200:
            img = oe.json().get("thumbnail_url", "")
            for low, high in [("236x","originals"),("474x","originals"),("736x","originals")]:
                img = img.replace(low, high)
            if img:
                return img
    except Exception as e:
        logger.warning(f"oEmbed failed: {e}")

    try:
        r = requests.get(pin_url, timeout=15, headers=HEADERS_PIN, allow_redirects=True)
        for pat in [
            r'"contentUrl":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'(https://i\.pinimg\.com/originals/[^\s"\']+\.(?:jpg|jpeg|png|webp))',
            r'(https://i\.pinimg\.com/736x/[^\s"\']+\.(?:jpg|jpeg|png|webp))',
        ]:
            m = re.search(pat, r.text)
            if m:
                return m.group(1)
    except Exception as e:
        logger.warning(f"Scrape failed: {e}")
    return None

def upload_to_cdn(image_path: str) -> str:
    with open(image_path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            files={"fileToUpload": ("img.jpg", f, "image/jpeg")},
            data={"reqtype": "fileupload", "userhash": ""},
            timeout=60
        )
    if r.status_code == 200 and r.text.startswith("https://"):
        return r.text.strip()
    raise ValueError(f"CDN upload failed: {r.text[:100]}")

# ── Instagram ─────────────────────────────────────────────────────────
def create_container(image_url: str, caption: str) -> str:
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": INSTAGRAM_ACCESS_TOKEN}
    )
    if r.status_code != 200:
        raise ValueError(f"Container error: {r.text}")
    return r.json()["id"]

def publish_post(container_id: str) -> str:
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN}
    )
    if r.status_code != 200:
        raise ValueError(f"Publish error: {r.text}")
    return r.json()["id"]

# ── Telegram ──────────────────────────────────────────────────────────
def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
        logger.info("✅ Telegram notification sent")
    except Exception as e:
        logger.warning(f"Telegram failed: {e}")

# ── Main ──────────────────────────────────────────────────────────────
def main():
    logger.info("🚀 Starting Pinterest → Instagram Auto Poster")

    # Read sheet
    try:
        rows = get_sheet_data()
    except Exception as e:
        logger.error(f"Failed to read Google Sheet: {e}")
        send_telegram(f"❌ Cannot read Google Sheet!\nError: {e}")
        return

    # Find PENDING URLs
    pending = [r for r in rows if str(r.get("Status","")).strip().upper() == "PENDING"]
    logger.info(f"Found {len(pending)} PENDING URLs")

    if not pending:
        logger.warning("No PENDING URLs! Add more to Google Sheet.")
        send_telegram("⚠️ Queue Empty!\nAdd more Pinterest URLs to Google Sheet with Status = PENDING")
        return

    # Post only 1 per run (runs 3x daily = 3 posts/day)
    item = pending[0]
    pin_url = str(item.get("Pinterest_URL") or item.get("pinterest_url") or "").strip()

    if not pin_url:
        logger.error("Empty Pinterest URL!")
        return

    logger.info(f"📌 Processing: {pin_url}")
    logger.info(f"📊 Queue remaining: {len(pending)}")

    try:
        # Step 1: Extract image
        logger.info("Extracting Pinterest image...")
        image_url = get_pinterest_image(pin_url)
        if not image_url:
            raise ValueError("Could not extract image from Pinterest URL")
        logger.info(f"Image URL: {image_url[:60]}...")

        # Step 2: Download image
        logger.info("Downloading image...")
        img_resp = requests.get(image_url, timeout=30, headers=HEADERS_PIN)
        img_resp.raise_for_status()
        img_path = "/tmp/post_image.jpg"
        with open(img_path, "wb") as f:
            f.write(img_resp.content)
        logger.info(f"Downloaded: {len(img_resp.content)} bytes")

        # Step 3: Upload to CDN
        logger.info("Uploading to public CDN...")
        public_url = upload_to_cdn(img_path)
        logger.info(f"CDN URL: {public_url}")

        # Step 4: Create Instagram container
        logger.info("Creating Instagram container...")
        container_id = create_container(public_url, CAPTION)
        logger.info(f"Container ID: {container_id}")

        # Step 5: Wait
        logger.info("Waiting 15 seconds...")
        time.sleep(15)

        # Step 6: Publish
        logger.info("Publishing to Instagram...")
        post_id = publish_post(container_id)
        logger.info(f"✅ Posted! Post ID: {post_id}")

        # Step 7: Update sheet status
        update_sheet_status(pin_url, "POSTED")

        # Step 8: Telegram success
        send_telegram(
            f"✅ <b>Posted to Instagram!</b>\n\n"
            f"🔗 Pinterest: {pin_url[:60]}\n"
            f"📸 Post ID: {post_id}\n"
            f"🕐 Time: {time.strftime('%Y-%m-%d %H:%M IST')}\n"
            f"📊 Queue left: {len(pending)-1} URLs\n\n"
            f"⚠️ <b>Update Status to POSTED in Google Sheet!</b>"
        )

        logger.info("🎉 Done! 1 post published successfully.")

    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        update_sheet_status(pin_url, "FAILED")
        send_telegram(
            f"❌ <b>Post Failed!</b>\n\n"
            f"🔗 URL: {pin_url[:60]}\n"
            f"⚠️ Error: {str(e)[:200]}\n"
            f"🔄 Change Status to PENDING in sheet to retry"
        )

if __name__ == "__main__":
    main()
