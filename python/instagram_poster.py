"""
instagram_poster.py
Posts image or video to Instagram Business Account via Facebook Graph API
Author: Kadari Eshwar

Requirements:
  - Instagram Business Account linked to Facebook Page
  - Facebook App with instagram_basic, instagram_content_publish permissions
  - Long-lived access token
"""

import requests, os, time

GRAPH_URL = "https://graph.facebook.com/v18.0"

def post_image(ig_user_id: str, access_token: str, image_url: str, caption: str) -> dict:
    """Post an image to Instagram. image_url must be a public URL."""

    # Step 1: Create media container
    print("📤 Creating media container...")
    r = requests.post(
        f"{GRAPH_URL}/{ig_user_id}/media",
        data={
            "image_url":    image_url,
            "caption":      caption,
            "access_token": access_token,
        }
    )
    data = r.json()
    if "id" not in data:
        print(f"❌ Container error: {data}")
        return data

    container_id = data["id"]
    print(f"✅ Container created: {container_id}")

    # Step 2: Wait for container to be ready
    time.sleep(5)

    # Step 3: Publish
    print("🚀 Publishing post...")
    r2 = requests.post(
        f"{GRAPH_URL}/{ig_user_id}/media_publish",
        data={
            "creation_id":  container_id,
            "access_token": access_token,
        }
    )
    result = r2.json()
    if "id" in result:
        print(f"✅ Posted! Post ID: {result['id']}")
    else:
        print(f"❌ Publish error: {result}")
    return result


def post_video(ig_user_id: str, access_token: str, video_url: str, caption: str) -> dict:
    """Post a video/reel to Instagram."""

    print("📤 Creating video container...")
    r = requests.post(
        f"{GRAPH_URL}/{ig_user_id}/media",
        data={
            "media_type":   "REELS",
            "video_url":    video_url,
            "caption":      caption,
            "share_to_feed": "true",
            "access_token": access_token,
        }
    )
    data = r.json()
    if "id" not in data:
        print(f"❌ Container error: {data}")
        return data

    container_id = data["id"]
    print(f"✅ Container: {container_id} — waiting for processing...")

    # Wait for video to process (up to 2 minutes)
    for i in range(24):
        time.sleep(5)
        status_r = requests.get(
            f"{GRAPH_URL}/{container_id}",
            params={"fields": "status_code", "access_token": access_token}
        )
        status = status_r.json().get("status_code")
        print(f"  Status: {status} ({(i+1)*5}s)")
        if status == "FINISHED":
            break
        if status == "ERROR":
            print("❌ Video processing failed")
            return {"error": "Video processing failed"}

    # Publish
    r2 = requests.post(
        f"{GRAPH_URL}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token}
    )
    result = r2.json()
    if "id" in result:
        print(f"✅ Video posted! Post ID: {result['id']}")
    else:
        print(f"❌ Publish error: {result}")
    return result


def get_ig_user_id(page_access_token: str, page_id: str) -> str:
    """Get Instagram Business Account ID linked to Facebook Page."""
    r = requests.get(
        f"{GRAPH_URL}/{page_id}",
        params={"fields": "instagram_business_account", "access_token": page_access_token}
    )
    data = r.json()
    ig_id = data.get("instagram_business_account", {}).get("id")
    if ig_id:
        print(f"✅ Instagram User ID: {ig_id}")
    else:
        print(f"❌ Could not get Instagram ID: {data}")
    return ig_id
