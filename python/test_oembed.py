import requests, json, urllib.parse, sys

pin_urls = [
    "https://www.pinterest.com/pin/872361390330023115/",
    "https://www.pinterest.com/pin/1127940669175905650/",
]

output_lines = []
def log(msg):
    print(msg)
    output_lines.append(msg)

for pin_url in pin_urls:
    log(f"\n=== Testing: {pin_url} ===")
    for ua in [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "facebookexternalhit/1.1",
    ]:
        try:
            r = requests.get(
                "https://www.pinterest.com/oembed.json?url=" + urllib.parse.quote(pin_url),
                timeout=15,
                headers={"User-Agent": ua, "Accept": "application/json"})
            log(f"  UA={ua[:30]} HTTP={r.status_code}")
            if r.status_code == 200:
                d = r.json()
                log(f"  type: {d.get('type')}")
                log(f"  thumbnail_url: {d.get('thumbnail_url','')}")
                log(f"  html: {d.get('html','')}")
                log(f"  ALL FIELDS JSON: {json.dumps(d)}")
        except Exception as e:
            log(f"  ERROR: {e}")

# Write output to a file in repo so we can read it via Contents API
with open("oembed_debug_output.txt", "w") as f:
    f.write("\n".join(output_lines))
