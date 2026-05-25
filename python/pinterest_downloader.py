"""
pinterest_downloader.py
Downloads images/videos from Pinterest URLs
Author: Kadari Eshwar
"""
import requests, re, os

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

def get_media_url(pinterest_url):
    """Extract direct media URL from Pinterest page."""
    try:
        # Expand short URLs
        if "pin.it" in pinterest_url:
            r = requests.get(pinterest_url, headers=HEADERS, allow_redirects=True, timeout=10)
            pinterest_url = r.url

        r    = requests.get(pinterest_url, headers=HEADERS, timeout=10)
        html = r.text

        # Check for video first
        vm = re.search(r'"contentUrl":"(https://v[^"]+\.mp4[^"]*)"', html)
        if vm:
            return vm.group(1), "video"

        # Try images in order of quality
        for pat in [
            r'"contentUrl":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'(https://i\.pinimg\.com/originals/[^"\s]+\.(?:jpg|jpeg|png))',
            r'(https://i\.pinimg\.com/736x/[^"\s]+\.(?:jpg|jpeg|png))',
        ]:
            m = re.search(pat, html)
            if m:
                return m.group(1), "image"

        return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def download(url, folder="downloads"):
    """Download media from Pinterest URL."""
    os.makedirs(folder, exist_ok=True)
    media_url, media_type = get_media_url(url)
    if not media_url:
        return None, None

    ext  = media_url.split(".")[-1].split("?")[0]
    ext  = ext if ext in ["jpg","jpeg","png","mp4","webp"] else "jpg"
    path = f"{folder}/media_{abs(hash(url)) % 99999}.{ext}"

    r = requests.get(media_url, headers=HEADERS, stream=True, timeout=30)
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

    print(f"✅ Downloaded: {path} ({media_type})")
    return path, media_type
