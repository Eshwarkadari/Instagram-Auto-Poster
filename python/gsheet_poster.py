"""
gsheet_poster.py - Pinterest to Instagram via Google Sheets Queue
Reads PENDING URLs, posts to Instagram, sends Telegram notification
"""

import os, requests, base64, re, time, logging, csv, io

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ["INSTAGRAM_ACCOUNT_ID"]
TELEGRAM_BOT_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID       = os.environ.get("TELEGRAM_CHAT_ID", "")
GOOGLE_SHEET_ID        = os.environ["GOOGLE_SHEET_ID"]
GH_TOKEN               = os.environ["GH_TOKEN"]
GITHUB_REPO            = os.environ.get("GITHUB_REPO", "Eshwarkadari/Instagram-Auto-Poster")

HEADERS_GH  = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}
HEADERS_PIN = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

CAPTION = """🔥 Men's Fashion Inspiration

Upgrade your wardrobe with timeless style and confidence.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #mensstyle #outfitideas #fashion #style #menswear #streetwear #casualstyle #outfitinspiration #styleformen #fashionreels #indianmensfashion #dailyoutfit #styleinspo #fashiontips"""


# ── Google Sheet Reader ───────────────────────────────────────────────
def get_sheet_rows():
    """Read Google Sheet - tries multiple methods"""
    
    # Method 1: Public CSV export
    try:
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"
        r = requests.get(url, timeout=15, allow_redirects=True,
                        headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and "," in r.text:
            reader = csv.DictReader(io.StringIO(r.text))
            rows = list(reader)
            logger.info(f"✅ Read sheet via CSV: {len(rows)} rows")
            logger.info(f"Columns: {list(rows[0].keys()) if rows else 'empty'}")
            return rows
    except Exception as e:
        logger.warning(f"CSV export failed: {e}")

    # Method 2: gviz JSON (public sheets)
    try:
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            reader = csv.DictReader(io.StringIO(r.text))
            rows = list(reader)
            logger.info(f"✅ Read sheet via gviz: {len(rows)} rows")
            return rows
    except Exception as e:
        logger.warning(f"gviz failed: {e}")

    # Method 3: Read from links.txt in GitHub as fallback
    logger.warning("Google Sheet not accessible - using links.txt fallback")
    return read_from_github_links()


def read_from_github_links():
    """Fallback: read from links.txt in GitHub repo"""
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH
        )
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        sha = r.json()["sha"]
        lines = [l.strip() for l in content.split("\n") 
                if l.strip() and not l.strip().startswith("#") and "pin" in l.lower()]
        rows = [{"Pinterest_URL": url, "Status": "PENDING", "_sha": sha, "_source": "github"} 
                for url in lines]
        logger.info(f"✅ Read {len(rows)} URLs from links.txt")
        return rows
    except Exception as e:
        logger.error(f"GitHub fallback failed: {e}")
        return []


def mark_posted_in_github(url: str, all_rows: list):
    """Mark URL as posted in links.txt → move to posted.txt"""
    try:
        # Remove from links.txt
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH
        )
        data = r.json()
        sha = data["sha"]
        content = base64.b64decode(data["content"]).decode("utf-8")
        lines = content.split("\n")
        new_lines = [l for l in lines if l.strip() != url.strip()]
        new_content = "\n".join(new_lines)
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH,
            json={"message": f"Auto: posted {url[:40]}", 
                  "content": base64.b64encode(new_content.encode()).decode(),
                  "sha": sha}
        )

        # Add to posted.txt
        r2 = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt",
            headers=HEADERS_GH
        )
        if r2.status_code == 200:
            d2 = r2.json()
            posted = base64.b64decode(d2["content"]).decode("utf-8")
            sha2 = d2["sha"]
        else:
            posted, sha2 = "", None

        new_posted = posted.strip() + "\n" + url + "\n"
        payload = {"message": f"Auto: marked posted", 
                   "content": base64.b64encode(new_posted.encode()).decode()}
        if sha2:
            payload["sha"] = sha2
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt",
            headers=HEADERS_GH, json=payload
        )
        logger.info("✅ Updated links.txt and posted.txt")
    except Exception as e:
        logger.warning(f"Could not update GitHub files: {e}")


# ── Pinterest ─────────────────────────────────────────────────────────
def get_pinterest_image(pin_url: str) -> str:
    try:
        r = requests.get(
            f"https://www.pinterest.com/oembed.json?url={pin_url}",
            timeout=10, headers=HEADERS_PIN
        )
        if r.status_code == 200:
            img = r.json().get("thumbnail_url", "")
            for low, high in [("236x","originals"),("474x","originals"),("736x","originals")]:
                img = img.replace(low, high)
            if img:
                logger.info(f"oEmbed image: {img[:60]}")
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
                logger.info(f"Scraped image: {m.group(1)[:60]}")
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
    raise ValueError(f"CDN failed: {r.text[:100]}")


# ── Instagram ─────────────────────────────────────────────────────────
def post_to_instagram(image_url: str) -> str:
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={"image_url": image_url, "caption": CAPTION,
              "access_token": INSTAGRAM_ACCESS_TOKEN}
    )
    if r.status_code != 200:
        raise ValueError(f"Container error: {r.text}")
    container_id = r.json()["id"]
    logger.info(f"Container: {container_id}")

    time.sleep(15)

    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN}
    )
    if r2.status_code != 200:
        raise ValueError(f"Publish error: {r2.text}")
    return r2.json()["id"]


# ── Telegram ──────────────────────────────────────────────────────────
def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
        logger.info("✅ Telegram sent")
    except Exception as e:
        logger.warning(f"Telegram failed: {e}")


# ── Main ──────────────────────────────────────────────────────────────
def main():
    logger.info("🚀 Starting Pinterest → Instagram Auto Poster")

    rows = get_sheet_rows()

    # Find PENDING
    pending = []
    for r in rows:
        # Check all possible column name formats
        status = (r.get("Status") or r.get("status") or r.get("STATUS") or "").strip().upper()
        url = (r.get("Pinterest_URL") or r.get("pinterest_url") or 
               r.get("Pinterest URL") or r.get("PINTEREST_URL") or "").strip()
        if status == "PENDING" and url:
            pending.append({"url": url, "row": r})

    logger.info(f"📊 Found {len(pending)} PENDING URLs")

    if not pending:
        logger.warning("❌ No PENDING URLs found!")
        logger.info("Please make sure your Google Sheet:")
        logger.info("1. Is shared as 'Anyone with link can view'")
        logger.info("2. Has columns: Pinterest_URL | Status")
        logger.info("3. Status column has value: PENDING (uppercase)")
        send_telegram(
            "⚠️ <b>Queue Empty!</b>\n\n"
            "No PENDING URLs found in Google Sheet.\n"
            "Please add Pinterest URLs with Status = PENDING\n\n"
            "Make sure sheet is shared publicly!"
        )
        return

    # Process first PENDING URL
    item = pending[0]
    pin_url = item["url"]
    logger.info(f"📌 Processing: {pin_url}")
    logger.info(f"📊 Queue: {len(pending)} remaining")

    try:
        # Get Pinterest image
        image_url = get_pinterest_image(pin_url)
        if not image_url:
            raise ValueError("Could not extract image from Pinterest")

        # Download
        img_resp = requests.get(image_url, timeout=30, headers=HEADERS_PIN)
        img_resp.raise_for_status()
        with open("/tmp/post.jpg", "wb") as f:
            f.write(img_resp.content)
        logger.info(f"Downloaded: {len(img_resp.content)} bytes")

        # Upload to CDN
        public_url = upload_to_cdn("/tmp/post.jpg")
        logger.info(f"CDN: {public_url}")

        # Post to Instagram
        post_id = post_to_instagram(public_url)
        logger.info(f"✅ Posted! ID: {post_id}")

        # Mark as posted
        mark_posted_in_github(pin_url, rows)

        # Success notification
        send_telegram(
            f"✅ <b>Posted to Instagram!</b>\n\n"
            f"🔗 {pin_url[:60]}\n"
            f"📸 Post ID: {post_id}\n"
            f"🕐 {time.strftime('%Y-%m-%d %H:%M')} IST\n"
            f"📊 {len(pending)-1} URLs remaining in queue\n\n"
            f"⚠️ <b>Update Status to POSTED in your Google Sheet!</b>"
        )

    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        send_telegram(
            f"❌ <b>Post Failed!</b>\n\n"
            f"🔗 {pin_url[:60]}\n"
            f"⚠️ {str(e)[:200]}\n"
            f"🔄 Fix and retry"
        )

if __name__ == "__main__":
    main()
