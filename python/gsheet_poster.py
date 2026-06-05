"""
gsheet_poster.py - Pinterest to Instagram via Google Sheets Queue
v4: FIXED - Skip invalid /sent/ invite URLs + proxy-based scraping for GitHub Actions IPs
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

CAPTION = """🔥 Men's Fashion Inspiration

Upgrade your wardrobe with timeless style and confidence.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #mensstyle #outfitideas #fashion #style #menswear #streetwear #casualstyle #outfitinspiration #styleformen #fashionreels #indianmensfashion #dailyoutfit #styleinspo #fashiontips"""


# ── Google Sheet ──────────────────────────────────────────────────────
def get_sheet_rows():
    for method, url in [
        ("CSV",  f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"),
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


# ── Pinterest: Validate URL is a real pin ─────────────────────────────
def is_valid_pin_url(url: str) -> bool:
    """
    Reject Pinterest invite/sent/gift links — they have no image.
    These look like: pinterest.com/pin/123/sent/?invite_code=...
    """
    invalid_patterns = ["/sent/", "/invite/", "/gift/", "invite_code=", "sfo=1"]
    for p in invalid_patterns:
        if p in url:
            logger.warning(f"⚠️  Skipping invalid invite/sent URL: {url[:80]}")
            return False
    return True


# ── Pinterest: Resolve shortlink ──────────────────────────────────────
def resolve_pin_url(pin_url: str) -> str:
    """Resolve pin.it shortlinks to full pinterest.com/pin/ID URLs"""
    if "pin.it" not in pin_url:
        return pin_url

    logger.info(f"Resolving: {pin_url}")
    for method in ["HEAD", "GET"]:
        try:
            fn = requests.head if method == "HEAD" else requests.get
            r = fn(pin_url, timeout=15, headers=get_headers(), allow_redirects=True)
            final = r.url
            logger.info(f"Resolved ({method}) → {final}")
            if "pinterest" in final:
                return final
        except Exception as e:
            logger.warning(f"Resolve {method}: {e}")

    return pin_url


# ── Pinterest: Fetch HTML via multiple methods ────────────────────────
def fetch_pinterest_html(url: str) -> str:
    """
    Fetch Pinterest page HTML using multiple approaches.
    GitHub Actions IPs are blocked by Pinterest directly,
    so we use proxy services as fallback.
    """
    # Method A: Direct request (works if not blocked)
    try:
        r = requests.get(url, timeout=20, headers=get_headers("https://www.google.com/"), allow_redirects=True)
        if r.status_code == 200 and "pinimg.com" in r.text:
            logger.info("✅ Direct fetch worked")
            return r.text
        logger.warning(f"Direct fetch: {r.status_code}, no pinimg in body")
    except Exception as e:
        logger.warning(f"Direct fetch: {e}")

    # Method B: allorigins.win proxy
    try:
        proxy_url = f"https://api.allorigins.win/get?url={urllib.parse.quote(url)}"
        r = requests.get(proxy_url, timeout=25, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200:
            data = r.json()
            html = data.get("contents", "")
            if html and "pinimg.com" in html:
                logger.info("✅ allorigins proxy worked")
                return html
            logger.warning(f"allorigins: got {len(html)} chars, no pinimg")
    except Exception as e:
        logger.warning(f"allorigins: {e}")

    # Method C: corsproxy.io
    try:
        proxy_url = f"https://corsproxy.io/?{urllib.parse.quote(url)}"
        r = requests.get(proxy_url, timeout=25, headers=get_headers())
        if r.status_code == 200 and "pinimg.com" in r.text:
            logger.info("✅ corsproxy.io worked")
            return r.text
    except Exception as e:
        logger.warning(f"corsproxy: {e}")

    # Method D: htmlpreview / thingproxy
    try:
        proxy_url = f"https://thingproxy.freeboard.io/fetch/{url}"
        r = requests.get(proxy_url, timeout=25, headers={"User-Agent": USER_AGENTS[0]})
        if r.status_code == 200 and "pinimg.com" in r.text:
            logger.info("✅ thingproxy worked")
            return r.text
    except Exception as e:
        logger.warning(f"thingproxy: {e}")

    return ""


# ── Pinterest: Extract image from HTML ────────────────────────────────
def extract_image_from_html(html: str) -> str:
    if not html:
        return None

    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'"contentUrl"\s*:\s*"(https://i\.pinimg\.com/originals/[^"]+)"',
        r'"url"\s*:\s*"(https://i\.pinimg\.com/originals/[^"]+)"',
        r'(https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp))',
        r'(https://i\.pinimg\.com/736x/[a-f0-9/]+\.(?:jpg|jpeg|png|webp))',
        r'(https://i\.pinimg\.com/474x/[a-f0-9/]+\.(?:jpg|jpeg|png|webp))',
        r'(https://i\.pinimg\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp))',
    ]

    for pat in patterns:
        m = re.search(pat, html, re.I)
        if m:
            img = m.group(1).replace("&amp;", "&")
            if "pinimg.com" in img:
                img = re.sub(r'/\d+x\d*/', '/originals/', img)
                logger.info(f"✅ Extracted: {img[:80]}")
                return img

    # JSON-LD
    for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', html, re.I):
        try:
            data = json.loads(block)
            imgs = data.get("image", [])
            if isinstance(imgs, str): imgs = [imgs]
            for img in (imgs if isinstance(imgs, list) else []):
                if "pinimg.com" in str(img):
                    img = re.sub(r'/\d+x\d*/', '/originals/', str(img))
                    logger.info(f"✅ JSON-LD: {img[:80]}")
                    return img
        except Exception:
            pass

    return None


# ── Pinterest: Main image extraction ─────────────────────────────────
def get_pinterest_image(pin_url: str) -> str:
    """Full extraction pipeline with all fallbacks"""

    # Step 0: Resolve shortlink
    resolved = resolve_pin_url(pin_url)
    logger.info(f"Working URL: {resolved}")

    # Step 1: Validate — skip invite/sent links
    if not is_valid_pin_url(resolved):
        raise ValueError(f"SKIP: This is a Pinterest invite/sent link, not a pin with an image: {resolved}")

    # Extract pin ID for API methods
    pin_id_match = re.search(r'/pin/(\d+)', resolved)
    pin_id = pin_id_match.group(1) if pin_id_match else None
    logger.info(f"Pin ID: {pin_id}")

    # Step 2: oEmbed (try both resolved and original)
    for try_url in list(dict.fromkeys([resolved, pin_url])):
        try:
            r = requests.get(
                f"https://www.pinterest.com/oembed.json?url={urllib.parse.quote(try_url)}",
                timeout=12, headers=get_headers("https://www.pinterest.com/"))
            if r.status_code == 200:
                img = r.json().get("thumbnail_url", "")
                for low, high in [("236x","originals"), ("474x","originals"), ("736x","originals")]:
                    img = img.replace(low, high)
                if img and "pinimg.com" in img:
                    logger.info(f"✅ oEmbed: {img[:80]}")
                    return img
                logger.warning(f"oEmbed OK but no image: {r.text[:100]}")
            else:
                logger.warning(f"oEmbed {r.status_code}: {r.text[:80]}")
        except Exception as e:
            logger.warning(f"oEmbed: {e}")

    # Step 3: Pinterest API v3 (uses pin ID)
    if pin_id:
        try:
            api_url = (f"https://www.pinterest.com/resource/PinResource/get/"
                       f"?source_url=/pin/{pin_id}/&data=%7B%22options%22%3A%7B%22id%22%3A%22{pin_id}%22%7D%7D")
            r = requests.get(api_url, timeout=12, headers={
                **get_headers("https://www.pinterest.com/"),
                "X-Requested-With": "XMLHttpRequest",
                "X-App-Version": "https://www.pinterest.com",
            })
            if r.status_code == 200:
                data = r.json()
                img = (data.get("resource_response", {})
                           .get("data", {})
                           .get("images", {})
                           .get("orig", {})
                           .get("url", ""))
                if not img:
                    # search the full response for any pinimg URL
                    raw = json.dumps(data)
                    m = re.search(r'https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|jpeg|png|webp)', raw)
                    if m: img = m.group(0)
                if img and "pinimg.com" in img:
                    logger.info(f"✅ API v3: {img[:80]}")
                    return img
        except Exception as e:
            logger.warning(f"API v3: {e}")

    # Step 4: Fetch HTML via direct + proxies, then extract
    html = fetch_pinterest_html(resolved)
    img = extract_image_from_html(html)
    if img:
        return img

    # Step 5: Wayback Machine (archive.org has cached Pinterest pages)
    if pin_id:
        try:
            wb_url = f"https://web.archive.org/web/2024*/https://www.pinterest.com/pin/{pin_id}/"
            r = requests.get(wb_url, timeout=15, headers={"User-Agent": USER_AGENTS[0]})
            # Find a snapshot URL
            snap = re.search(r'href="(/web/\d+/https://www\.pinterest\.com/pin/' + pin_id + r'/)"', r.text)
            if snap:
                snap_url = f"https://web.archive.org{snap.group(1)}"
                logger.info(f"Trying Wayback: {snap_url}")
                r2 = requests.get(snap_url, timeout=20, headers=get_headers())
                img = extract_image_from_html(r2.text)
                if img:
                    logger.info(f"✅ Wayback Machine: {img[:80]}")
                    return img
        except Exception as e:
            logger.warning(f"Wayback: {e}")

    logger.error(f"❌ All methods failed for: {pin_url} (resolved: {resolved})")
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

    urls_to_try = [image_url]
    if "originals" in image_url:
        urls_to_try.append(image_url.replace("originals", "736x"))
        urls_to_try.append(image_url.replace("originals", "474x"))

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
                        logger.info(f"✅ Downloaded {size} bytes")
                        return path
                    logger.warning(f"Too small: {size}b")
                else:
                    logger.warning(f"HTTP {r.status_code} for {url[:60]}")
            except Exception as e:
                logger.warning(f"Download attempt {attempt+1}: {e}")
            time.sleep(1)

    raise ValueError(f"Could not download image: {image_url}")


# ── Upload to CDN ─────────────────────────────────────────────────────
def upload_to_cdn(image_path: str) -> str:
    # Option 1: catbox.moe
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

    # Option 2: litterbox
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

    # Option 3: GitHub raw (always works)
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
    logger.info(f"Posting to IG: {INSTAGRAM_ACCOUNT_ID}")
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
        send_telegram("⚠️ <b>Queue Empty!</b>\n\nAdd Pinterest URLs with Status=PENDING to Google Sheet")
        return

    # Try each pending URL — skip bad ones, post first good one
    posted = False
    skipped = []

    for pin_url in pending:
        logger.info(f"📌 Processing: {pin_url}")
        try:
            image_url = get_pinterest_image(pin_url)
            if not image_url:
                raise ValueError(f"Could not extract image URL from: {pin_url}")

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
                f"📊 {len(pending)-len(skipped)-1} URLs remaining")
            posted = True
            break  # Success — stop after 1 post per run

        except ValueError as e:
            err = str(e)
            if "SKIP:" in err:
                # Invalid invite URL — skip silently, try next
                logger.warning(f"Skipping: {err}")
                skipped.append(pin_url)
                continue
            else:
                logger.error(f"❌ FAILED: {err}")
                send_telegram(
                    f"❌ <b>Post Failed!</b>\n\n"
                    f"🔗 {pin_url[:60]}\n"
                    f"⚠️ {err[:300]}\n\n"
                    f"Will retry next run.")
                break

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            send_telegram(
                f"❌ <b>Post Failed!</b>\n\n"
                f"🔗 {pin_url[:60]}\n"
                f"⚠️ {str(e)[:300]}")
            break

    if skipped and not posted:
        logger.warning(f"All {len(skipped)} URLs were invalid invite links!")
        send_telegram(
            f"⚠️ <b>All URLs are invalid invite links!</b>\n\n"
            f"These Pinterest URLs are invite/sent links, not pins:\n"
            + "\n".join(f"• {u}" for u in skipped[:5])
            + "\n\n<b>Please replace them with real Pinterest pin URLs!</b>\n"
            f"Format: https://pinterest.com/pin/123456789/")


if __name__ == "__main__":
    main()
