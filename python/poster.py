import os
import requests
import base64
import json
import time
import re
import random

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
    """Get direct image URL from Pinterest"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # Try oEmbed
        oembed = f"https://www.pinterest.com/oembed.json?url={pin_url}"
        r = requests.get(oembed, timeout=10, headers=headers)
        if r.status_code == 200:
            data = r.json()
            img = data.get('thumbnail_url', '')
            for low, high in [('236x', 'originals'), ('474x', 'originals'), ('736x', 'originals')]:
                img = img.replace(low, high)
            if img:
                print(f"  oEmbed image: {img[:60]}...")
                return img
    except Exception as e:
        print(f"  oEmbed failed: {e}")

    try:
        # Scrape page
        r = requests.get(pin_url, timeout=15, headers=headers, allow_redirects=True)
        html = r.text
        patterns = [
            r'"contentUrl":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'(https://i\.pinimg\.com/originals/[^\s"\']+\.(?:jpg|jpeg|png))',
            r'(https://i\.pinimg\.com/736x/[^\s"\']+\.(?:jpg|jpeg|png))',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                img = match.group(1)
                print(f"  Scraped image: {img[:60]}...")
                return img
    except Exception as e:
        print(f"  Scrape failed: {e}")

    return None

def upload_image_to_imgbb(image_url):
    """Download image and upload to imgbb for a stable public URL"""
    IMGBB_API_KEY = "temp"  # We'll use catbox.moe instead - no API key needed
    
    try:
        # Download image
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(image_url, timeout=30, headers=headers)
        r.raise_for_status()
        image_data = r.content
        print(f"  Downloaded image: {len(image_data)} bytes")

        # Upload to catbox.moe (free, no API key needed)
        files = {'fileToUpload': ('image.jpg', image_data, 'image/jpeg')}
        data = {'reqtype': 'fileupload', 'userhash': ''}
        upload_r = requests.post('https://catbox.moe/user/api.php', files=files, data=data, timeout=30)
        
        if upload_r.status_code == 200 and upload_r.text.startswith('https://'):
            public_url = upload_r.text.strip()
            print(f"  Uploaded to: {public_url}")
            return public_url
        else:
            print(f"  catbox upload failed: {upload_r.text[:100]}")
    except Exception as e:
        print(f"  Upload failed: {e}")
    
    return None

def create_instagram_container(image_url, caption):
    url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print(f"  Instagram API error: {r.text}")
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
        print("❌ No links found in links.txt!")
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

    for pin_url in to_post:
        print(f"\n📌 Processing: {pin_url}")
        try:
            # Step 1: Get Pinterest image URL
            image_url = get_pinterest_image(pin_url)
            if not image_url:
                print(f"  ⚠️ Could not extract image, skipping...")
                remaining.insert(0, pin_url)
                continue

            # Step 2: Upload to public host so Instagram can access it
            print(f"  📤 Uploading image to public host...")
            public_url = upload_image_to_imgbb(image_url)
            if not public_url:
                print(f"  ⚠️ Could not upload image, skipping...")
                remaining.insert(0, pin_url)
                continue

            # Step 3: Generate caption
            caption = random.choice(CAPTIONS)

            # Step 4: Create Instagram container
            print(f"  📲 Creating Instagram container...")
            container_id = create_instagram_container(public_url, caption)
            print(f"  ✅ Container: {container_id}")

            # Step 5: Wait for processing
            print(f"  ⏳ Waiting 15s...")
            time.sleep(15)

            # Step 6: Publish
            print(f"  🚀 Publishing...")
            post_id = publish_instagram(container_id)
            print(f"  ✅ Posted! ID: {post_id}")

            posted_this_run.append(pin_url)
            time.sleep(5)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            remaining.insert(0, pin_url)

    # Update links.txt
    new_links = "# Add your Pinterest links below (one per line)\n\n"
    new_links += '\n'.join(remaining) + '\n'
    update_file("links.txt", new_links, links_sha, f"Auto: removed {len(posted_this_run)} posted links")

    # Update posted.txt
    if posted_this_run:
        new_posted = (posted_content.strip() + '\n' + '\n'.join(posted_this_run) + '\n').strip()
        if posted_sha:
            update_file("posted.txt", new_posted, posted_sha, f"Auto: added {len(posted_this_run)} posted links")
        else:
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
