import requests, json, urllib.parse, sys

# Test with a known video pin
pin_urls = [
    "https://www.pinterest.com/pin/872361390330023115/",  # video pin (from earlier logs)
    "https://www.pinterest.com/pin/1127940669175905650/", # another pin
]

for pin_url in pin_urls:
    print(f"\n=== Testing: {pin_url} ===")
    for ua in [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "facebookexternalhit/1.1",
    ]:
        r = requests.get(
            "https://www.pinterest.com/oembed.json?url=" + urllib.parse.quote(pin_url),
            timeout=15,
            headers={"User-Agent": ua, "Accept": "application/json"})
        print(f"  UA={ua[:30]} HTTP={r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"  type: {d.get('type')}")
            print(f"  thumbnail_url: {d.get('thumbnail_url','')}")
            print(f"  html: {d.get('html','')[:300]}")
            print(f"  ALL FIELDS: {json.dumps(d, indent=2)[:500]}")
            break
