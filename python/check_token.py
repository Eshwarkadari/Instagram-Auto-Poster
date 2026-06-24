import requests, os, base64, time

INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID = os.environ["INSTAGRAM_ACCOUNT_ID"]

# Check token validity and rate limit headers
r = requests.get(
    f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}",
    params={"fields": "id,username", "access_token": INSTAGRAM_ACCESS_TOKEN},
    timeout=15
)
result = "TOKEN CHECK STATUS=" + str(r.status_code) + "\n"
result += "BODY=" + r.text[:500] + "\n\n"

# Check rate limit headers if present
result += "HEADERS:\n"
for k, v in r.headers.items():
    if "rate" in k.lower() or "usage" in k.lower() or "limit" in k.lower():
        result += f"  {k}: {v}\n"

# Check app-level usage
r2 = requests.get(
    f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
    params={"fields": "id", "limit": 1, "access_token": INSTAGRAM_ACCESS_TOKEN},
    timeout=15
)
result += "\nMEDIA LIST CHECK STATUS=" + str(r2.status_code) + "\n"
result += "BODY=" + r2.text[:500] + "\n"
result += "\nHEADERS:\n"
for k, v in r2.headers.items():
    if "rate" in k.lower() or "usage" in k.lower() or "limit" in k.lower():
        result += f"  {k}: {v}\n"

print(result)

token = os.environ.get("DEBUG_GH_TOKEN", "")
repo = os.environ.get("GITHUB_REPO", "")
b64 = base64.b64encode(result.encode()).decode()
sha = None
rr = requests.get("https://api.github.com/repos/" + repo + "/contents/full_run_log.txt",
                  headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"})
if rr.status_code == 200:
    sha = rr.json().get("sha")
payload = {"message": "token check " + str(int(time.time())), "content": b64}
if sha:
    payload["sha"] = sha
rr2 = requests.put("https://api.github.com/repos/" + repo + "/contents/full_run_log.txt",
                   headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"},
                   json=payload)
print("Push status:", rr2.status_code)
