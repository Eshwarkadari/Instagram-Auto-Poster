"""
gsheet_poster.py - Pinterest → Instagram Auto Poster
v6 FINAL - Production ready
  ✅ Resolves pin.it shortlinks (GitHub Actions IPs can do this)
  ✅ Extracts pin ID from ANY URL variant (/sent/, /repin/, /invite/)
  ✅ 6 image extraction methods with proper fallbacks
  ✅ 4 HTML proxy fallbacks for Pinterest blocking
  ✅ Skips bad URLs and tries next PENDING automatically
  ✅ CDN upload with 3 fallbacks
  ✅ Full Telegram notifications
Author: Kadari Eshwar (@styleformenindia)
"""

import os, requests, base64, re, time, logging, csv, io, random, json, urllib.parse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Environment Variables ──────────────────────────────────────────────────────
INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ.get("INSTAGRAM_ACCOUNT_ID", "967454269255245")
TELEGRAM_BOT_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID       = os.environ.get("TELEGRAM_CHAT_ID", "7446081188")
GOOGLE_SHEET_ID        = os.environ.get("GOOGLE_SHEET_ID", "15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960")
GH_TOKEN               = os.environ["GH_TOKEN"]
GITHUB_REPO            = os.environ.get("GITHUB_REPO", "Eshwarkadari/Instagram-Auto-Poster")

HEADERS_GH = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json"
}

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


def browser_headers(referer="https://www.google.com/"):
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


# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE SHEET — read PENDING URLs
# ─────────────────────────────────────────────────────────────────────────────

def get_sheet_rows():
    """Read queue from Google Sheet. Falls back to links.txt in repo."""
    for method, url in [
        ("CSV",  f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"),
        ("gviz", f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv"),
    ]:
        try:
            r = requests.get(url, timeout=15, allow_redirects=True,
                             headers={"User-Agent": USER_AGENTS[0]})
            if r.status_code == 200 and "," in r.text:
                rows = list(csv.DictReader(io.StringIO(r.text)))
                logger.info(f"✅ Sheet ({method}): {len(rows)} rows | cols={list(rows[0].keys()) if rows else []}")
                return rows
        except Exception as e:
            logger.warning(f"Sheet {method}: {e}")

    # Fallback: links.txt
    logger.warning("Sheet unavailable — falling back to links.txt")
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH, timeout=10)
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        lines = [l.strip() for l in content.split("\n")
                 if l.strip() and not l.startswith("#") and "pin" in l.lower()]
        logger.info(f"✅ links.txt: {len(lines)} URLs")
        return [{"Pinterest_URL": u, "Status": "PENDING"} for u in lines]
    except Exception as e:
        logger.error(f"links.txt failed: {e}")
        return []


def mark_url_posted(pin_url: str):
    """Remove from links.txt, add to posted.txt."""
    try:
        # Remove from links.txt
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH, timeout=10)
        d = r.json()
        content = base64.b64decode(d["content"]).decode("utf-8")
        lines = [l for l in content.split("\n") if l.strip() != pin_url.strip()]
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/links.txt",
            headers=HEADERS_GH,
            json={"message": f"Auto: posted {pin_url[:40]}",
                  "sha": d["sha"],
                  "content": base64.b64encode("\n".join(lines).encode()).decode()})

        # Add to posted.txt
        r2 = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt",
            headers=HEADERS_GH, timeout=10)
        existing = base64.b64decode(r2.json()["content"]).decode("utf-8") if r2.status_code == 200 else "# Posted URLs\n"
        sha2 = r2.json().get("sha") if r2.status_code == 200 else None
        timestamp = time.strftime("%Y-%m-%d %H:%M IST")
        new_entry = f"{timestamp} | {pin_url}"
        new_posted = existing.rstrip() + "\n" + new_entry + "\n"
        payload = {"message": "Auto: mark posted",
                   "content": base64.b64encode(new_posted.encode()).decode()}
        if sha2:
            payload["sha"] = sha2
        requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt",
            headers=HEADERS_GH, json=payload)
        logger.info("✅ links.txt + posted.txt updated")
    except Exception as e:
        logger.warning(f"mark_url_posted: {e}")


def update_sheet_status(pin_url: str):
    """Mark URL as POSTED in Google Sheet via Apps Script."""
    try:
        WEBAPP_URL = ("https://script.google.com/macros/s/"
                      "AKfycbwkvG2B_ewPkyt2nibNa61i1SOiPno3yj5ikMexuPE6yo3q6xVkuShqbFt9gj5htqgZ/exec")
        r = requests.get(WEBAPP_URL, params={"url": pin_url}, timeout=20)
        logger.info(f"Sheet status update: {r.text[:100]}")
    except Exception as e:
        logger.warning(f"Sheet status update: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PINTEREST URL CLEANING
# Handles: pin.it/xxx, pinterest.com/pin/ID/, /pin/ID/sent/?invite_code=, etc.
# ─────────────────────────────────────────────────────────────────────────────

def get_clean_pin_url(original_url: str):
    """
    Returns (clean_url, pin_id) or (None, None).
    clean_url is always: https://www.pinterest.com/pin/{pin_id}/
    Resolves pin.it shortlinks first, then extracts pin ID from ANY path.
    """
    url = original_url.strip()

    # Resolve pin.it shortlinks (GitHub Actions IPs can do this)
    if "pin.it" in url:
        logger.info(f"Resolving shortlink: {url}")
        for method in ("HEAD", "GET"):
            try:
                fn = requests.head if method == "HEAD" else requests.get
                r = fn(url, timeout=15, headers=browser_headers(), allow_redirects=True)
                if "pinterest" in r.url:
                    url = r.url
                    logger.info(f"  Resolved ({method}) → {url[:80]}")
                    break
                # Also check for Location header in non-follow HEAD
                loc = r.headers.get("Location", "")
                if loc and "pinterest" in loc:
                    url = loc
                    logger.info(f"  Location header → {url[:80]}")
                    break
            except Exception as e:
                logger.warning(f"  {method} resolve: {e}")

    # Extract numeric pin ID from URL path
    # Works for: /pin/123456/, /pin/123456/sent/, /pin/123456/?ref=...
    m = re.search(r'/pin/(\d+)', url)
    if not m:
        logger.error(f"Cannot find pin ID in: {url}")
        return None, None

    pin_id = m.group(1)
    clean_url = f"https://www.pinterest.com/pin/{pin_id}/"
    logger.info(f"✅ Clean URL: {clean_url} (pin_id={pin_id})")
    return clean_url, pin_id


# ─────────────────────────────────────────────────────────────────────────────
# HTML FETCH — Direct + 4 proxy fallbacks
# Pinterest blocks GitHub Actions IPs; proxies work around this
# ─────────────────────────────────────────────────────────────────────────────

def fetch_html(url: str) -> str:
    """Fetch page HTML via direct request or proxies."""

    # Direct request
    try:
        r = requests.get(url, timeout=20, headers=browser_headers("https://www.google.com/"),
                         allow_redirects=True)
        if r.status_code == 200 and len(r.text) > 500:
            logger.info(f"✅ Direct fetch: {len(r.text):,} chars")
            return r.text
        logger.warning(f"Direct: HTTP {r.status_code}, {len(r.text)} chars")
    except Exception as e:
        logger.warning(f"Direct fetch: {e}")

    enc = urllib.parse.quote(url, safe="")

    # Proxy 1: allorigins.win
    try:
        r = requests.get(f"https://api.allorigins.win/get?url={enc}",
                         timeout=25, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200:
            html = r.json().get("contents", "")
            if len(html) > 500:
                logger.info(f"✅ allorigins: {len(html):,} chars")
                return html
    except Exception as e:
        logger.warning(f"allorigins: {e}")

    # Proxy 2: corsproxy.io
    try:
        r = requests.get(f"https://corsproxy.io/?{enc}",
                         timeout=25, headers=browser_headers())
        if r.status_code == 200 and len(r.text) > 500:
            logger.info(f"✅ corsproxy: {len(r.text):,} chars")
            return r.text
    except Exception as e:
        logger.warning(f"corsproxy: {e}")

    # Proxy 3: thingproxy
    try:
        r = requests.get(f"https://thingproxy.freeboard.io/fetch/{url}",
                         timeout=25, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200 and len(r.text) > 500:
            logger.info(f"✅ thingproxy: {len(r.text):,} chars")
            return r.text
    except Exception as e:
        logger.warning(f"thingproxy: {e}")

    # Proxy 4: codetabs
    try:
        r = requests.get(f"https://api.codetabs.com/v1/proxy?quest={enc}",
                         timeout=25, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200 and len(r.text) > 500:
            logger.info(f"✅ codetabs: {len(r.text):,} chars")
            return r.text
    except Exception as e:
        logger.warning(f"codetabs: {e}")

    logger.warning("All HTML fetch methods failed")
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE EXTRACTION FROM HTML
# ─────────────────────────────────────────────────────────────────────────────

def extract_image_from_html(html: str) -> str:
    """Extract highest-quality Pinterest image URL from page HTML."""
    if not html:
        return None

    patterns = [
        # og:image — most reliable, always highest available resolution
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        # CDN originals
        r'"contentUrl"\s*:\s*"(https://i\.pinimg\.com/originals/[^"]+)"',
        r'"url"\s*:\s*"(https://i\.pinimg\.com/originals/[^"]+)"',
        r'(https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp))',
        # 736x fallback
        r'(https://i\.pinimg\.com/736x/[a-f0-9/]+\.(?:jpg|jpeg|png|webp))',
        # 474x fallback
        r'(https://i\.pinimg\.com/474x/[a-f0-9/]+\.(?:jpg|jpeg|png|webp))',
        # Any pinimg
        r'(https://i\.pinimg\.com/[^\s"\'<>\\]+\.(?:jpg|jpeg|png|webp))',
    ]

    for pat in patterns:
        m = re.search(pat, html, re.I)
        if m:
            img = m.group(1).replace("&amp;", "&")
            if "pinimg.com" in img:
                img = re.sub(r'/\d+x\d*/', '/originals/', img)
                logger.info(f"✅ HTML extract: {img[:80]}")
                return img

    # JSON-LD
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


# ─────────────────────────────────────────────────────────────────────────────
# MAIN IMAGE EXTRACTION — 6 methods
# ─────────────────────────────────────────────────────────────────────────────

def get_pinterest_image(original_url: str) -> str:
    """
    Extract image URL from a Pinterest pin using 6 cascading methods.
    Always cleans the URL first (handles pin.it, /sent/, /repin/, etc.)
    """

    # ── Step 0: Get clean canonical URL + pin ID ───────────────────────────
    clean_url, pin_id = get_clean_pin_url(original_url)
    if not clean_url or not pin_id:
        raise ValueError(f"Cannot extract pin ID from: {original_url}")
    logger.info(f"Working | pin_id={pin_id} | url={clean_url}")

    # ── Method 1: oEmbed API ───────────────────────────────────────────────
    # Try original URL first (pin.it sometimes works in oEmbed), then clean URL
    for try_url in list(dict.fromkeys([original_url, clean_url])):
        try:
            r = requests.get(
                f"https://www.pinterest.com/oembed.json?url={urllib.parse.quote(try_url)}",
                timeout=12, headers=browser_headers("https://www.pinterest.com/"))
            if r.status_code == 200:
                data = r.json()
                img = data.get("thumbnail_url", "")
                # Upgrade resolution: replace 236x/474x/736x with originals
                for res in ["236x", "474x", "736x"]:
                    img = img.replace(f"/{res}/", "/originals/")
                if img and "pinimg.com" in img:
                    logger.info(f"✅ Method 1 oEmbed: {img[:80]}")
                    return img
            else:
                logger.warning(f"oEmbed HTTP {r.status_code} for {try_url[:50]}")
        except Exception as e:
            logger.warning(f"oEmbed ({try_url[:40]}): {e}")

    # ── Method 2: Pinterest internal PinResource API ───────────────────────
    try:
        api_url = (
            f"https://www.pinterest.com/resource/PinResource/get/"
            f"?source_url=/pin/{pin_id}/"
            f"&data=%7B%22options%22%3A%7B%22id%22%3A%22{pin_id}%22%7D%7D"
        )
        r = requests.get(api_url, timeout=12, headers={
            **browser_headers("https://www.pinterest.com/"),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        })
        if r.status_code == 200:
            # Search the entire JSON response for pinimg URLs
            for pat in [
                r'https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp)',
                r'https://i\.pinimg\.com/736x/[a-f0-9/]+\.(?:jpg|jpeg|png|webp)',
                r'https://i\.pinimg\.com/[^\s"\'\\]+\.(?:jpg|jpeg|png|webp)',
            ]:
                m = re.search(pat, r.text, re.I)
                if m:
                    img = re.sub(r'/\d+x\d*/', '/originals/', m.group(0))
                    logger.info(f"✅ Method 2 PinResource API: {img[:80]}")
                    return img
        logger.warning(f"PinResource API: HTTP {r.status_code}")
    except Exception as e:
        logger.warning(f"PinResource API: {e}")

    # ── Method 3: Scrape clean pin page (direct + 4 proxies) ──────────────
    html = fetch_html(clean_url)
    img = extract_image_from_html(html)
    if img:
        logger.info(f"✅ Method 3 HTML scrape: {img[:80]}")
        return img

    # ── Method 4: Wayback Machine (archive.org) ────────────────────────────
    try:
        logger.info("Trying Wayback Machine...")
        r = requests.get(
            f"https://archive.org/wayback/available?url=pinterest.com/pin/{pin_id}/",
            timeout=15, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200:
            snap = r.json().get("archived_snapshots", {}).get("closest", {})
            if snap.get("available") and snap.get("url"):
                logger.info(f"Wayback snapshot: {snap['url']}")
                html2 = fetch_html(snap["url"])
                img = extract_image_from_html(html2)
                if img:
                    logger.info(f"✅ Method 4 Wayback: {img[:80]}")
                    return img
    except Exception as e:
        logger.warning(f"Wayback: {e}")

    # ── Method 5: Pinterest mobile/pidget API ──────────────────────────────
    try:
        r = requests.get(
            f"https://api.pinterest.com/v3/pidgets/pins/info/?pin_ids={pin_id}",
            timeout=12, headers={
                "User-Agent": "Pinterest/10.0 (iPhone; iOS 16.0; Scale/2.0)",
                "Accept": "application/json",
            })
        if r.status_code == 200:
            for pat in [
                r'https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp)',
                r'https://i\.pinimg\.com/[^\s"\'\\]+\.(?:jpg|jpeg|png|webp)',
            ]:
                m = re.search(pat, r.text, re.I)
                if m:
                    img = re.sub(r'/\d+x\d*/', '/originals/', m.group(0))
                    logger.info(f"✅ Method 5 Mobile API: {img[:80]}")
                    return img
        logger.warning(f"Mobile API: HTTP {r.status_code}")
    except Exception as e:
        logger.warning(f"Mobile API: {e}")

    # ── Method 6: Pinterest GraphQL API ───────────────────────────────────
    try:
        payload = {
            "options": {
                "field_set_key": "unauth_react",
                "id": pin_id,
            },
            "context": {}
        }
        r = requests.get(
            "https://www.pinterest.com/resource/PinResource/get/",
            params={"source_url": f"/pin/{pin_id}/",
                    "data": json.dumps(payload),
                    "_": str(int(time.time() * 1000))},
            headers={
                **browser_headers("https://www.pinterest.com/"),
                "X-Pinterest-AppState": "active",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=15)
        if r.status_code == 200:
            m = re.search(
                r'https://i\.pinimg\.com/[^\s"\'\\]+\.(?:jpg|jpeg|png|webp)',
                r.text, re.I)
            if m:
                img = re.sub(r'/\d+x\d*/', '/originals/', m.group(0))
                logger.info(f"✅ Method 6 GraphQL: {img[:80]}")
                return img
        logger.warning(f"GraphQL: HTTP {r.status_code}")
    except Exception as e:
        logger.warning(f"GraphQL: {e}")

    raise ValueError(f"All 6 methods exhausted | pin_id={pin_id} | url={original_url}")


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE DOWNLOAD
# ─────────────────────────────────────────────────────────────────────────────



def download_image(image_url: str) -> str:
    """Download Pinterest image to /tmp/post.jpg. Tries multiple resolutions."""
    img_headers = {
        **browser_headers("https://www.pinterest.com/"),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
    }

    # Build URL variants to try (highest resolution first)
    urls = [image_url]
    if "originals" in image_url:
        urls += [image_url.replace("originals", "736x"),
                 image_url.replace("originals", "474x")]
    elif "736x" in image_url:
        urls += [image_url.replace("736x", "originals"),
                 image_url.replace("736x", "474x")]

    for url in urls:
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
                        logger.info(f"✅ Downloaded {size:,} bytes | {url[:60]}")
                        return path
                    logger.warning(f"File too small: {size} bytes")
                else:
                    logger.warning(f"HTTP {r.status_code}: {url[:60]}")
            except Exception as e:
                logger.warning(f"Download attempt {attempt+1}: {e}")
            time.sleep(1)

    raise ValueError(f"Cannot download image from: {image_url}")


# ─────────────────────────────────────────────────────────────────────────────
# CDN UPLOAD — 3 options, auto-fallback
# ─────────────────────────────────────────────────────────────────────────────

def upload_to_cdn(image_path: str) -> str:
    """Upload image to a public CDN so Instagram can fetch it."""

    # Option 1: catbox.moe — permanent free hosting
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                files={"fileToUpload": ("img.jpg", f, "image/jpeg")},
                data={"reqtype": "fileupload", "userhash": ""},
                timeout=60)
        url = r.text.strip()
        if r.status_code == 200 and url.startswith("https://"):
            logger.info(f"✅ CDN catbox: {url}")
            return url
    except Exception as e:
        logger.warning(f"catbox: {e}")

    # Option 2: litterbox.catbox.moe — 72h hosting
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                files={"fileToUpload": ("img.jpg", f, "image/jpeg")},
                data={"reqtype": "fileupload", "time": "72h"},
                timeout=60)
        url = r.text.strip()
        if r.status_code == 200 and url.startswith("https://"):
            logger.info(f"✅ CDN litterbox: {url}")
            return url
    except Exception as e:
        logger.warning(f"litterbox: {e}")

    # Option 3: GitHub raw — always works, uses your own repo
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        fname = f"storage/img_{int(time.time())}.jpg"
        r = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{fname}",
            headers=HEADERS_GH,
            json={"message": "tmp: post image", "content": img_b64},
            timeout=30)
        if r.status_code in [200, 201]:
            time.sleep(3)  # Wait for GitHub CDN propagation
            url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{fname}"
            logger.info(f"✅ CDN GitHub raw: {url}")
            return url
    except Exception as e:
        logger.warning(f"GitHub raw: {e}")

    raise ValueError("All 3 CDN uploads failed!")


# ─────────────────────────────────────────────────────────────────────────────
# INSTAGRAM GRAPH API
# ─────────────────────────────────────────────────────────────────────────────

def image_to_video(image_path: str) -> str:
    """
    Convert a JPG image to a 9:16 MP4 video for Instagram Reels.
    Uses ffmpeg (installed via apt in GitHub Actions workflow).
    Output: 1080x1920, 7 seconds, h264, no audio.
    """
    import subprocess, shutil

    output = "/tmp/reel.mp4"

    # Find ffmpeg — use absolute path to avoid PATH issues
    ffmpeg_bin = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    logger.info(f"ffmpeg path: {ffmpeg_bin}")

    if not os.path.exists(ffmpeg_bin):
        raise ValueError(
            f"ffmpeg not found at {ffmpeg_bin}. "
            "Make sure 'sudo apt-get install -y ffmpeg' runs before this step.")

    # Step 1: Create 9:16 padded frame with blurred background
    padded = "/tmp/reel_frame.jpg"
    pad_cmd = [
        ffmpeg_bin, "-y", "-i", image_path,
        "-vf",
        "split[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=20:20[blurred];"
        "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[sharp];"
        "[blurred][sharp]overlay=(W-w)/2:(H-h)/2",
        "-frames:v", "1", "-q:v", "2", padded
    ]
    r1 = subprocess.run(pad_cmd, capture_output=True, text=True, timeout=60)
    if r1.returncode != 0 or not os.path.exists(padded):
        logger.warning(f"Blur pad failed ({r1.returncode}) — using original image")
        padded = image_path

    # Step 2: Image → 7-second MP4
    video_cmd = [
        ffmpeg_bin, "-y",
        "-loop", "1",
        "-i", padded,
        "-t", "7",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-r", "30",
        "-an",
        output
    ]
    logger.info(f"Running ffmpeg video conversion...")
    r2 = subprocess.run(video_cmd, capture_output=True, text=True, timeout=120)
    if r2.returncode != 0:
        raise ValueError(f"ffmpeg conversion failed (code {r2.returncode}): {r2.stderr[-600:]}")

    size = os.path.getsize(output)
    logger.info(f"✅ MP4 created: {size:,} bytes | 7s | 1080x1920")
    if size < 10000:
        raise ValueError(f"MP4 suspiciously small ({size}b) — check ffmpeg output")
    return output


def post_to_instagram(image_path: str) -> str:
    """
    Convert photo to MP4, upload to CDN, post as Instagram REEL.
    Instagram Reels API requires video_url — cannot use image_url for Reels.
    """
    logger.info(f"Preparing Reel | account={INSTAGRAM_ACCOUNT_ID}")

    # Step 1: Convert image → MP4 (required by Instagram Reels API)
    video_path = image_to_video(image_path)

    # Step 2: Upload MP4 to public CDN
    video_url = upload_to_cdn(video_path)
    logger.info(f"Video CDN URL: {video_url}")

    # Step 3: Create Reel container with video_url
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={
            "video_url":     video_url,
            "media_type":    "REELS",
            "caption":       CAPTION,
            "share_to_feed": "true",
            "access_token":  INSTAGRAM_ACCESS_TOKEN,
        }, timeout=60)
    logger.info(f"Container: HTTP {r.status_code} | {r.text[:300]}")
    if r.status_code != 200:
        raise ValueError(f"Reel container failed: {r.text}")

    container_id = r.json()["id"]
    logger.info(f"Container ID: {container_id} — polling (video takes ~30-90s)...")

    # Step 4: Poll until FINISHED (videos take longer than images)
    for attempt in range(24):   # 24 × 10s = 4 min max
        time.sleep(10)
        s = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code", "access_token": INSTAGRAM_ACCESS_TOKEN},
            timeout=15)
        if s.status_code == 200:
            code = s.json().get("status_code", "UNKNOWN")
            logger.info(f"  [{attempt+1}/24] status: {code}")
            if code == "FINISHED":
                logger.info("✅ Video processed!")
                break
            if code in ("ERROR", "EXPIRED"):
                raise ValueError(f"Container failed with status: {s.json()}")
        else:
            logger.warning(f"  Poll HTTP {s.status_code}")
    else:
        raise ValueError("Video processing timed out after 4 minutes")

    # Step 5: Publish
    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN},
        timeout=30)
    logger.info(f"Publish: HTTP {r2.status_code} | {r2.text[:300]}")
    if r2.status_code != 200:
        raise ValueError(f"Reel publish failed: {r2.text}")

    post_id = r2.json()["id"]
    logger.info(f"🎬 REEL POSTED! ID: {post_id}")
    return post_id


# ─────────────────────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────

def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("No Telegram token set")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10)
        logger.info("✅ Telegram sent")
    except Exception as e:
        logger.warning(f"Telegram: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("🚀 Pinterest → Instagram Auto Poster | v6 FINAL")
    logger.info(f"   Account : {INSTAGRAM_ACCOUNT_ID}")
    logger.info(f"   Sheet   : {GOOGLE_SHEET_ID}")
    logger.info(f"   Repo    : {GITHUB_REPO}")
    logger.info("=" * 60)

    # Load queue
    rows = get_sheet_rows()
    pending = []
    for row in rows:
        status = (row.get("Status") or row.get("status") or "").strip().upper()
        url = (row.get("Pinterest_URL") or row.get("pinterest_url")
               or row.get("Pinterest URL") or "").strip()
        if status == "PENDING" and url:
            pending.append(url)

    logger.info(f"📊 {len(pending)} PENDING URLs in queue")

    if not pending:
        logger.warning("Queue is empty!")
        send_telegram(
            "⚠️ <b>Queue Empty!</b>\n\n"
            "No PENDING URLs found.\n"
            "Add Pinterest URLs with Status=PENDING to your Google Sheet:\n"
            f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
        return

    # Try up to 5 URLs — skip bad ones, post first success
    MAX_TRY = min(5, len(pending))
    posted = False
    skip_count = 0

    for i, pin_url in enumerate(pending[:MAX_TRY], 1):
        logger.info(f"\n{'─'*50}")
        logger.info(f"📌 Attempt {i}/{MAX_TRY}: {pin_url}")

        try:
            image_url  = get_pinterest_image(pin_url)
            img_path   = download_image(image_url)
            post_id    = post_to_instagram(img_path)

            logger.info(f"🎉 SUCCESS! Instagram Post ID: {post_id}")
            mark_url_posted(pin_url)
            update_sheet_status(pin_url)

            send_telegram(
                f"✅ <b>Posted to Instagram!</b>\n\n"
                f"🔗 {pin_url}\n"
                f"📸 Post ID: <code>{post_id}</code>\n"
                f"🕐 {time.strftime('%Y-%m-%d %H:%M')} IST\n"
                f"📊 {len(pending) - i} URLs remaining in queue")
            posted = True
            break

        except ValueError as e:
            err = str(e)
            # Extraction failure = bad URL → skip silently and try next
            if any(k in err for k in ["Cannot extract pin ID", "All 6 methods", "Cannot find pin"]):
                skip_count += 1
                logger.warning(f"⏭  Skipping (bad URL #{skip_count}): {err[:80]}")
                continue
            # Other failures (IG, CDN) → alert and stop
            logger.error(f"❌ Fatal error: {err}")
            send_telegram(
                f"❌ <b>Post Failed!</b>\n\n"
                f"🔗 {pin_url}\n"
                f"⚠️ <code>{err[:400]}</code>\n\n"
                f"Will retry at next scheduled run.")
            break

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            send_telegram(
                f"❌ <b>Unexpected Error!</b>\n\n"
                f"🔗 {pin_url}\n"
                f"⚠️ <code>{str(e)[:400]}</code>")
            break

    if not posted:
        logger.error(f"Failed after {MAX_TRY} attempts ({skip_count} skipped)")
        send_telegram(
            f"⚠️ <b>Could Not Post!</b>\n\n"
            f"Tried {MAX_TRY} URLs, none worked.\n\n"
            f"URLs attempted:\n"
            + "\n".join(f"• {u}" for u in pending[:MAX_TRY])
            + "\n\n<b>Please check your Pinterest URLs are valid public pins.</b>\n"
            f"Use: <code>https://pinterest.com/pin/123456789/</code>")


if __name__ == "__main__":
    main()





