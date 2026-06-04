"""
gsheet_poster.py - Pinterest to Instagram via Google Sheets Queue
Fixed: Pinterest 403 download issue + correct Instagram ID
"""

import os, requests, base64, re, time, logging, csv, io, random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ.get("INSTAGRAM_ACCOUNT_ID", "17841429486895129")
TELEGRAM_BOT_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID       = os.environ.get("TELEGRAM_CHAT_ID", "7446081188")
GOOGLE_SHEET_ID        = os.environ.get("GOOGLE_SHEET_ID", "15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960")
GH_TOKEN               = os.environ["GH_TOKEN"]
GITHUB_REPO            = os.environ.get("GITHUB_REPO", "Eshwarkadari/Instagram-Auto-Poster")

HEADERS_GH = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}

# Full browser headers to bypass Pinterest 403
HEADERS_PIN = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.pinterest.com/",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Connection": "keep-alive",
}

CAPTION = """🔥 Men's Fashion Inspiration

Upgrade your wardrobe with timeless style and confidence.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #mensstyle #outfitideas #fashion #style #menswear #streetwear #casualstyle #outfitinspiration #styleformen #fashionreels #indianmensfashion #dailyoutfit #styleinspo #fashiontips"""


# ── Google Sheet ──────────────────────────────────────────────────────
def get_sheet_rows():
    # Method 1: CSV export (sheet must be public)
    try:
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"
        r = requests.get(url, timeout=15, allow_redirects=True,
                        headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and "," in r.text:
            rows = list(csv.DictReader(io.StringIO(r.text)))
            logger.info(f"✅ Sheet CSV: {len(rows)} rows | Columns: {list(rows[0].keys()) if rows else []}")
            return rows
    except Exception as e:
        logger.warning(f"CSV failed: {e}")

    # Method 2: gviz
    try:
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            rows = list(csv.DictReader(io.StringIO(r.text)))
            logger.info(f"✅ gviz: {len(rows)} rows")
            return rows
    except Exception as e:
        logger.warning(f"gviz failed: {e}")

    # Method 3: links.txt fallback
    logger.warning("Sheet not accessible - using links.txt")
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH)
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        lines = [l.strip() for l in content.split("\n")
                if l.strip() and not l.strip().startswith("#") and "pin" in l.lower()]
        logger.info(f"✅ links.txt: {len(lines)} URLs")
        return [{"Pinterest_URL": u, "Status": "PENDING"} for u in lines]
    except Exception as e:
        logger.error(f"links.txt failed: {e}")
        return []


def mark_url_posted(pin_url: str):
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH)
        d = r.json()
        content = base64.b64decode(d["content"]).decode("utf-8")
        new_content = "\n".join(
            [l for l in content.split("\n") if l.strip() != pin_url.strip()])
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH,
            json={"message": "Auto: posted", 
                  "content": base64.b64encode(new_content.encode()).decode(),
                  "sha": d["sha"]})

        r2 = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt",
            headers=HEADERS_GH)
        posted = base64.b64decode(r2.json()["content"]).decode("utf-8") if r2.status_code == 200 else ""
        sha2 = r2.json().get("sha") if r2.status_code == 200 else None
        new_posted = posted.strip() + "\n" + pin_url + "\n"
        p = {"message": "Auto: marked posted",
             "content": base64.b64encode(new_posted.encode()).decode()}
        if sha2: p["sha"] = sha2
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt",
            headers=HEADERS_GH, json=p)
        logger.info("✅ Updated links.txt + posted.txt")
    except Exception as e:
        logger.warning(f"File update failed: {e}")


# ── Pinterest Image Extraction ────────────────────────────────────────
def get_pinterest_image(pin_url: str) -> str:
    """Extract Pinterest image - multiple methods"""

    # Method 1: oEmbed
    try:
        r = requests.get(
            f"https://www.pinterest.com/oembed.json?url={pin_url}",
            timeout=10, headers=HEADERS_PIN)
        if r.status_code == 200:
            img = r.json().get("thumbnail_url", "")
            for low, high in [("236x","originals"),("474x","originals"),("736x","originals")]:
                img = img.replace(low, high)
            if img:
                logger.info(f"oEmbed image: {img[:70]}")
                return img
    except Exception as e:
        logger.warning(f"oEmbed: {e}")

    # Method 2: Scrape pin page
    try:
        r = requests.get(pin_url, timeout=15, headers=HEADERS_PIN, allow_redirects=True)
        for pat in [
            r'"contentUrl":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'(https://i\.pinimg\.com/originals/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp))',
            r'(https://i\.pinimg\.com/736x/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp))',
            r'(https://i\.pinimg\.com/474x/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp))',
        ]:
            m = re.search(pat, r.text)
            if m:
                logger.info(f"Scraped: {m.group(1)[:70]}")
                return m.group(1)
    except Exception as e:
        logger.warning(f"Scrape: {e}")
    return None


def download_image(image_url: str) -> str:
    """Download image with full browser headers to bypass 403"""
    img_headers = {
        **HEADERS_PIN,
        "Referer": "https://www.pinterest.com/",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }

    # Try direct download
    for attempt in range(3):
        try:
            r = requests.get(image_url, timeout=30, headers=img_headers,
                           allow_redirects=True, stream=True)
            if r.status_code == 200:
                path = "/tmp/post.jpg"
                with open(path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                size = os.path.getsize(path)
                logger.info(f"✅ Downloaded: {size} bytes")
                if size > 10000:  # Must be > 10KB
                    return path
                logger.warning(f"Image too small: {size} bytes")
            else:
                logger.warning(f"Download attempt {attempt+1}: {r.status_code}")
        except Exception as e:
            logger.warning(f"Download attempt {attempt+1} failed: {e}")
        time.sleep(2)

    # Try 736x version if originals failed
    if "originals" in image_url:
        alt_url = image_url.replace("originals", "736x")
        logger.info(f"Trying 736x: {alt_url[:70]}")
        try:
            r = requests.get(alt_url, timeout=30, headers=img_headers)
            if r.status_code == 200 and len(r.content) > 10000:
                with open("/tmp/post.jpg", "wb") as f:
                    f.write(r.content)
                logger.info(f"✅ 736x downloaded: {len(r.content)} bytes")
                return "/tmp/post.jpg"
        except Exception as e:
            logger.warning(f"736x failed: {e}")

    raise ValueError(f"Could not download image from: {image_url}")


def upload_to_cdn(image_path: str) -> str:
    """Upload to catbox.moe for public URL"""
    with open(image_path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            files={"fileToUpload": ("img.jpg", f, "image/jpeg")},
            data={"reqtype": "fileupload", "userhash": ""},
            timeout=60)
    if r.status_code == 200 and r.text.startswith("https://"):
        logger.info(f"✅ CDN: {r.text.strip()}")
        return r.text.strip()
    raise ValueError(f"CDN failed: {r.text[:100]}")


# ── Instagram ─────────────────────────────────────────────────────────
def post_to_instagram(image_url: str) -> str:
    logger.info(f"Posting to Instagram ID: {INSTAGRAM_ACCOUNT_ID}")

    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={"image_url": image_url, "caption": CAPTION,
              "access_token": INSTAGRAM_ACCESS_TOKEN})
    logger.info(f"Container: {r.status_code} - {r.text[:200]}")
    if r.status_code != 200:
        raise ValueError(f"Container error: {r.text}")

    container_id = r.json()["id"]
    logger.info(f"Container ID: {container_id} — waiting 15s...")
    time.sleep(15)

    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": container_id,
              "access_token": INSTAGRAM_ACCESS_TOKEN})
    logger.info(f"Publish: {r2.status_code} - {r2.text[:200]}")
    if r2.status_code != 200:
        raise ValueError(f"Publish error: {r2.text}")
    return r2.json()["id"]


# ── Telegram ──────────────────────────────────────────────────────────
def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN: return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10)
        logger.info("✅ Telegram sent")
    except Exception as e:
        logger.warning(f"Telegram: {e}")


# ── Main ──────────────────────────────────────────────────────────────
def main():
    logger.info("🚀 Starting Pinterest → Instagram Auto Poster")
    logger.info(f"Instagram Account ID: {INSTAGRAM_ACCOUNT_ID}")

    rows = get_sheet_rows()
    pending = []
    for row in rows:
        status = (row.get("Status") or row.get("status") or "").strip().upper()
        url = (row.get("Pinterest_URL") or row.get("pinterest_url") or
               row.get("Pinterest URL") or "").strip()
        if status == "PENDING" and url:
            pending.append(url)

    logger.info(f"📊 {len(pending)} PENDING URLs found")

    if not pending:
        logger.warning("No PENDING URLs!")
        send_telegram(
            "⚠️ <b>Queue Empty!</b>\n\n"
            "Add Pinterest URLs with Status=PENDING to Google Sheet\n"
            "Make sure sheet is: Share → Anyone with link → Viewer")
        return

    pin_url = pending[0]
    logger.info(f"📌 Processing: {pin_url}")

    try:
        # Step 1: Get image URL
        image_url = get_pinterest_image(pin_url)
        if not image_url:
            raise ValueError("Could not extract image URL from Pinterest")

        # Step 2: Download image
        img_path = download_image(image_url)

        # Step 3: Upload to CDN
        public_url = upload_to_cdn(img_path)

        # Step 4: Post to Instagram
        post_id = post_to_instagram(public_url)
        logger.info(f"🎉 POSTED! Post ID: {post_id}")

        # Step 5: Mark as done
        mark_url_posted(pin_url)

        send_telegram(
            f"✅ <b>Posted to Instagram!</b>\n\n"
            f"🔗 {pin_url[:60]}\n"
            f"📸 Post ID: {post_id}\n"
            f"🕐 {time.strftime('%Y-%m-%d %H:%M')} IST\n"
            f"📊 {len(pending)-1} URLs remaining\n\n"
            f"⚠️ Update Status to POSTED in Google Sheet!")

    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        send_telegram(
            f"❌ <b>Post Failed!</b>\n\n"
            f"🔗 {pin_url[:60]}\n"
            f"⚠️ {str(e)[:300]}")

if __name__ == "__main__":
    main()
