import os
import requests
import base64
import json
import time

INSTAGRAM_ACCESS_TOKEN = os.environ['INSTAGRAM_ACCESS_TOKEN']
INSTAGRAM_ACCOUNT_ID = os.environ['INSTAGRAM_ACCOUNT_ID']
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_REPO = os.environ['GITHUB_REPO']

HEADERS_GH = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

CAPTIONS = [
    "✨ Beautiful moments captured. 📸\n\n#photography #beautiful #amazing #aesthetic #instagood #viral #trending",
    "🌟 Life is beautiful. Enjoy every moment. 💫\n\n#life #beautiful #moments #photography #instagood #explore",
    "📸 A picture says a thousand words. 🎨\n\n#photography #art #beautiful #creative #aesthetic #photooftheday",
    "💫 Creating memories one photo at a time. ✨\n\n#photography #memories #beautiful #instagood #reels #viral",
    "🌈 Colors of life. 🎨\n\n#colorful #beautiful #photography #aesthetic #instagram #viral #trending",
    "🔥 Absolutely stunning! 😍\n\n#stunning #beautiful #photography #amazing #viral #trending #reels",
    "💎 Pure perfection. ✨\n\n#perfect #beautiful #photography #aesthetic #instagood #amazing",
    "🌸 Beauty is everywhere. 🌺\n\n#beauty #beautiful #nature #photography #aesthetic #instagood",
]

def get_file(path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    r = requests.get(url, headers=HEADERS_GH)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data['content']).decode('utf-8')
    return content, data['sha']

def update_file(path, content, sha, message):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {"message": message, "content": encoded, "sha": sha}
    r = requests.put(url, headers=HEADERS_GH, json=payload)
    r.raise_for_status()
    print(f"✅ Updated {path}")

def get_pinterest_image(pin_url):
    """Get image URL from Pinterest pin"""
    try:
        # Try oEmbed first
        oembed_url = f"https://www.pinterest.com/oembed.json?url={pin_url}"
        r = requests.get(oembed_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            data = r.json()
            img = data.get('thumbnail_url', '')
            # Upgrade resolution
            for low, high in [('236x', '736x'), ('474x', '736x'), ('170x', '736x')]:
                img = img.replace(low, high)
            if img:
                return img
    except Exception as e:
        print(f"oEmbed failed: {e}")

    try:
        # Fallback: scrape page
        r = requests.get(pin_url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        html = r.text
        import re
        patterns = [
            r'"contentUrl":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'(https://i\.pinimg\.com/736x/[^\s"]+\.(?:jpg|jpeg|png))',
            r'(https://i\.pinimg\.com/originals/[^\s"]+\.(?:jpg|jpeg|png))',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Scrape failed: {e}")

    return None

def create_instagram_container(image_url, caption):
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    r = requests.post(url, data=payload)
    r.raise_for_status()
    return r.json()['id']

def publish_instagram(container_id):
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    r = requests.post(url, data=payload)
    r.raise_for_status()
    return r.json()['id']

def main():
    print("🚀 Starting Instagram Auto Poster...")

    # Read links.txt
    links_content, links_sha = get_file("links.txt")
    links = [l.strip() for l in links_content.split('\n')
             if l.strip() and not l.strip().startswith('#') and 'pin' in l.lower()]

    if not links:
        print("❌ No links found in links.txt! Add Pinterest links to continue.")
        return

    print(f"📋 Found {len(links)} links. Processing first 3...")

    # Read posted.txt
    try:
        posted_content, posted_sha = get_file("posted.txt")
    except:
        posted_content, posted_sha = "", None

    to_post = links[:3]
    remaining = links[3:]
    posted_this_run = []
    import random

    for pin_url in to_post:
        print(f"\n📌 Processing: {pin_url}")
        try:
            # Get image
            image_url = get_pinterest_image(pin_url)
            if not image_url:
                print(f"⚠️ Could not extract image from {pin_url}, skipping...")
                remaining.insert(0, pin_url)
                continue

            print(f"🖼️ Image URL: {image_url[:60]}...")

            # Generate caption
            caption = random.choice(CAPTIONS)

            # Create container
            print("📤 Creating Instagram container...")
            container_id = create_instagram_container(image_url, caption)
            print(f"✅ Container created: {container_id}")

            # Wait for processing
            time.sleep(15)

            # Publish
            print("🚀 Publishing to Instagram...")
            post_id = publish_instagram(container_id)
            print(f"✅ Posted successfully! Post ID: {post_id}")

            posted_this_run.append(pin_url)
            time.sleep(5)

        except Exception as e:
            print(f"❌ Error posting {pin_url}: {e}")
            remaining.insert(0, pin_url)

    # Update links.txt - remove posted links
    new_links = "# Add your Pinterest links below (one per line)\n# Lines starting with # are ignored\n\n"
    new_links += '\n'.join(remaining) + '\n'
    update_file("links.txt", new_links, links_sha, f"Auto: removed {len(posted_this_run)} posted links")

    # Update posted.txt - add posted links
    if posted_this_run:
        new_posted = posted_content.strip() + '\n' + '\n'.join(posted_this_run) + '\n'
        if posted_sha:
            update_file("posted.txt", new_posted, posted_sha, f"Auto: added {len(posted_this_run)} posted links")
        else:
            # Create posted.txt if doesn't exist
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/posted.txt"
            encoded = base64.b64encode(new_posted.encode()).decode()
            requests.put(url, headers=HEADERS_GH, json={
                "message": "Auto: created posted.txt",
                "content": encoded
            })
            print("✅ Created posted.txt")

    print(f"\n🎉 Done! Posted {len(posted_this_run)}/3 images to Instagram.")

if __name__ == "__main__":
    main()
