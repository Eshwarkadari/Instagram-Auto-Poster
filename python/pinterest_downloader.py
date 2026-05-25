"""
pinterest_downloader.py
Downloads image or video from a Pinterest URL
Author: Kadari Eshwar
"""

import requests, re, os, json
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_pinterest_media(url: str, save_dir: str = "downloads") -> dict:
    """
    Download image or video from a Pinterest pin URL.
    Returns: { "path": "...", "type": "image/video", "title": "..." }
    """
    os.makedirs(save_dir, exist_ok=True)

    # Resolve short URLs (pin.it/xxx)
    if "pin.it" in url:
        r = requests.get(url, headers=HEADERS, allow_redirects=True)
        url = r.url

    # Fetch pin page
    r = requests.get(url, headers=HEADERS)
    html = r.text

    # Extract JSON data embedded in page
    result = {"url": url, "type": "image", "path": None, "title": ""}

    # Try video first
    video_match = re.search(r'"url"\s*:\s*"(https://v\.pinimg\.com/[^"]+\.mp4[^"]*)"', html)
    if video_match:
        media_url = video_match.group(1).replace("\u0026", "&")
        result["type"] = "video"
    else:
        # Try high-res image
        img_match = re.search(r'"orig"\s*:\s*\{[^}]*"url"\s*:\s*"([^"]+)"', html)
        if not img_match:
            img_match = re.search(r'"736x"\s*:\s*\{[^}]*"url"\s*:\s*"([^"]+)"', html)
        if img_match:
            media_url = img_match.group(1).replace("\u0026", "&")
        else:
            # Fallback: og:image
            og_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            if og_match:
                media_url = og_match.group(1)
            else:
                print(f"❌ Could not find media in: {url}")
                return result

    # Extract title
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    if title_match:
        result["title"] = title_match.group(1)

    # Download
    ext  = ".mp4" if result["type"] == "video" else ".jpg"
    pin_id = re.search(r"/pin/(\d+)", url)
    fname  = f"{pin_id.group(1) if pin_id else 'pin'}{ext}"
    fpath  = os.path.join(save_dir, fname)

    media_r = requests.get(media_url, headers=HEADERS, stream=True)
    with open(fpath, "wb") as f:
        for chunk in media_r.iter_content(8192):
            f.write(chunk)

    result["path"] = fpath
    size_kb = os.path.getsize(fpath) // 1024
    print(f"✅ Downloaded {result['type']}: {fname} ({size_kb}KB)")
    return result


if __name__ == "__main__":
    # Test
    url = input("Enter Pinterest URL: ").strip()
    result = get_pinterest_media(url)
    print(json.dumps(result, indent=2))
