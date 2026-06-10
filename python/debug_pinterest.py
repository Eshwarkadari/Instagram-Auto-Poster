import requests, re, urllib.parse, sys

# Test multiple approaches
pin_id = sys.argv[1] if len(sys.argv) > 1 else "872361390330023115"
clean_url = f"https://www.pinterest.com/pin/{pin_id}/"

print(f"Testing pin: {pin_id}")
print(f"Clean URL: {clean_url}")

headers_browser = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

# Test oEmbed
print("\n--- oEmbed ---")
r = requests.get(
    "https://www.pinterest.com/oembed.json?url=" + urllib.parse.quote(clean_url),
    timeout=10, headers=headers_browser)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"Keys: {list(d.keys())}")
    print(f"type: {d.get('type')}")
    print(f"thumbnail_url: {d.get('thumbnail_url', 'NONE')[:100]}")
else:
    print(f"Body: {r.text[:200]}")

# Test direct HTML fetch
print("\n--- Direct HTML ---")
r2 = requests.get(clean_url, timeout=15, headers=headers_browser, allow_redirects=True)
print(f"Status: {r2.status_code} | Length: {len(r2.text)}")
html = r2.text

# Count script tags
scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
print(f"Script tags: {len(scripts)}")

# Check for any data
print(f"Has pinimg: {'pinimg.com' in html}")
print(f"Has og:image: {'og:image' in html}")
print(f"HTML first 500: {html[:500]}")

# Raw search for any image URL
imgs = re.findall(r'https://i\.pinimg\.com/[^\s"\'<>\\]+\.(jpg|jpeg|png|webp)', html.replace('\\/','//'))
print(f"Image URLs found: {imgs[:3]}")

# Test Pinterest's JSON API with proper headers
print("\n--- Pinterest JSON API ---")
api = f"https://www.pinterest.com/resource/PinResource/get/?source_url=/pin/{pin_id}/&data=%7B%22options%22%3A%7B%22id%22%3A%22{pin_id}%22%7D%7D"
headers_api = {
    **headers_browser,
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
r3 = requests.get(api, timeout=10, headers=headers_api)
print(f"Status: {r3.status_code} | Length: {len(r3.text)}")
if r3.status_code == 200:
    imgs2 = re.findall(r'https://i\.pinimg\.com/[^\s"\'<>\\]+\.(jpg|jpeg|png|webp)', r3.text.replace('\\/','//'))
    print(f"Images in API: {imgs2[:3]}")
else:
    print(f"Body: {r3.text[:100]}")
