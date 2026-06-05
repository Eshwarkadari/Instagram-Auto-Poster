"""
gsheet_poster.py - Pinterest to Instagram via Google Sheets Queue
FIX v3: Robust Pinterest extraction - handles pin.it shortlinks + all block scenarios
Author: Kadari Eshwar
"""

import os, requests, base64, re, time, logging, csv, io, random, json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ.get("INSTAGRAM_ACCOUNT_ID", "967454269255245")
TELEGRAM_BOT_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID       = os.environ.get("TELEGRAM_CHAT_ID", "7446081188")
GOOGLE_SHEET_ID        = os.environ.get("GOOGLE_SHEET_ID", "15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960")
GH_TOKEN               = os.environ["GH_TOKEN"]
GITHUB_REPO            = os.environ.get("GITHUB_REPO", "Eshwarkadari/Instagram-Auto-Poster")

HEADERS_GH = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}

# Rotate through multiple User-Agents to avoid blocks
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

def get_headers(referer="https://www.google.com/"):
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": referer,
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Cache-Control": "max-age=0",
    }

CAPTION = """🔥 Men's Fashion Inspiration

Upgrade your wardrobe with timeless style and confidence.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #mensstyle #outfitideas #fashion #style #menswear #streetwear #casualstyle #outfitinspiration #styleformen #fashionreels #indianmensfashion #dailyoutfit #styleinspo #fashiontips"""


# ── Google Sheet ──────────────────────────────────────────────────────
def get_sheet_rows():
    for method, url in [
        ("CSV", f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"),
        ("gviz", f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv"),
    ]:
        try:
            r = requests.get(url, timeout=15, allow_redirects=True, headers={"User-Agent": USER_AGENTS[0]})
            if r.status_code == 200 and "," in r.text:
                rows = list(csv.DictReader(io.StringIO(r.text)))
                logger.info(f"✅ Sheet {method}: {len(rows)} rows | Columns: {list(rows[0].keys()) if rows else []}")
                return rows
        except Exception as e:
            logger.warning(f"{method} failed: {e}")

    # Fallback: links.txt
    logger.warning("Sheet not accessible — using links.txt fallback")
    try:
        r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt", headers=HEADERS_GH)
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#") and "pin" in l.lower()]
        logger.info(f"✅ links.txt: {len(lines)} URLs")
        return [{"Pinterest_URL": u, "Status": "PENDING"} for u in lines]
    except Exception as e:
        logger.error(f"links.txt failed: {e}")
        return []


def mark_url_posted(pin_url: str):
    try:
        r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt", headers=HEADERS_GH)
        d = r.json()
        content = base64.b64decode(d["content"]).decode("utf-8")
        new_content = "\n".join([l for l in content.split("\n") if l.strip() != pin_url.strip()])
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH,
            json={"message": "Auto: posted", "content": base64.b64encode(new_content.encode()).decode(), "sha": d["sha"]})

        r2 = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt", headers=HEADERS_GH)
        posted = base64.b64decode(r2.json()["content"]).decode("utf-8") if r2.status_code == 200 else ""
        sha2 = r2.json().get("sha") if r2.status_code == 200 else None
        new_posted = posted.strip() + "\n" + pin_url + "\n"
        p = {"message": "Auto: marked posted", "content": base64.b64encode(new_posted.encode()).decode()}
        if sha2:
            p["sha"] = sha2
        requests.put(f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt", headers=HEADERS_GH, json=p)
        logger.info("✅ Updated links.txt + posted.txt")
    except Exception as e:
        logger.warning(f"File update failed: {e}")


# ── Pinterest: Resolve shortlink ──────────────────────────────────────
def resolve_pin_url(pin_url: str) -> str:
    """
    Resolve pin.it shortlinks and any redirect to the final pinterest.com/pin/ID URL.
    This is CRITICAL — oEmbed and scraping both fail on unresolved shortlinks.
    """
    if "pin.it" not in pin_url and "/pin/" in pin_url:
        return pin_url  # Already a direct URL

    logger.info(f"Resolving shortlink: {pin_url}")
    try:
        # Use HEAD first (faster, no body download)
        r = requests.head(pin_url, timeout=15, headers=get_headers(), allow_redirects=True)
        final = r.url
        if "pinterest" in final and "/pin/" in final:
            logger.info(f"Resolved → {final}")
            return final
    except Exception as e:
        logger.warning(f"HEAD resolve failed: {e}")

    try:
        # GET with allow_redirects
        r = requests.get(pin_url, timeout=15, headers=get_headers(), allow_redirects=True)
        final = r.url
        if "pinterest" in final and "/pin/" in final:
            logger.info(f"Resolved via GET → {final}")
            return final
        # Try to extract from HTML if redirect landed on pinterest page
        m = re.search(r'https://[a-z.]*pinterest\.[a-z.]+/pin/\d+', r.text)
        if m:
            logger.info(f"Extracted from HTML → {m.group(0)}")
            return m.group(0)
    except Exception as e:
        logger.warning(f"GET resolve failed: {e}")

    logger.warning(f"Could not resolve shortlink, using original: {pin_url}")
    return pin_url


# ── Pinterest: Image Extraction (6 methods) ───────────────────────────
def get_pinterest_image(pin_url: str) -> str:
    """
    Extract Pinterest image URL using 6 cascading methods.
    Always resolves shortlinks first.
    """
    # ── STEP 0: Resolve pin.it shortlinks ────────────────────────────
    resolved_url = resolve_pin_url(pin_url)

    # ── Method 1: oEmbed API (fastest, most reliable) ─────────────────
    for url_to_try in [resolved_url, pin_url]:
        try:
            r = requests.get(
                f"https://www.pinterest.com/oembed.json?url={url_to_try}",
                timeout=10, headers=get_headers("https://www.pinterest.com/"))
            if r.status_code == 200:
                data = r.json()
                img = data.get("thumbnail_url", "")
                for low, high in [("236x", "originals"), ("474x", "originals"), ("736x", "originals")]:
                    img = img.replace(low, high)
                if img and "pinimg.com" in img:
                    logger.info(f"✅ Method 1 oEmbed: {img[:80]}")
                    return img
        except Exception as e:
            logger.warning(f"oEmbed ({url_to_try[:40]}): {e}")

    # ── Method 2: og:image meta tag (very reliable) ───────────────────
    for url_to_try in [resolved_url, pin_url]:
        try:
            r = requests.get(url_to_try, timeout=20, headers=get_headers("https://www.google.com/"), allow_redirects=True)
            html = r.text

            # og:image
            m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
            if not m:
                m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
            if m:
                img = m.group(1).replace("&amp;", "&")
                if "pinimg.com" in img:
                    img = re.sub(r'/\d+x\d*/', '/originals/', img)
                    logger.info(f"✅ Method 2 og:image: {img[:80]}")
                    return img

            # ── Method 3: JSON-LD structured data ─────────────────────
            for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', html, re.I):
                try:
                    data = json.loads(block)
                    imgs = data.get("image", [])
                    if isinstance(imgs, str):
                        imgs = [imgs]
                    for img in imgs:
                        if "pinimg.com" in img:
                            img = re.sub(r'/\d+x\d*/', '/originals/', img)
                            logger.info(f"✅ Method 3 JSON-LD: {img[:80]}")
                            return img
                except Exception:
                    pass

            # ── Method 4: pinimg.com CDN regex in HTML ─────────────────
            for pat in [
                r'https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp)',
                r'https://i\.pinimg\.com/736x/[a-f0-9/]+\.(?:jpg|jpeg|png|webp)',
                r'"contentUrl":"(https://i\.pinimg\.com/[^"]+)"',
                r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"',
                r'(https://i\.pinimg\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp))',
            ]:
                m = re.search(pat, html, re.I)
                if m:
                    img = m.group(1) if m.lastindex else m.group(0)
                    img = re.sub(r'/\d+x\d*/', '/originals/', img)
                    logger.info(f"✅ Method 4 regex ({url_to_try[:40]}): {img[:80]}")
                    return img

        except Exception as e:
            logger.warning(f"HTML scrape ({url_to_try[:40]}): {e}")

    # ── Method 5: Pinterest embedded app state __PWS_DATA__ ───────────
    for url_to_try in [resolved_url, pin_url]:
        try:
            r = requests.get(url_to_try, timeout=20, headers=get_headers(), allow_redirects=True)
            for state_pat in [r'P\._(\{[\s\S]+?\});\s*</script', r'__PWS_DATA__\s*=\s*(\{[\s\S]+?\});', r'window\.__INITIAL_STATE__\s*=\s*(\{[\s\S]+?\});']:
                m = re.search(state_pat, r.text)
                if m:
                    try:
                        raw = m.group(1)
                        # Search raw string for pinimg URLs (faster than full JSON parse)
                        imgs = re.findall(r'https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp)', raw)
                        if imgs:
                            logger.info(f"✅ Method 5 app state: {imgs[0][:80]}")
                            return imgs[0]
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"App state ({url_to_try[:40]}): {e}")

    # ── Method 6: Pinterest API v3 (no auth needed for public pins) ────
    try:
        pin_id = re.search(r'/pin/(\d+)', resolved_url)
        if pin_id:
            api_url = f"https://www.pinterest.com/resource/PinResource/get/?source_url=/pin/{pin_id.group(1)}/&data=%7B%22options%22%3A%7B%22id%22%3A%22{pin_id.group(1)}%22%7D%7D"
            r = requests.get(api_url, timeout=10, headers={**get_headers(), "X-Requested-With": "XMLHttpRequest"})
            if r.status_code == 200:
                data = r.json()
                img = (data.get("resource_response", {})
                           .get("data", {})
                           .get("images", {})
                           .get("orig", {})
                           .get("url", ""))
                if img and "pinimg.com" in img:
                    logger.info(f"✅ Method 6 API v3: {img[:80]}")
                    return img
    except Exception as e:
        logger.warning(f"API v3: {e}")

    logger.error(f"❌ All 6 methods failed for: {pin_url}")
    return None


# ── Download image ────────────────────────────────────────────────────
def download_image(image_url: str) -> str:
    img_headers = {
        **get_headers("https://www.pinterest.com/"),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }

    # Try originals, then 736x fallback
    urls_to_try = [image_url]
    if "originals" in image_url:
        urls_to_try.append(image_url.replace("originals", "736x"))
    if "736x" not in image_url:
        urls_to_try.append(re.sub(r'/\d+x\d*/', '/736x/', image_url))

    for url in urls_to_try:
        for attempt in range(2):
            try:
                r = requests.get(url, timeout=30, headers=img_headers, allow_redirects=True, stream=True)
                if r.status_code == 200:
                    path = "/tmp/post.jpg"
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                    size = os.path.getsize(path)
                    if size > 5000:
                        logger.info(f"✅ Downloaded {size} bytes from {url[:60]}")
                        return path
                    logger.warning(f"Too small ({size}b), trying next")
                else:
                    logger.warning(f"HTTP {r.status_code} for {url[:60]}")
            except Exception as e:
                logger.warning(f"Download attempt {attempt+1}: {e}")
            time.sleep(1)

    raise ValueError(f"Could not download image from any URL variant of: {image_url}")


# ── Upload to CDN ─────────────────────────────────────────────────────
def upload_to_cdn(image_path: str) -> str:
    # Option 1: catbox.moe (no account, permanent)
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                files={"fileToUpload": ("img.jpg", f, "image/jpeg")},
                data={"reqtype": "fileupload", "userhash": ""},
                timeout=60)
        if r.status_code == 200 and r.text.strip().startswith("https://"):
            logger.info(f"✅ catbox: {r.text.strip()}")
            return r.text.strip()
    except Exception as e:
        logger.warning(f"catbox: {e}")

    # Option 2: litterbox (72h, but reliable)
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                files={"fileToUpload": ("img.jpg", f, "image/jpeg")},
                data={"reqtype": "fileupload", "time": "72h"},
                timeout=60)
        if r.status_code == 200 and r.text.strip().startswith("https://"):
            logger.info(f"✅ litterbox: {r.text.strip()}")
            return r.text.strip()
    except Exception as e:
        logger.warning(f"litterbox: {e}")

    # Option 3: GitHub raw (always works - uses your own repo)
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        fname = f"storage/img_{int(time.time())}.jpg"
        r = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{fname}",
            headers=HEADERS_GH,
            json={"message": "temp: post image", "content": img_b64})
        if r.status_code in [200, 201]:
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{fname}"
            logger.info(f"✅ GitHub raw: {raw_url}")
            return raw_url
    except Exception as e:
        logger.warning(f"GitHub raw: {e}")

    raise ValueError("All CDN uploads failed!")


# ── Instagram ─────────────────────────────────────────────────────────
def post_to_instagram(image_url: str) -> str:
    logger.info(f"Posting to IG account: {INSTAGRAM_ACCOUNT_ID}")
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={"image_url": image_url, "caption": CAPTION, "access_token": INSTAGRAM_ACCESS_TOKEN})
    logger.info(f"Container: {r.status_code} — {r.text[:300]}")
    if r.status_code != 200:
        raise ValueError(f"Container error: {r.text}")

    container_id = r.json()["id"]
    logger.info(f"Container ID: {container_id} — waiting 15s...")
    time.sleep(15)

    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN})
    logger.info(f"Publish: {r2.status_code} — {r2.text[:300]}")
    if r2.status_code != 200:
        raise ValueError(f"Publish error: {r2.text}")
    return r2.json()["id"]


# ── Telegram ──────────────────────────────────────────────────────────
def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10)
        logger.info("✅ Telegram sent")
    except Exception as e:
        logger.warning(f"Telegram: {e}")


def update_sheet_status(pin_url):
    try:
        WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwkvG2B_ewPkyt2nibNa61i1SOiPno3yj5ikMexuPE6yo3q6xVkuShqbFt9gj5htqgZ/exec"
        r = requests.get(WEBAPP_URL, params={"url": pin_url}, timeout=20)
        logger.info(f"Sheet update: {r.text}")
    except Exception as e:
        logger.warning(f"Sheet update failed: {e}")


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
            "Add Pinterest URLs with Status=PENDING to Google Sheet")
        return

    pin_url = pending[0]
    logger.info(f"📌 Processing: {pin_url}")

    try:
        image_url = get_pinterest_image(pin_url)
        if not image_url:
            raise ValueError(f"Could not extract image URL from Pinterest: {pin_url}")

        img_path = download_image(image_url)
        public_url = upload_to_cdn(img_path)
        post_id = post_to_instagram(public_url)
        logger.info(f"🎉 POSTED! Post ID: {post_id}")

        mark_url_posted(pin_url)
        update_sheet_status(pin_url)

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
            f"⚠️ {str(e)[:300]}\n\n"
            f"Auto-retries next scheduled run.")


if __name__ == "__main__":
    main()
