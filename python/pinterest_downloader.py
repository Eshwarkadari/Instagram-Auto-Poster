"""
pinterest_downloader.py
Downloads images and videos from Pinterest URLs
Author: Kadari Eshwar | B.Tech ECE, JNTU Hyderabad
"""

import requests
import re
import os
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_pinterest_media(url):
    """
    Extract direct media URL from a Pinterest link.
    Returns: (media_url, media_type) where media_type is 'image' or 'video'
    """
    try:
        # Expand short URLs (pin.it/xxx)
        if "pin.it" in url:
            resp = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
            url  = resp.url

        # Fetch Pinterest page
        resp = requests.get(url, headers=HEADERS, timeout=10)
        html = resp.text

        # Try to find video URL first
        video_match = re.search(r'"contentUrl":"(https://v[^"]+\.mp4[^"]*)"', html)
        if video_match:
            return video_match.group(1), "video"

        # Try high-res image
        img_patterns = [
            r'"contentUrl":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'(https://i\.pinimg\.com/originals/[a-z0-9/]+\.(?:jpg|jpeg|png|webp))',
            r'(https://i\.pinimg\.com/736x/[a-z0-9/]+\.(?:jpg|jpeg|png|webp))',
        ]
        for pattern in img_patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1), "image"

        return None, None

    except Exception as e:
        print(f"Error fetching Pinterest URL: {e}")
        return None, None

def download_media(url, save_path="downloads"):
    """Download media from Pinterest and save locally."""
    os.makedirs(save_path, exist_ok=True)

    media_url, media_type = get_pinterest_media(url)
    if not media_url:
        print(f"❌ Could not extract media from: {url}")
        return None, None

    # Get file extension
    ext = media_url.split(".")[-1].split("?")[0]
    if ext not in ["jpg","jpeg","png","mp4","webp"]:
        ext = "jpg"

    filename = f"{save_path}/media_{hash(url) % 100000}.{ext}"

    resp = requests.get(media_url, headers=HEADERS, stream=True, timeout=30)
    with open(filename, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"✅ Downloaded: {filename} ({media_type})")
    return filename, media_type

if __name__ == "__main__":
    # Test with a Pinterest URL
    test_url = input("Enter Pinterest URL: ")
    filename, mtype = download_media(test_url)
    if filename:
        print(f"Saved as: {filename} | Type: {mtype}")
