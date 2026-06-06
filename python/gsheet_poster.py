"""
gsheet_poster.py - Pinterest to Instagram via Google Sheets Queue
v5: COMPLETE FIX
  - Clean pin ID from ANY URL (including /sent/?invite_code=)
  - Skip bad URLs and auto-try next PENDING
  - Robust HTML fetch via 4 proxies
  - 6 image extraction methods
Author: Kadari Eshwar
"""

import os, requests, base64, re, time, logging, csv, io, random, json, urllib.parse

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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

CAPTION = """🔥 Men's Fashion Inspiration

Upgrade your wardrobe with timeless style and confidence.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #mensstyle #outfitideas #fashion #style #menswear #streetwear #casualstyle #outfitinspiration #styleformen #fashionreels #indianmensfashion #dailyoutfit #styleinspo #fashiontips"""


def get_headers(referer="https://www.google.com/"):
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": referer,
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ─────────────────────────────────────────────────────────────────────
# GOOGLE SHEET
# ─────────────────────────────────────────────────────────────────────

def get_sheet_rows():
    for method, url in [
        ("CSV",  f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"),
        ("gviz", f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv"),
    ]:
        try:
            r = requests.get(url, timeout=15, allow_redirects=True,
                             headers={"User-Agent": USER_AGENTS[0]})
            if r.status_code == 200 and "," in r.text:
                rows = list(csv.DictReader(io.StringIO(r.text)))
                logger.info(f"✅ Sheet {method}: {len(rows)} rows | Columns: {list(rows[0].keys()) if rows else []}")
                return rows
        except Exception as e:
            logger.warning(f"Sheet {method}: {e}")

    # Fallback: links.txt in repo
    logger.warning("Sheet unavailable — using links.txt")
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH)
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        lines = [l.strip() for l in content.split("\n")
                 if l.strip() and not l.startswith("#") and "pin" in l.lower()]
        logger.info(f"✅ links.txt: {len(lines)} URLs")
        return [{"Pinterest_URL": u, "Status": "PENDING"} for u in lines]
    except Exception as e:
        logger.error(f"links.txt: {e}")
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
            json={"message": "Auto: posted", "sha": d["sha"],
                  "content": base64.b64encode(new_content.encode()).decode()})

        r2 = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt",
            headers=HEADERS_GH)
        posted = base64.b64decode(r2.json()["content"]).decode("utf-8") if r2.status_code == 200 else ""
        sha2 = r2.json().get("sha") if r2.status_code == 200 else None
        new_posted = posted.strip() + "\n" + pin_url + "\n"
        p = {"message": "Auto: marked posted",
             "content": base64.b64encode(new_posted.encode()).decode()}
        if sha2:
            p["sha"] = sha2
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt",
            headers=HEADERS_GH, json=p)
        logger.info("✅ links.txt + posted.txt updated")
    except Exception as e:
        logger.warning(f"mark_posted: {e}")


def update_sheet_status(pin_url):
    try:
        WEBAPP_URL = ("https://script.google.com/macros/s/"
                      "AKfycbwkvG2B_ewPkyt2nibNa61i1SOiPno3yj5ikMexuPE6yo3q6xVkuShqbFt9gj5htqgZ/exec")
        r = requests.get(WEBAPP_URL, params={"url": pin_url}, timeout=20)
        logger.info(f"Sheet update: {r.text}")
    except Exception as e:
        logger.warning(f"Sheet update: {e}")


# ─────────────────────────────────────────────────────────────────────
# PINTEREST URL CLEANING
# The CORE fix: extract pin ID from ANY URL variant including:
#   pin.it/xxxx  →  resolve redirect  →  pinterest.com/pin/ID/sent/?invite_code=...
#   Then strip everything after /pin/ID/ to get clean URL
# ─────────────────────────────────────────────────────────────────────

def get_clean_pin_url(original_url: str) -> tuple:
    """
    Returns (clean_url, pin_id) where clean_url is always:
      https://www.pinterest.com/pin/{pin_id}/
    Works for pin.it shortlinks, /sent/ invite URLs, /repin/, etc.
    Returns (None, None) if no pin ID can be found.
    """
    url = original_url.strip()

    # Step 1: Resolve pin.it shortlinks via redirect
    if "pin.it" in url:
        logger.info(f"Resolving shortlink: {url}")
        for method in ("HEAD", "GET"):
            try:
                fn = requests.head if method == "HEAD" else requests.get
                r = fn(url, timeout=15, headers=get_headers(), allow_redirects=True)
                url = r.url
                logger.info(f"  {method} → {url}")
                if "pinterest" in url:
                    break
            except Exception as e:
                logger.warning(f"  {method} resolve failed: {e}")

    # Step 2: Extract numeric pin ID from whatever URL we have
    # Matches /pin/123456789/ in any position, ignoring everything after
    m = re.search(r'/pin/(\d+)', url)
    if not m:
        logger.error(f"No pin ID found in: {url}")
        return None, None

    pin_id = m.group(1)
    clean_url = f"https://www.pinterest.com/pin/{pin_id}/"
    logger.info(f"✅ Clean URL: {clean_url}  (pin_id={pin_id})")
    return clean_url, pin_id


# ─────────────────────────────────────────────────────────────────────
# HTML FETCH — Direct + 4 Proxy fallbacks
# GitHub Actions IPs are often blocked by Pinterest.
# ─────────────────────────────────────────────────────────────────────

def fetch_html(url: str) -> str:
    """Fetch page HTML. Try direct first, then proxies."""

    # Direct
    try:
        r = requests.get(url, timeout=20,
                         headers=get_headers("https://www.google.com/"),
                         allow_redirects=True)
        if r.status_code == 200 and len(r.text) > 1000:
            logger.info(f"✅ Direct fetch ({len(r.text)} chars)")
            return r.text
        logger.warning(f"Direct: HTTP {r.status_code}, {len(r.text)} chars")
    except Exception as e:
        logger.warning(f"Direct: {e}")

    # Proxy 1: allorigins.win
    try:
        r = requests.get(
            f"https://api.allorigins.win/get?url={urllib.parse.quote(url)}",
            timeout=25, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200:
            html = r.json().get("contents", "")
            if html and len(html) > 1000:
                logger.info(f"✅ allorigins ({len(html)} chars)")
                return html
    except Exception as e:
        logger.warning(f"allorigins: {e}")

    # Proxy 2: corsproxy.io
    try:
        r = requests.get(
            f"https://corsproxy.io/?{urllib.parse.quote(url)}",
            timeout=25, headers=get_headers())
        if r.status_code == 200 and len(r.text) > 1000:
            logger.info(f"✅ corsproxy ({len(r.text)} chars)")
            return r.text
    except Exception as e:
        logger.warning(f"corsproxy: {e}")

    # Proxy 3: thingproxy
    try:
        r = requests.get(
            f"https://thingproxy.freeboard.io/fetch/{url}",
            timeout=25, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200 and len(r.text) > 1000:
            logger.info(f"✅ thingproxy ({len(r.text)} chars)")
            return r.text
    except Exception as e:
        logger.warning(f"thingproxy: {e}")

    # Proxy 4: htmlpreview (last resort)
    try:
        r = requests.get(
            f"https://api.codetabs.com/v1/proxy?quest={urllib.parse.quote(url)}",
            timeout=25, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200 and len(r.text) > 1000:
            logger.info(f"✅ codetabs ({len(r.text)} chars)")
            return r.text
    except Exception as e:
        logger.warning(f"codetabs: {e}")

    logger.warning("All HTML fetch methods failed")
    return ""


# ─────────────────────────────────────────────────────────────────────
# IMAGE EXTRACTION FROM HTML
# ─────────────────────────────────────────────────────────────────────

def extract_image_from_html(html: str) -> str:
    if not html:
        return None

    # Pattern priority: highest resolution first
    patterns = [
        # og:image (most reliable)
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        # Pinterest CDN originals
        r'"contentUrl"\s*:\s*"(https://i\.pinimg\.com/originals/[^"]+)"',
        r'"url"\s*:\s*"(https://i\.pinimg\.com/originals/[^"]+)"',
        r'(https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp))',
        # 736x fallback
        r'(https://i\.pinimg\.com/736x/[a-f0-9/]+\.(?:jpg|jpeg|png|webp))',
        # Any pinimg
        r'(https://i\.pinimg\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp))',
    ]

    for pat in patterns:
        m = re.search(pat, html, re.I)
        if m:
            img = m.group(1).replace("&amp;", "&")
            if "pinimg.com" in img:
                # Upgrade to originals resolution
                img = re.sub(r'/\d+x\d*/', '/originals/', img)
                logger.info(f"✅ HTML regex extracted: {img[:80]}")
                return img

    # JSON-LD structured data
    for block in re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
            html, re.I):
        try:
            data = json.loads(block)
            imgs = data.get("image", [])
            if isinstance(imgs, str):
                imgs = [imgs]
            for img in (imgs if isinstance(imgs, list) else []):
                if "pinimg.com" in str(img):
                    img = re.sub(r'/\d+x\d*/', '/originals/', str(img))
                    logger.info(f"✅ JSON-LD: {img[:80]}")
                    return img
        except Exception:
            pass

    return None


# ─────────────────────────────────────────────────────────────────────
# MAIN IMAGE EXTRACTION — 6 methods in order
# ─────────────────────────────────────────────────────────────────────

def get_pinterest_image(original_url: str) -> str:
    # ── STEP 0: Get clean pin URL with extracted pin ID ───────────────
    clean_url, pin_id = get_clean_pin_url(original_url)
    if not clean_url or not pin_id:
        raise ValueError(f"Cannot extract pin ID from URL: {original_url}")

    logger.info(f"Extracting image | pin_id={pin_id} | url={clean_url}")

    # ── Method 1: oEmbed API ──────────────────────────────────────────
    for try_url in [clean_url, original_url]:
        try:
            r = requests.get(
                f"https://www.pinterest.com/oembed.json?url={urllib.parse.quote(try_url)}",
                timeout=12, headers=get_headers("https://www.pinterest.com/"))
            if r.status_code == 200:
                data = r.json()
                img = data.get("thumbnail_url", "")
                for res in ["236x", "474x", "736x"]:
                    img = img.replace(res, "originals")
                if img and "pinimg.com" in img:
                    logger.info(f"✅ Method 1 oEmbed: {img[:80]}")
                    return img
                logger.warning(f"oEmbed OK but no image in response")
            else:
                logger.warning(f"oEmbed HTTP {r.status_code}")
        except Exception as e:
            logger.warning(f"oEmbed: {e}")

    # ── Method 2: Pinterest internal API v3 ──────────────────────────
    try:
        api_url = (
            f"https://www.pinterest.com/resource/PinResource/get/"
            f"?source_url=/pin/{pin_id}/"
            f"&data=%7B%22options%22%3A%7B%22id%22%3A%22{pin_id}%22%7D%7D"
        )
        r = requests.get(api_url, timeout=12, headers={
            **get_headers("https://www.pinterest.com/"),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        })
        if r.status_code == 200:
            raw = r.text
            # Search raw JSON string for any pinimg URL
            m = re.search(
                r'https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp)',
                raw, re.I)
            if not m:
                m = re.search(
                    r'https://i\.pinimg\.com/[^\s"\'\\]+\.(?:jpg|jpeg|png|webp)',
                    raw, re.I)
            if m:
                img = re.sub(r'/\d+x\d*/', '/originals/', m.group(0))
                logger.info(f"✅ Method 2 API v3: {img[:80]}")
                return img
        logger.warning(f"API v3: HTTP {r.status_code}")
    except Exception as e:
        logger.warning(f"API v3: {e}")

    # ── Method 3: Scrape clean pin page (direct + proxies) ───────────
    html = fetch_html(clean_url)
    img = extract_image_from_html(html)
    if img:
        logger.info(f"✅ Method 3 HTML scrape: {img[:80]}")
        return img

    # ── Method 4: Wayback Machine cached version ──────────────────────
    try:
        logger.info("Trying Wayback Machine...")
        avail_url = f"https://archive.org/wayback/available?url=pinterest.com/pin/{pin_id}/"
        r = requests.get(avail_url, timeout=15, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200:
            snap = r.json().get("archived_snapshots", {}).get("closest", {})
            if snap.get("available") and snap.get("url"):
                snap_url = snap["url"]
                logger.info(f"Wayback snapshot: {snap_url}")
                html2 = fetch_html(snap_url)
                img = extract_image_from_html(html2)
                if img:
                    logger.info(f"✅ Method 4 Wayback: {img[:80]}")
                    return img
    except Exception as e:
        logger.warning(f"Wayback: {e}")

    # ── Method 5: Pinterest mobile API ───────────────────────────────
    try:
        r = requests.get(
            f"https://api.pinterest.com/v3/pidgets/pins/info/?pin_ids={pin_id}",
            timeout=12, headers={
                "User-Agent": "Pinterest/10.0 (iPhone; iOS 16.0)",
                "Accept": "application/json",
            })
        if r.status_code == 200:
            raw = r.text
            m = re.search(
                r'https://i\.pinimg\.com/[^\s"\'\\]+\.(?:jpg|jpeg|png|webp)',
                raw, re.I)
            if m:
                img = re.sub(r'/\d+x\d*/', '/originals/', m.group(0))
                logger.info(f"✅ Method 5 Mobile API: {img[:80]}")
                return img
    except Exception as e:
        logger.warning(f"Mobile API: {e}")

    # ── Method 6: Pinterest search image endpoint ─────────────────────
    try:
        r = requests.get(
            f"https://i.pinimg.com/736x/{pin_id[:2]}/{pin_id[2:4]}/{pin_id[4:6]}/{pin_id}.jpg",
            timeout=10, headers=get_headers())
        # This URL pattern doesn't always work but try it
        if r.status_code == 200 and len(r.content) > 5000:
            # Upload this directly
            path = "/tmp/direct.jpg"
            with open(path, "wb") as f:
                f.write(r.content)
            logger.info(f"✅ Method 6 direct CDN guess: {len(r.content)} bytes")
            return f"ALREADY_DOWNLOADED:{path}"
    except Exception as e:
        logger.warning(f"Direct CDN: {e}")

    raise ValueError(f"All 6 methods failed for pin_id={pin_id} | original={original_url}")


# ─────────────────────────────────────────────────────────────────────
# IMAGE DOWNLOAD
# ─────────────────────────────────────────────────────────────────────

def download_image(image_url: str) -> str:
    # Special case: already downloaded by method 6
    if image_url.startswith("ALREADY_DOWNLOADED:"):
        path = image_url.split(":", 1)[1]
        if os.path.exists(path) and os.path.getsize(path) > 5000:
            return path

    img_headers = {
        **get_headers("https://www.pinterest.com/"),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }

    # Try originals, 736x, 474x variants
    urls_to_try = [image_url]
    if "originals" in image_url:
        urls_to_try.append(image_url.replace("originals", "736x"))
        urls_to_try.append(image_url.replace("originals", "474x"))
    elif "736x" in image_url:
        urls_to_try.append(image_url.replace("736x", "originals"))

    for url in urls_to_try:
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=30, headers=img_headers,
                                 allow_redirects=True, stream=True)
                if r.status_code == 200:
                    path = "/tmp/post.jpg"
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                    size = os.path.getsize(path)
                    if size > 5000:
                        logger.info(f"✅ Downloaded {size:,} bytes from {url[:60]}")
                        return path
                    logger.warning(f"Too small: {size} bytes")
                else:
                    logger.warning(f"HTTP {r.status_code}: {url[:60]}")
            except Exception as e:
                logger.warning(f"Download attempt {attempt+1}: {e}")
            time.sleep(1)

    raise ValueError(f"Cannot download image: {image_url}")


# ─────────────────────────────────────────────────────────────────────
# CDN UPLOAD
# ─────────────────────────────────────────────────────────────────────

def upload_to_cdn(image_path: str) -> str:
    # 1. catbox.moe (permanent, no account needed)
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

    # 2. litterbox (72h)
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

    # 3. GitHub raw (always works — uses your own repo)
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        fname = f"storage/img_{int(time.time())}.jpg"

        # Create storage dir entry if needed
        r = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{fname}",
            headers=HEADERS_GH,
            json={"message": "temp: post image", "content": img_b64})

        if r.status_code in [200, 201]:
            # Use raw URL — must wait for GitHub CDN propagation
            time.sleep(3)
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{fname}"
            logger.info(f"✅ GitHub raw: {raw_url}")
            return raw_url
    except Exception as e:
        logger.warning(f"GitHub raw: {e}")

    raise ValueError("All CDN uploads failed!")


# ─────────────────────────────────────────────────────────────────────
# INSTAGRAM
# ─────────────────────────────────────────────────────────────────────

def post_to_instagram(image_url: str) -> str:
    logger.info(f"Creating IG container | account={INSTAGRAM_ACCOUNT_ID}")
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={
            "image_url": image_url,
            "caption": CAPTION,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        })
    logger.info(f"Container: HTTP {r.status_code} | {r.text[:300]}")
    if r.status_code != 200:
        raise ValueError(f"Container failed: {r.text}")

    container_id = r.json()["id"]
    logger.info(f"Container ID: {container_id} — waiting 15s for processing...")
    time.sleep(15)

    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN})
    logger.info(f"Publish: HTTP {r2.status_code} | {r2.text[:300]}")
    if r2.status_code != 200:
        raise ValueError(f"Publish failed: {r2.text}")

    return r2.json()["id"]


# ─────────────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

def main():
    logger.info("🚀 Starting Pinterest → Instagram Auto Poster")
    logger.info(f"Account: {INSTAGRAM_ACCOUNT_ID}")

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
        send_telegram("⚠️ <b>Queue Empty!</b>\n\nAdd Pinterest URLs with Status=PENDING to Google Sheet")
        return

    posted = False
    attempted = 0
    MAX_ATTEMPTS = min(5, len(pending))  # Try up to 5 URLs per run

    for pin_url in pending[:MAX_ATTEMPTS]:
        attempted += 1
        logger.info(f"\n📌 Attempt {attempted}/{MAX_ATTEMPTS}: {pin_url}")

        try:
            image_url = get_pinterest_image(pin_url)
            img_path  = download_image(image_url)
            public_url = upload_to_cdn(img_path)
            post_id   = post_to_instagram(public_url)

            logger.info(f"🎉 SUCCESS! Post ID: {post_id}")
            mark_url_posted(pin_url)
            update_sheet_status(pin_url)

            send_telegram(
                f"✅ <b>Posted to Instagram!</b>\n\n"
                f"🔗 {pin_url[:60]}\n"
                f"📸 Post ID: <code>{post_id}</code>\n"
                f"🕐 {time.strftime('%Y-%m-%d %H:%M')} IST\n"
                f"📊 {len(pending) - attempted} URLs remaining in queue")
            posted = True
            break

        except Exception as e:
            err = str(e)
            logger.error(f"❌ Failed: {err}")

            # If it's a pin ID extraction failure — bad URL, skip to next silently
            if "Cannot extract pin ID" in err or "All 6 methods failed" in err:
                logger.warning(f"Skipping bad URL, trying next...")
                continue

            # Other errors (IG, CDN, download) — alert and stop
            send_telegram(
                f"❌ <b>Post Failed!</b>\n\n"
                f"🔗 {pin_url[:60]}\n"
                f"⚠️ {err[:300]}\n\n"
                f"Will retry next scheduled run.")
            break

    if not posted:
        bad_urls = pending[:attempted]
        logger.error(f"Could not post after {attempted} attempts")
        send_telegram(
            f"⚠️ <b>Could not post!</b>\n\n"
            f"Tried {attempted} URL(s), all failed.\n\n"
            f"Bad URLs detected:\n" +
            "\n".join(f"• {u[:60]}" for u in bad_urls[:3]) +
            "\n\n<b>Please add valid Pinterest pin URLs to the queue.\n"
            f"Format: https://pinterest.com/pin/123456789/</b>")


if __name__ == "__main__":
    main()
