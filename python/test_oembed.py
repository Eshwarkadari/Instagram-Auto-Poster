import requests, json, urllib.parse, os, base64, time

pin_ids = ["872361390330023115", "1127940669175905650"]

output_lines = []
def log(msg):
    print(msg)
    output_lines.append(str(msg))

for pin_id in pin_ids:
    log("")
    log("=== PinResource API for pin_id: " + pin_id + " ===")
    try:
        api_url = (
            "https://www.pinterest.com/resource/PinResource/get/"
            "?source_url=/pin/" + pin_id + "/"
            "&data=%7B%22options%22%3A%7B%22id%22%3A%22" + pin_id + "%22%2C%22field_set_key%22%3A%22detailed%22%7D%7D"
        )
        r = requests.get(api_url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.pinterest.com/",
        })
        log("HTTP: " + str(r.status_code) + " | len=" + str(len(r.text)))
        if r.status_code == 200:
            data = r.json()
            # Navigate to the pin data
            resource_response = data.get("resource_response", {})
            pin_data = resource_response.get("data", {})
            log("Pin data keys: " + str(list(pin_data.keys())[:30]))
            log("is_video: " + str(pin_data.get("is_video")))
            log("videos present: " + str("videos" in pin_data))
            if "videos" in pin_data:
                log("videos value: " + json.dumps(pin_data["videos"])[:300])
            log("media: " + json.dumps(pin_data.get("media", {}))[:200])
            log("type field: " + str(pin_data.get("type")))
        else:
            log("Body: " + r.text[:200])
    except Exception as e:
        log("ERROR: " + str(e))

result_text = "\n".join(output_lines)
print("RESULT LENGTH:", len(result_text))

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

payload = {"message": "debug: PinResource output " + str(int(time.time())), "content": b64content}
if sha:
    payload["sha"] = sha

r2 = requests.put(
    "https://api.github.com/repos/" + REPO + "/contents/oembed_debug_output.txt",
    headers={"Authorization": "Bearer " + GH_TOKEN, "Accept": "application/vnd.github+json"},
    json=payload, timeout=30)
print("PUSH_STATUS:", r2.status_code)
