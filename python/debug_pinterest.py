"""Run this manually: python debug_pinterest.py"""
import requests, re, sys

url = sys.argv[1] if len(sys.argv)>1 else "https://www.pinterest.com/pin/1127940669175905650/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}
r = requests.get(url, timeout=20, headers=headers)
html = r.text
print(f"HTTP {r.status_code} | {len(html)} chars")

# Show all script tags with id
ids = re.findall(r'<script[^>]+id=["\']([^"\']+)["\']', html)
print(f"Script IDs: {ids}")

# Show all script sizes
scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
print(f"Script count: {len(scripts)}")
for i, s in enumerate(scripts):
    if len(s) > 100:
        print(f"  Script {i}: {len(s)} chars | preview: {s[:80].strip()}")

# Raw pinimg search
import html as htmllib
decoded = htmllib.unescape(html).replace("\\/","/")
imgs = re.findall(r'https://i\.pinimg\.com/[^\s"\'<>\\]+\.(jpg|jpeg|png|webp)', decoded)
vids = re.findall(r'https://v\d*\.pinimg\.com/[^\s"\'<>\\]+', decoded)
print(f"Image URLs: {imgs[:5]}")
print(f"Video URLs: {vids[:3]}")
