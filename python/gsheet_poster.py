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

import os, re, time, logging, csv, io, random, json, urllib.parse
import requests
import base64

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

import random as _random

# Rotating viral hook captions — each post gets a different one
# Research-backed: pattern interrupt + desire + CTA = max saves & shares
_CAPTIONS = [
    """POV: You finally figured out how to dress 🔥

Most guys dress basic their whole life.
This look changes everything.

✅ Save this before your friends steal it
💬 Comment "FIT" and I'll send you the details
👔 Follow @styleformenindia — new fits daily

#mensfashion #mensstyle #indianmensfashion #outfitoftheday #fashionreels #styleformen #menswear #ootd #outfitinspo #fashiontips #streetwear #casualstyle #swag #styleinspo #viralmenfashion #dappermen #fashionformen #outfitideas #mensfashionpost #reelsviral""",

    """The outfit that will make people stop and stare 👀

No cap — this is the look you wear when you want to be remembered.

📌 Save this for your next event
💬 Comment "DETAILS" for outfit breakdown
👔 Follow @styleformenindia for daily inspo

#mensfashion #mensstyle #outfitideas #indianmensfashion #fashionreels #styleformen #menswear #ootd #dapperstyle #classymen #gentlemanstyle #styleinspo #fashiontips #mensfashionblogger #reelsviral #viralreels #outfitinspiration #casualstyle #streetwear #trendingfashion""",

    """Why do stylish men always look confident? 🤔

Because the right outfit isn't just clothes —
it's armour. It's a statement. It's YOU.

This is yours to steal. 💪

📌 Save it. You'll thank me later.
💬 Drop "🔥" if this hits different
👔 Follow @styleformenindia

#mensfashion #confidence #mensstyle #indianmensfashion #fashionreels #styleformen #menswear #ootd #outfitoftheday #styleinspo #fashiontips #dapper #gentlemen #viralmenfashion #reelsviral #outfitideas #streetwear #casualstyle #swagstyle #trending""",

    """Nobody talks about how much a good outfit changes your life 💯

Job interviews. First dates. Walking into a room.
The right fit = instant respect.

Start here. 👇

✅ Save this look
💬 Comment "STYLE" for a full guide
👔 Follow @styleformenindia — level up daily

#mensfashion #mensstyle #outfitideas #indianmensfashion #fashionreels #styleformen #menswear #ootd #fashiontips #styleinspo #dapperstyle #gentlemanstyle #reelsviral #viralreels #trending #outfitinspiration #casualstyle #streetwear #swag #mensfashionpost""",

    """This outfit goes HARD 🔥🔥🔥

If you know, you know.
If you don't — that's what @styleformenindia is for.

📌 Save before it's gone
💬 Tag someone who needs this
👔 Follow for daily men's fashion that actually slaps

#mensfashion #mensstyle #outfitoftheday #indianmensfashion #fashionreels #styleformen #menswear #ootd #outfitinspo #styleinspo #fashiontips #streetwear #casualstyle #reelsviral #viralreels #trending #trendingfashion #swagstyle #dapper #outfitideas""",

    """Upgrade your wardrobe. Upgrade your life. 💎

The difference between looking good and looking GREAT
is knowing what works for YOU.

This works. Trust.

📌 Save this look for your next purchase
💬 Comment "LINK" for exact products
👔 Follow @styleformenindia for more

#mensfashion #mensstyle #indianmensfashion #fashionreels #styleformen #menswear #outfitideas #ootd #styleinspo #fashiontips #dapperstyle #gentlemen #classymen #reelsviral #viralreels #trending #outfitinspiration #streetwear #casualstyle #swag""",

    """Men who dress well never go unnoticed 👑

This is your sign to stop dressing average.

3 rules:
✅ Fit matters more than brand
✅ Colours that complement your skin
✅ Accessories seal the deal

Save this. Share it. Live it.
👔 Follow @styleformenindia

#mensfashion #mensstyle #outfitideas #indianmensfashion #fashionreels #styleformen #menswear #ootd #fashiontips #styleinspo #dapper #gentlemanstyle #classymen #reelsviral #viralreels #trending #outfitoftheday #streetwear #casualstyle #swagstyle""",

    """This is the fit that makes her double-tap 😮‍💨🔥

You don't need expensive clothes.
You need the RIGHT clothes.

📌 Save this look before you forget
💬 Comment "FIT CHECK" and I'll break it down
👔 Follow @styleformenindia — 3 fits posted daily

#mensfashion #mensstyle #indianmensfashion #fashionreels #styleformen #menswear #ootd #outfitoftheday #styleinspo #fashiontips #streetwear #casualstyle #reelsviral #viralreels #trending #trendingfashion #outfitideas #swag #dapper #gentlemen""",
]

def get_caption():
    """Return a random viral caption — different every post."""
    return _random.choice(_CAPTIONS)

CAPTION = get_caption()  # Set once per run


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
    url = original_url.strip()
    if "pin.it" in url:
        logger.info("Resolving shortlink: " + url)
        for method in ("HEAD", "GET"):
            try:
                fn = requests.head if method == "HEAD" else requests.get
                r = fn(url, timeout=15, headers=browser_headers(), allow_redirects=True)
                if "pinterest" in r.url:
                    url = r.url
                    logger.info("  Resolved (" + method + ") → " + url[:80])
                    break
                loc = r.headers.get("Location", "")
                if loc and "pinterest" in loc:
                    url = loc
                    break
            except Exception as e:
                logger.warning("  " + method + " resolve: " + str(e))
    m = re.search(r'/pin/(\d+)', url)
    if not m:
        logger.error("Cannot find pin ID in: " + url)
        return None, None
    pin_id = m.group(1)
    clean_url = "https://www.pinterest.com/pin/" + pin_id + "/"
    logger.info("✅ Clean URL: " + clean_url + " (pin_id=" + pin_id + ")")
    return clean_url, pin_id


def fetch_html(url: str) -> str:
    try:
        r = requests.get(url, timeout=20, headers=browser_headers("https://www.google.com/"), allow_redirects=True)
        if r.status_code == 200 and len(r.text) > 500:
            logger.info("✅ Direct fetch: " + str(len(r.text)) + " chars")
            return r.text
    except Exception as e:
        logger.warning("Direct fetch: " + str(e))

    enc = urllib.parse.quote(url, safe="")
    for name, proxy_url in [
        ("allorigins", "https://api.allorigins.win/get?url=" + enc),
        ("corsproxy",  "https://corsproxy.io/?" + enc),
        ("thingproxy", "https://thingproxy.freeboard.io/fetch/" + url),
        ("codetabs",   "https://api.codetabs.com/v1/proxy?quest=" + enc),
    ]:
        try:
            r = requests.get(proxy_url, timeout=25, headers={"User-Agent": USER_AGENTS[0]})
            if r.status_code == 200:
                html = r.json().get("contents", "") if name == "allorigins" else r.text
                if len(html) > 500:
                    logger.info("✅ " + name + ": " + str(len(html)) + " chars")
                    return html
        except Exception as e:
            logger.warning(name + ": " + str(e))
    return ""


def extract_media_from_html(html: str) -> tuple:
    """Returns (url, is_video). Checks video FIRST."""
    if not html:
        return None, False

    # VIDEO: og:video meta tag
    for pat in [
        r'property=["\']og:video(?::url)?["\'][^>]+content=["\']([^"\']+)["\']',
        r'content=["\']([^"\']+)["\'][^>]+property=["\']og:video(?::url)?["\']',
    ]:
        m = re.search(pat, html, re.I)
        if m:
            u = m.group(1).replace("&amp;", "&")
            if u:
                logger.info("✅ og:video: " + u[:80])
                return u, True

    # VIDEO: v.pinimg.com CDN mp4
    m = re.search(r'https://v\d*[.]pinimg[.]com/[^\s"\'<>\\]+[.]mp4[^\s"\'<>\\]*', html, re.I)
    if m:
        logger.info("✅ CDN video: " + m.group(0)[:80])
        return m.group(0), True

    # VIDEO: any mp4 URL in JSON
    m = re.search(r'"video_url"\s*:\s*"(https://[^"]+[.]mp4[^"]*)"', html)
    if m:
        logger.info("✅ video_url JSON: " + m.group(1)[:80])
        return m.group(1), True

    # VIDEO: JSON-LD VideoObject
    for block in re.findall(r'<script[^>]+type=["\']application/ld[+]json["\'][^>]*>([\s\S]*?)</script>', html, re.I):
        try:
            data = json.loads(block)
            if data.get("@type") in ("VideoObject", "Video"):
                u = data.get("contentUrl") or data.get("url", "")
                if u:
                    logger.info("✅ JSON-LD VideoObject: " + u[:80])
                    return u, True
        except Exception:
            pass

    # IMAGE: og:image
    for pat in [
        r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]:
        m = re.search(pat, html, re.I)
        if m:
            img = m.group(1).replace("&amp;", "&")
            if "pinimg.com" in img:
                img = re.sub(r'/\d+x\d*/', '/originals/', img)
                logger.info("✅ og:image: " + img[:80])
                return img, False

    # IMAGE: CDN patterns
    for pat in [
        r'https://i[.]pinimg[.]com/originals/[a-f0-9/]+[.](jpg|jpeg|png|webp)',
        r'https://i[.]pinimg[.]com/736x/[a-f0-9/]+[.](jpg|jpeg|png|webp)',
        r'https://i[.]pinimg[.]com/[^\s"\'<>\\]+[.](jpg|jpeg|png|webp)',
    ]:
        m = re.search(pat, html, re.I)
        if m:
            img = re.sub(r'/\d+x\d*/', '/originals/', m.group(0))
            logger.info("✅ CDN image: " + img[:80])
            return img, False

    # IMAGE: JSON-LD
    for block in re.findall(r'<script[^>]+type=["\']application/ld[+]json["\'][^>]*>([\s\S]*?)</script>', html, re.I):
        try:
            data = json.loads(block)
            imgs = data.get("image", [])
            if isinstance(imgs, str):
                imgs = [imgs]
            for img in (imgs if isinstance(imgs, list) else []):
                if "pinimg.com" in str(img):
                    img = re.sub(r'/\d+x\d*/', '/originals/', str(img))
                    logger.info("✅ JSON-LD image: " + img[:80])
                    return img, False
        except Exception:
            pass

    return None, False


def get_pinterest_media(original_url: str) -> tuple:
    """
    Extract media URL from Pinterest pin.
    Returns (url, is_video). Detects video pins correctly.
    """
    clean_url, pin_id = get_clean_pin_url(original_url)
    if not clean_url or not pin_id:
        raise ValueError("Cannot extract pin ID from: " + original_url)
    logger.info("Working | pin_id=" + pin_id + " | url=" + clean_url)

    # Method 1: oEmbed
    for try_url in list(dict.fromkeys([original_url, clean_url])):
        try:
            r = requests.get(
                "https://www.pinterest.com/oembed.json?url=" + urllib.parse.quote(try_url),
                timeout=12, headers=browser_headers("https://www.pinterest.com/"))
            if r.status_code == 200:
                data = r.json()
                oe_type = data.get("type", "")
                oe_html = data.get("html", "")
                if oe_type == "video" or ".mp4" in oe_html:
                    mp4 = re.search(r"src=['\"]([^'\"]+\.mp4[^'\"]*)['\"]", oe_html)
                    if mp4:
                        logger.info("✅ Method 1 oEmbed VIDEO: " + mp4.group(1)[:80])
                        return mp4.group(1), True
                img = data.get("thumbnail_url", "")
                for res in ["236x", "474x", "736x"]:
                    img = img.replace("/" + res + "/", "/originals/")
                if img and "pinimg.com" in img:
                    logger.info("✅ Method 1 oEmbed IMAGE: " + img[:80])
                    return img, False
        except Exception as e:
            logger.warning("oEmbed: " + str(e))

    # Method 2: PinResource API
    try:
        r = requests.get(
            "https://www.pinterest.com/resource/PinResource/get/"
            "?source_url=/pin/" + pin_id + "/"
            "&data=%7B%22options%22%3A%7B%22id%22%3A%22" + pin_id + "%22%7D%7D",
            timeout=12, headers=dict(
                list(browser_headers("https://www.pinterest.com/").items()) +
                [("X-Requested-With", "XMLHttpRequest"), ("Accept", "application/json")]
            ))
        if r.status_code == 200:
            raw = r.text
            vm = re.search(r'v\d*[.]pinimg[.]com/[^\s"\'\\]+[.]mp4', raw, re.I)
            if vm:
                logger.info("✅ Method 2 API VIDEO: " + vm.group(0)[:80])
                return vm.group(0), True
            im = re.search(r'https://i[.]pinimg[.]com/originals/[a-f0-9/]+[.](jpg|jpeg|png|webp)', raw, re.I)
            if im:
                logger.info("✅ Method 2 API IMAGE: " + im.group(0)[:80])
                return im.group(0), False
    except Exception as e:
        logger.warning("PinResource: " + str(e))

    # Method 3: HTML scrape
    html = fetch_html(clean_url)
    u3, v3 = extract_media_from_html(html)
    if u3:
        logger.info("✅ Method 3 HTML: " + ("VIDEO" if v3 else "IMAGE") + " " + u3[:80])
        return u3, v3

    # Method 4: Wayback
    try:
        r = requests.get(
            "https://archive.org/wayback/available?url=pinterest.com/pin/" + pin_id + "/",
            timeout=15, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200:
            snap = r.json().get("archived_snapshots", {}).get("closest", {})
            if snap.get("available") and snap.get("url"):
                html2 = fetch_html(snap["url"])
                u4, v4 = extract_media_from_html(html2)
                if u4:
                    logger.info("✅ Method 4 Wayback: " + ("VIDEO" if v4 else "IMAGE"))
                    return u4, v4
    except Exception as e:
        logger.warning("Wayback: " + str(e))

    # Method 5: Mobile API
    try:
        r = requests.get(
            "https://api.pinterest.com/v3/pidgets/pins/info/?pin_ids=" + pin_id,
            timeout=12, headers={
                "User-Agent": "Pinterest/10.0 (iPhone; iOS 16.0; Scale/2.0)",
                "Accept": "application/json"})
        if r.status_code == 200:
            raw = r.text
            vm = re.search(r'v\d*[.]pinimg[.]com/[^\s"\'\\]+[.]mp4', raw, re.I)
            if vm:
                logger.info("✅ Method 5 Mobile VIDEO: " + vm.group(0)[:80])
                return vm.group(0), True
            im = re.search(r'https://i[.]pinimg[.]com/[^\s"\'\\]+[.](jpg|jpeg|png|webp)', raw, re.I)
            if im:
                img = re.sub(r'/\d+x\d*/', '/originals/', im.group(0))
                logger.info("✅ Method 5 Mobile IMAGE: " + img[:80])
                return img, False
    except Exception as e:
        logger.warning("Mobile API: " + str(e))

    raise ValueError("All 5 methods exhausted | pin_id=" + pin_id + " | url=" + original_url)


def is_video_url(url: str) -> bool:
    """Detect if a URL points to a video file."""
    video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v')
    url_lower = url.lower().split('?')[0]
    return any(url_lower.endswith(ext) for ext in video_exts)


def download_media(media_url: str) -> tuple:
    """
    Download image or video from URL.
    Returns (local_path, is_video) tuple.
    - Images saved as /tmp/post.jpg
    - Videos saved as /tmp/post.mp4
    Auto-detects type from URL extension or Content-Type header.
    """
    dl_headers = {
        **browser_headers("https://www.pinterest.com/"),
        "Accept": "*/*",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "no-cors",
    }

    # Build URL variants for images (try highest res first)
    urls = [media_url]
    if not is_video_url(media_url):
        if "originals" in media_url:
            urls += [media_url.replace("originals", "736x"),
                     media_url.replace("originals", "474x")]
        elif "736x" in media_url:
            urls += [media_url.replace("736x", "originals"),
                     media_url.replace("736x", "474x")]

    for url in urls:
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=60, headers=dl_headers,
                                 allow_redirects=True, stream=True)
                if r.status_code == 200:
                    # Detect type from Content-Type or URL
                    ctype = r.headers.get("Content-Type", "")
                    detected_video = (
                        "video" in ctype
                        or is_video_url(url)
                        or is_video_url(r.url)
                    )
                    path = "/tmp/post.mp4" if detected_video else "/tmp/post.jpg"
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                    size = os.path.getsize(path)
                    if size > 5000:
                        kind = "VIDEO" if detected_video else "IMAGE"
                        logger.info(f"✅ Downloaded {kind}: {size:,} bytes | {url[:60]}")
                        return path, detected_video
                    logger.warning(f"Too small ({size}b), trying next")
                else:
                    logger.warning(f"HTTP {r.status_code}: {url[:60]}")
            except Exception as e:
                logger.warning(f"Download attempt {attempt+1}: {e}")
            time.sleep(1)

    raise ValueError(f"Cannot download media from: {media_url}")


# ─────────────────────────────────────────────────────────────────────────────
# CDN UPLOAD — 3 options, auto-fallback
# ─────────────────────────────────────────────────────────────────────────────

def upload_to_cdn(file_path: str) -> str:
    """
    Upload image or video to a public CDN.
    Automatically detects file type (jpg/mp4) and sets correct mime type.
    Instagram requires publicly accessible URL for both images and videos.
    """
    is_video = file_path.endswith(".mp4")
    mime     = "video/mp4"  if is_video else "image/jpeg"
    fname_cdn = "reel.mp4"  if is_video else "img.jpg"
    ext       = ".mp4"      if is_video else ".jpg"
    logger.info(f"Uploading {'video' if is_video else 'image'} to CDN: {file_path}")

    # Option 1: catbox.moe — permanent, supports mp4
    try:
        with open(file_path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                files={"fileToUpload": (fname_cdn, f, mime)},
                data={"reqtype": "fileupload", "userhash": ""},
                timeout=120)
        url = r.text.strip()
        if r.status_code == 200 and url.startswith("https://"):
            logger.info(f"✅ CDN catbox: {url}")
            return url
        logger.warning(f"catbox: HTTP {r.status_code} | {r.text[:100]}")
    except Exception as e:
        logger.warning(f"catbox: {e}")

    # Option 2: litterbox — 72h, supports mp4
    try:
        with open(file_path, "rb") as f:
            r = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                files={"fileToUpload": (fname_cdn, f, mime)},
                data={"reqtype": "fileupload", "time": "72h"},
                timeout=120)
        url = r.text.strip()
        if r.status_code == 200 and url.startswith("https://"):
            logger.info(f"✅ CDN litterbox: {url}")
            return url
        logger.warning(f"litterbox: HTTP {r.status_code} | {r.text[:100]}")
    except Exception as e:
        logger.warning(f"litterbox: {e}")

    # Option 3: GitHub raw — always works, correct extension for video
    try:
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        gh_fname = f"storage/post_{int(time.time())}{ext}"
        r = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{gh_fname}",
            headers=HEADERS_GH,
            json={"message": f"tmp: post {'video' if is_video else 'image'}", "content": b64},
            timeout=60)
        if r.status_code in [200, 201]:
            time.sleep(5)  # Wait for GitHub CDN to propagate
            url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{gh_fname}"
            logger.info(f"✅ CDN GitHub raw: {url}")
            return url
        logger.warning(f"GitHub raw: HTTP {r.status_code} | {r.json().get('message','')}")
    except Exception as e:
        logger.warning(f"GitHub raw: {e}")

    raise ValueError("All 3 CDN uploads failed!")


# ─────────────────────────────────────────────────────────────────────────────
# INSTAGRAM GRAPH API
# ─────────────────────────────────────────────────────────────────────────────

def post_as_photo(image_path: str) -> str:
    """Upload JPG and post as Instagram PHOTO post."""
    logger.info("📸 Posting as PHOTO")
    public_url = upload_to_cdn(image_path)
    logger.info(f"Image CDN: {public_url}")

    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={
            "image_url":    public_url,
            "caption":      get_caption(),
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        }, timeout=30)
    logger.info(f"Container: HTTP {r.status_code} | {r.text[:200]}")
    if r.status_code != 200:
        raise ValueError(f"Photo container failed: {r.text}")

    container_id = r.json()["id"]

    # Poll until FINISHED
    for attempt in range(12):
        time.sleep(5)
        s = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code", "access_token": INSTAGRAM_ACCESS_TOKEN},
            timeout=10)
        if s.status_code == 200:
            code = s.json().get("status_code", "")
            logger.info(f"  [{attempt+1}/12] {code}")
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED"):
                raise ValueError(f"Photo container error: {s.json()}")
    
    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN},
        timeout=30)
    if r2.status_code != 200:
        raise ValueError(f"Photo publish failed: {r2.text}")

    post_id = r2.json()["id"]
    logger.info(f"📸 PHOTO POSTED! ID: {post_id}")
    return post_id


def post_as_reel(video_path: str) -> str:
    """Upload MP4 and post as Instagram REEL."""
    logger.info("🎬 Posting as REEL")
    video_url = upload_to_cdn(video_path)
    logger.info(f"Video CDN: {video_url}")

    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={
            "video_url":     video_url,
            "media_type":    "REELS",
            "caption":       get_caption(),
            "share_to_feed": "true",
            "access_token":  INSTAGRAM_ACCESS_TOKEN,
        }, timeout=60)
    logger.info(f"Container: HTTP {r.status_code} | {r.text[:200]}")
    if r.status_code != 200:
        raise ValueError(f"Reel container failed: {r.text}")

    container_id = r.json()["id"]
    logger.info(f"Container ID: {container_id} — polling...")

    for attempt in range(24):   # 24 × 10s = 4 min
        time.sleep(10)
        s = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code", "access_token": INSTAGRAM_ACCESS_TOKEN},
            timeout=15)
        if s.status_code == 200:
            code = s.json().get("status_code", "")
            logger.info(f"  [{attempt+1}/24] {code}")
            if code == "FINISHED":
                logger.info("✅ Video ready!")
                break
            if code in ("ERROR", "EXPIRED"):
                raise ValueError(f"Reel container error: {s.json()}")
    else:
        raise ValueError("Reel processing timed out (4 min)")

    r2 = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN},
        timeout=30)
    if r2.status_code != 200:
        raise ValueError(f"Reel publish failed: {r2.text}")

    post_id = r2.json()["id"]
    logger.info(f"🎬 REEL POSTED! ID: {post_id}")
    return post_id


def post_to_instagram(media_path: str, is_video: bool) -> str:
    """
    Smart router:
    - is_video=False → post as PHOTO (image_url)
    - is_video=True  → post as REEL (video_url) — no conversion, post directly
    """
    if is_video:
        return post_as_reel(media_path)
    else:
        return post_as_photo(media_path)


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
            media_url, is_vid_pin = get_pinterest_media(pin_url)
            media_path, is_vid    = download_media(media_url)
            is_vid = is_vid or is_vid_pin  # video if URL is video OR pin is video
            post_id            = post_to_instagram(media_path, is_vid)

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










