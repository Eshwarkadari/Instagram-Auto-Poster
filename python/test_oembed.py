import requests, json, urllib.parse, os, base64, time

pin_urls = [
    "https://www.pinterest.com/pin/872361390330023115/",
    "https://www.pinterest.com/pin/1127940669175905650/",
]

output_lines = []
def log(msg):
    print(msg)
    output_lines.append(str(msg))

for pin_url in pin_urls:
    log("")
    log("=== Testing: " + pin_url + " ===")
    for ua in [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "facebookexternalhit/1.1",
    ]:
        try:
            r = requests.get(
                "https://www.pinterest.com/oembed.json?url=" + urllib.parse.quote(pin_url),
                timeout=15,
                headers={"User-Agent": ua, "Accept": "application/json"})
            log("  UA=" + ua[:30] + " HTTP=" + str(r.status_code))
            if r.status_code == 200:
                d = r.json()
                log("  type: " + str(d.get('type')))
                log("  thumbnail_url: " + str(d.get('thumbnail_url','')))
                log("  html: " + str(d.get('html','')))
                log("  ALL FIELDS JSON: " + json.dumps(d))
            else:
                log("  body: " + r.text[:200])
        except Exception as e:
            log("  ERROR: " + str(e))

result_text = "\n".join(output_lines)

# Push directly via GitHub API instead of git commit (more reliable in Actions)
GH_TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPO", "Eshwarkadari/Instagram-Auto-Poster")

if GH_TOKEN:
    b64content = base64.b64encode(result_text.encode("utf-8")).decode("utf-8")
    # Check if file exists to get sha
    sha = None
    try:
        r = requests.get(
            "https://api.github.com/repos/" + REPO + "/contents/oembed_debug_output.txt",
            headers={"Authorization": "Bearer " + GH_TOKEN, "Accept": "application/vnd.github+json"},
            timeout=15)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception as e:
        log("sha check error: " + str(e))

    payload = {"message": "debug: oEmbed output " + str(int(time.time())), "content": b64content}
    if sha:
        payload["sha"] = sha

    r2 = requests.put(
        "https://api.github.com/repos/" + REPO + "/contents/oembed_debug_output.txt",
        headers={"Authorization": "Bearer " + GH_TOKEN, "Accept": "application/vnd.github+json"},
        json=payload, timeout=30)
    print("Push result:", r2.status_code, r2.text[:200])
else:
    print("No GH_TOKEN available")
