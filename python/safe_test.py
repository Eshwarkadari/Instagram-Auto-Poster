import requests, base64, os, time

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwAmCT_oqhO3XAkkk2ywyXciNBzyZiUk7bJtKpf0VUkAbE96iVK8Xgf9HLD4vV0Eo11/exec"
test_url = "https://pin.it/2F07WgfCW"

r = requests.get(WEBAPP_URL, params={"url": test_url}, timeout=30)
result = "STATUS=" + str(r.status_code) + "\n" + "BODY=" + r.text[:800]
print(result)

token = os.environ.get("DEBUG_GH_TOKEN", "")
repo = os.environ.get("GITHUB_REPO", "")
b64 = base64.b64encode(result.encode()).decode()
sha = None
rr = requests.get("https://api.github.com/repos/" + repo + "/contents/full_run_log.txt",
                  headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"})
if rr.status_code == 200:
    sha = rr.json().get("sha")
payload = {"message": "safe test result " + str(int(time.time())), "content": b64}
if sha:
    payload["sha"] = sha
rr2 = requests.put("https://api.github.com/repos/" + repo + "/contents/full_run_log.txt",
                   headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"},
                   json=payload)
print("Push status:", rr2.status_code)
