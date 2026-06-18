import requests, json, urllib.parse, os, base64, time, re

pin_ids = ["872361390330023115", "1127940669175905650"]

output_lines = []
def log(msg):
    print(msg)
    output_lines.append(str(msg))

for pin_id in pin_ids:
    log("")
    log("=== embed.html for pin_id: " + pin_id + " ===")
    embed_url = "https://assets.pinterest.com/ext/embed.html?id=" + pin_id + "&src=oembed"
    try:
        r = requests.get(embed_url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
            "Accept": "text/html",
            "Referer": "https://www.pinterest.com/",
        })
        log("HTTP: " + str(r.status_code) + " | len=" + str(len(r.text)))
        if r.status_code == 200:
            html = r.text
            log("has <video: " + str("<video" in html.lower()))
            log("has video_url: " + str("video_url" in html))
            log("has .mp4: " + str(".mp4" in html))
            log("has v.pinimg: " + str("v.pinimg" in html))
            log("has og:video: " + str("og:video" in html))
            log("has play button class: " + str("playButton" in html or "PlayButton" in html or "play-button" in html))
            log("has isVideo: " + str("isVideo" in html or "is_video" in html))
            # Find script tags
            scripts = re.findall(r'<script[^>]*>([\s\S]{0,200})', html)
            log("script count: " + str(len(scripts)))
            log("HTML preview (first 800): " + html[:800].replace("\n"," "))
        else:
            log("Body: " + r.text[:200])
    except Exception as e:
        log("ERROR: " + str(e))

result_text = "\n".join(output_lines)

GH_TOKEN = os.environ.get("DEBUG_GH_TOKEN", "")
REPO = os.environ.get("GITHUB_REPO", "Eshwarkadari/Instagram-Auto-Poster")

b64content = base64.b64encode(result_text.encode("utf-8")).decode("utf-8")
sha = None
r = requests.get(
    "https://api.github.com/repos/" + REPO + "/contents/oembed_debug_output.txt",
    headers={"Authorization": "Bearer " + GH_TOKEN, "Accept": "application/vnd.github+json"},
    timeout=15)
if r.status_code == 200:
    sha = r.json().get("sha")
payload = {"message": "debug: embed.html output " + str(int(time.time())), "content": b64content}
if sha:
    payload["sha"] = sha
r2 = requests.put(
    "https://api.github.com/repos/" + REPO + "/contents/oembed_debug_output.txt",
    headers={"Authorization": "Bearer " + GH_TOKEN, "Accept": "application/vnd.github+json"},
    json=payload, timeout=30)
print("PUSH_STATUS:", r2.status_code)
