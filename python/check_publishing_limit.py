import requests, base64, os, time

INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID = os.environ["INSTAGRAM_ACCOUNT_ID"]

# Official endpoint to check exact publishing quota usage
r = requests.get(
    f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/content_publishing_limit",
    params={"fields": "config,quota_usage", "access_token": INSTAGRAM_ACCESS_TOKEN},
    timeout=15
)
result = "CONTENT_PUBLISHING_LIMIT STATUS=" + str(r.status_code) + "\n"
result += "BODY=" + r.text + "\n"
print(result)

token = os.environ.get("DEBUG_GH_TOKEN", "")
repo = os.environ.get("GITHUB_REPO", "")
b64 = base64.b64encode(result.encode()).decode()
sha = None
rr = requests.get("https://api.github.com/repos/" + repo + "/contents/full_run_log.txt",
                  headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"})
if rr.status_code == 200:
    sha = rr.json().get("sha")
payload = {"message": "publishing limit check " + str(int(time.time())), "content": b64}
if sha:
    payload["sha"] = sha
rr2 = requests.put("https://api.github.com/repos/" + repo + "/contents/full_run_log.txt",
                   headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"},
                   json=payload)
print("Push status:", rr2.status_code)
