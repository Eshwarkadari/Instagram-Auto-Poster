"""
poster.py
Main Pinterest to Instagram auto poster
Uses AI Vision to generate men's fashion captions
Author: Kadari Eshwar
"""

import os
import requests
import base64
import time
import re
import random
import logging
import hashlib

from caption_generator import generate

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Credentials from GitHub Actions secrets
INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ["INSTAGRAM_ACCOUNT_ID"]
GITHUB_TOKEN           = os.environ["GITHUB_TOKEN"]
GITHUB_REPO            = os.environ["GITHUB_REPO"]
OPENAI_API_KEY         = os.environ.get("OPENAI_API_KEY", "")

HEADERS_GH = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

PINTEREST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}


# ──────────────────────────────────────────────
# GitHub helpers
# ──────────────────────────────────────────────

def get_file(path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    r = requests.get(url, headers=HEADERS_GH)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def update_file(path, content, sha, message):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    r = requests.put(url, headers=HEADERS_GH, json={
        "message": message, "content": encoded, "sha": sha
    })
    r.raise_for_status()
    logger.info(f"✅ Updated {path}")


# ──────────────────────────────────────────────
# Pinterest helpers
# ──────────────────────────────────────────────

def get_pinterest_image(pin_url: str) -> str:
    """Extract highest-quality image URL from a Pinterest pin"""
    # 1. Try oEmbed
    try:
        oe = requests.get(
            f"https://www.pinterest.com/oembed.json?url={pin_url}",
            timeout=10, headers=PINTEREST_HEADERS
        )
        if oe.status_code == 200:
            img = oe.json().get("thumbnail_url", "")
            for low, high in [("236x","originals"),("474x","originals"),("736x","originals")]:
                img = img.replace(low, high)
            if img:
                logger.info(f"  oEmbed image: {img[:60]}...")
                return img
    except Exception as e:
        logger.warning(f"  oEmbed failed: {e}")

    # 2. Scrape page
    try:
        r = requests.get(pin_url, timeout=15, headers=PINTEREST_HEADERS, allow_redirects=True)
        for pattern in [
            r'"contentUrl":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'(https://i\.pinimg\.com/originals/[^\s"\']+\.(?:jpg|jpeg|png|webp))',
            r'(https://i\.pinimg\.com/736x/[^\s"\']+\.(?:jpg|jpeg|png|webp))',
        ]:
            m = re.search(pattern, r.text)
            if m:
                logger.info(f"  Scraped image: {m.group(1)[:60]}...")
                return m.group(1)
    except Exception as e:
        logger.warning(f"  Scrape failed: {e}")

    return None


def download_image(image_url: str, save_path: str) -> bytes:
    """Download image bytes and save locally"""
    r = requests.get(image_url, timeout=30, headers=PINTEREST_HEADERS, stream=True)
    r.raise_for_status()
    content = r.content
    with open(save_path, "wb") as f:
        f.write(content)
    logger.info(f"  Downloaded: {len(content)} bytes → {save_path}")
    return content


def upload_to_public_host(image_path: str) -> str:
    """Upload image to catbox.moe and return public URL"""
    with open(image_path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            files={"fileToUpload": ("image.jpg", f, "image/jpeg")},
            data={"reqtype": "fileupload", "userhash": ""},
            timeout=30
        )
    if r.status_code == 200 and r.text.startswith("https://"):
        url = r.text.strip()
        logger.info(f"  Uploaded → {url}")
        return url
    raise ValueError(f"Upload failed: {r.text[:100]}")


# ──────────────────────────────────────────────
# Instagram helpers
# ──────────────────────────────────────────────

def create_instagram_container(image_url: str, caption: str) -> str:
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
    )
    if r.status_code != 200:
        logger.error(f"  Container error: {r.text}")
    r.raise_for_status()
    return r.json()["id"]


def publish_instagram(container_id: str) -> str:
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
    )
    r.raise_for_status()
    return r.json()["id"]


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    logger.info("🚀 Starting Instagram Auto Poster...")

    # Read links.txt from GitHub
    links_content, links_sha = get_file("links.txt")
    links = [
        l.strip() for l in links_content.split("\n")
        if l.strip() and not l.strip().startswith("#") and "pin" in l.lower()
    ]

    if not links:
        logger.warning("❌ No Pinterest links found in links.txt!")
        return

    logger.info(f"📋 Found {len(links)} links. Processing first 3...")

    # Read posted.txt
    try:
        posted_content, posted_sha = get_file("posted.txt")
    except Exception:
        posted_content, posted_sha = "", None

    posted_hashes = set(posted_content.strip().splitlines())
    to_post    = links[:3]
    remaining  = links[3:]
    posted_this_run = []

    os.makedirs("/tmp/images", exist_ok=True)

    for pin_url in to_post:
        logger.info(f"\n📌 Processing: {pin_url}")
        try:
            # 1. Extract image URL
            image_url = get_pinterest_image(pin_url)
            if not image_url:
                logger.warning("  ⚠️ Could not extract image, skipping")
                remaining.insert(0, pin_url)
                continue

            # 2. Download image
            save_path = f"/tmp/images/{hashlib.md5(pin_url.encode()).hexdigest()}.jpg"
            download_image(image_url, save_path)

            # 3. Duplicate detection via image hash
            with open(save_path, "rb") as f:
                img_hash = hashlib.sha256(f.read()).hexdigest()[:16]
            if img_hash in posted_hashes:
                logger.warning(f"  ⚠️ Duplicate image detected ({img_hash}), skipping")
                continue

            # 4. Upload to public host
            logger.info("  📤 Uploading to public host...")
            public_url = upload_to_public_host(save_path)

            # 5. Generate AI caption using OpenAI Vision
            logger.info("  🤖 Generating AI caption...")
            caption = generate(
                image_path=save_path if OPENAI_API_KEY else None,
                image_url=public_url if OPENAI_API_KEY else None
            )
            logger.info(f"  📝 Caption: {caption[:80]}...")

            # 6. Create Instagram container
            logger.info("  📲 Creating Instagram container...")
            container_id = create_instagram_container(public_url, caption)
            logger.info(f"  ✅ Container: {container_id}")

            # 7. Wait for processing
            logger.info("  ⏳ Waiting 15s for Instagram to process...")
            time.sleep(15)

            # 8. Publish
            logger.info("  🚀 Publishing to Instagram...")
            post_id = publish_instagram(container_id)
            logger.info(f"  ✅ Published! Post ID: {post_id}")

            posted_this_run.append(pin_url)
            posted_hashes.add(img_hash)
            time.sleep(5)

        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            remaining.insert(0, pin_url)

    # Update links.txt — remove posted links
    new_links = "# Add Pinterest links below (one per line)\n\n" + "\n".join(remaining) + "\n"
    update_file("links.txt", new_links, links_sha, f"Auto: removed {len(posted_this_run)} posted links")

    # Update posted.txt — add new hashes
    if posted_this_run:
        new_posted = "\n".join(sorted(posted_hashes)) + "\n"
        if posted_sha:
            update_file("posted.txt", new_posted, posted_sha, f"Auto: added {len(posted_this_run)} posted entries")
        else:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt"
            requests.put(url, headers=HEADERS_GH, json={
                "message": "Auto: created posted.txt",
                "content": base64.b64encode(new_posted.encode()).decode()
            })
            logger.info("✅ Created posted.txt")

    logger.info(f"\n🎉 Done! Posted {len(posted_this_run)}/3 images to Instagram.")


if __name__ == "__main__":
    main()
