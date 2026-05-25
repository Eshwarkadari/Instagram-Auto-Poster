"""
instagram_poster.py
Posts images/videos to Instagram via Facebook Graph API
Author: Kadari Eshwar | B.Tech ECE, JNTU Hyderabad
"""

import requests
import os
import time

# ── Config (set these as environment variables) ────────────────────────────
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "YOUR_INSTAGRAM_ACCOUNT_ID")
ACCESS_TOKEN         = os.getenv("FACEBOOK_ACCESS_TOKEN",  "YOUR_ACCESS_TOKEN")
API_VERSION          = "v18.0"
BASE_URL             = f"https://graph.facebook.com/{API_VERSION}"

def upload_image_container(image_url, caption):
    """Step 1: Create a media container for image post."""
    url    = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "image_url":    image_url,
        "caption":      caption,
        "access_token": ACCESS_TOKEN,
    }
    resp = requests.post(url, params=params)
    data = resp.json()
    if "id" in data:
        print(f"✅ Image container created: {data['id']}")
        return data["id"]
    print(f"❌ Container error: {data}")
    return None

def upload_video_container(video_url, caption):
    """Step 1: Create a media container for video/reel post."""
    url    = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "video_url":    video_url,
        "caption":      caption,
        "media_type":   "REELS",
        "access_token": ACCESS_TOKEN,
    }
    resp = requests.post(url, params=params)
    data = resp.json()
    if "id" in data:
        print(f"✅ Video container created: {data['id']}")
        return data["id"]
    print(f"❌ Container error: {data}")
    return None

def check_container_status(container_id):
    """Check if media container is ready to publish."""
    url    = f"{BASE_URL}/{container_id}"
    params = {"fields": "status_code", "access_token": ACCESS_TOKEN}
    resp   = requests.get(url, params=params)
    data   = resp.json()
    return data.get("status_code", "ERROR")

def publish_container(container_id):
    """Step 2: Publish the media container to Instagram."""
    url    = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    params = {"creation_id": container_id, "access_token": ACCESS_TOKEN}
    resp   = requests.post(url, params=params)
    data   = resp.json()
    if "id" in data:
        print(f"✅ Post published! Post ID: {data['id']}")
        return data["id"]
    print(f"❌ Publish error: {data}")
    return None

def post_image(image_url, caption):
    """Post an image to Instagram."""
    print(f"📸 Posting image...")
    container_id = upload_image_container(image_url, caption)
    if not container_id:
        return None
    # Wait for container to be ready
    for _ in range(10):
        status = check_container_status(container_id)
        if status == "FINISHED":
            break
        print(f"   Waiting... status: {status}")
        time.sleep(3)
    return publish_container(container_id)

def post_video(video_url, caption):
    """Post a video/reel to Instagram."""
    print(f"🎥 Posting video/reel...")
    container_id = upload_video_container(video_url, caption)
    if not container_id:
        return None
    # Videos take longer to process
    print("   Processing video (this takes ~30 seconds)...")
    for _ in range(20):
        status = check_container_status(container_id)
        if status == "FINISHED":
            break
        print(f"   Status: {status}")
        time.sleep(5)
    return publish_container(container_id)

def post_media(media_url, caption, media_type="image"):
    """Auto-detect and post image or video."""
    if media_type == "video":
        return post_video(media_url, caption)
    return post_image(media_url, caption)

if __name__ == "__main__":
    # Test post
    print("=== Instagram Poster Test ===")
    print(f"Account ID: {INSTAGRAM_ACCOUNT_ID}")
    print(f"Token set: {'Yes' if ACCESS_TOKEN != 'YOUR_ACCESS_TOKEN' else 'No - set env vars!'}")
