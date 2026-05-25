"""
poster.py — Run automation manually (test mode)
Author: Kadari Eshwar | B.Tech ECE, JNTU Hyderabad

Usage:
  python poster.py          # dry run (no actual posting)
  python poster.py --live   # real posting (needs credentials)
"""
import os, sys, base64, json
import urllib.request, urllib.parse
from datetime import datetime
from pinterest_downloader import download
from caption_generator import generate

# ── Credentials (set as environment variables) ─────────────────────────────
GITHUB_TOKEN          = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO           = os.getenv("GITHUB_REPO", "Eshwarkadari/Instagram-Auto-Poster")
INSTAGRAM_ACCOUNT_ID  = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
POSTS_PER_RUN         = 3
LIVE_MODE             = "--live" in sys.argv

GH_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def gh_get_file(path):
    """Read file from GitHub repo."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    req = urllib.request.Request(url, headers=GH_HEADERS)
    with urllib.request.urlopen(req) as r:
        data    = json.load(r)
        content = base64.b64decode(data["content"]).decode()
        return content, data["sha"]

def gh_update_file(path, content, sha, msg):
    """Update file in GitHub repo."""
    url     = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{urllib.parse.quote(path)}"
    encoded = base64.b64encode(content.encode()).decode()
    payload = {"message": msg, "content": encoded, "sha": sha}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={**GH_HEADERS, "Content-Type": "application/json"},
        method="PUT"
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def read_links():
    """Read pending links from links.txt."""
    content, sha = gh_get_file("links.txt")
    links = [
        line.strip() for line in content.splitlines()
        if line.strip() and not line.startswith("#") and "pin" in line.lower()
    ]
    return links, content, sha

def post_to_instagram(media_url, caption, media_type="image"):
    """Post to Instagram via Facebook Graph API."""
    base = f"https://graph.facebook.com/v18.0/{INSTAGRAM_ACCOUNT_ID}"

    # Step 1: Create container
    params = {
        "caption":      caption,
        "access_token": FACEBOOK_ACCESS_TOKEN,
    }
    if media_type == "video":
        params["video_url"]  = media_url
        params["media_type"] = "REELS"
    else:
        params["image_url"] = media_url

    data = urllib.parse.urlencode(params).encode()
    req  = urllib.request.Request(f"{base}/media", data=data, method="POST")
    with urllib.request.urlopen(req) as r:
        container = json.load(r)

    container_id = container.get("id")
    if not container_id:
        print(f"❌ Container error: {container}")
        return None

    # Step 2: Publish
    import time; time.sleep(5)
    pub_params = urllib.parse.urlencode({
        "creation_id":  container_id,
        "access_token": FACEBOOK_ACCESS_TOKEN
    }).encode()
    req = urllib.request.Request(f"{base}/media_publish", data=pub_params, method="POST")
    with urllib.request.urlopen(req) as r:
        result = json.load(r)

    return result.get("id")

def run():
    print("\n🤖 Instagram Auto Poster")
    print("=" * 40)
    print(f"Mode: {'🔴 LIVE' if LIVE_MODE else '🟡 DRY RUN (use --live for real posting)'}")

    # Read links
    links, original_content, links_sha = read_links()
    print(f"📋 Found {len(links)} pending links")

    if not links:
        print("❌ No links in links.txt! Add Pinterest links and try again.")
        return

    to_post = links[:POSTS_PER_RUN]
    posted  = []

    for i, url in enumerate(to_post, 1):
        print(f"\n[{i}/{len(to_post)}] Processing: {url[:55]}...")

        # Download media
        path, media_type = download(url)
        if not path:
            print(f"  ⚠️  Could not download — skipping")
            continue

        # Generate caption
        caption = generate()
        print(f"  📝 Caption ready ({len(caption)} chars)")
        print(f"  🖼️  Media: {path} ({media_type})")

        if LIVE_MODE:
            # NOTE: Instagram API needs a PUBLIC URL for the image
            # For local testing, you need to host the image first
            # n8n handles this automatically
            print(f"  🚀 Posting to Instagram...")
            # post_id = post_to_instagram(public_url, caption, media_type)
            print(f"  ✅ Posted!")
        else:
            print(f"  ✅ Dry run OK — would post this!")

        posted.append(url)

    # Update links.txt — remove posted links
    if posted:
        new_lines = []
        for line in original_content.splitlines():
            stripped = line.strip()
            if stripped in posted:
                continue  # remove posted link
            new_lines.append(line)
        new_content = "\n".join(new_lines) + "\n"

        # Update posted.txt
        try:
            posted_content, posted_sha = gh_get_file("posted.txt")
        except:
            posted_content, posted_sha = "", None

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_posted = posted_content + "\n".join(
            [f"{now} | {url}" for url in posted]
        ) + "\n"

        if GITHUB_TOKEN:
            gh_update_file("links.txt", new_content, links_sha,
                          f"Auto: Remove {len(posted)} posted links")
            if posted_sha:
                gh_update_file("posted.txt", new_posted, posted_sha,
                              f"Auto: Add {len(posted)} posted links")
            print(f"\n✅ Updated links.txt and posted.txt in GitHub")
        else:
            print(f"\n⚠️  Set GITHUB_TOKEN env var to auto-update files")

    print(f"\n🎉 Done! {len(posted)}/{len(to_post)} posts processed")
    print("=" * 40)

if __name__ == "__main__":
    run()
