"""
caption_generator.py
Generates Instagram captions for Pinterest content
Author: Kadari Eshwar
"""

import random

# Hashtag sets by topic — add more as needed
HASHTAG_SETS = {
    "general": "#instagram #viral #trending #explore #daily #content #post #reels #fyp #foryou",
    "nature":  "#nature #naturephotography #beautiful #landscape #earth #travel #adventure #outdoors",
    "food":    "#food #foodie #foodphotography #delicious #yummy #recipe #cooking #chef #homemade",
    "fashion": "#fashion #style #outfit #ootd #trendy #clothing #look #aesthetic #instafashion",
    "tech":    "#technology #tech #innovation #gadgets #digital #future #ai #programming #coding",
    "motivation": "#motivation #inspiration #success #mindset #goals #hustle #positivity #growth",
}

CAPTION_TEMPLATES = [
    "✨ {title}

{hashtags}",
    "🔥 {title}

Double tap if you love this! ❤️

{hashtags}",
    "💫 {title}

Save this for later! 🔖

{hashtags}",
    "👀 {title}

What do you think? Comment below! 👇

{hashtags}",
    "⭐ {title}

Share with someone who needs to see this! 📲

{hashtags}",
    "🎯 {title}

Follow for more content like this! 🚀

{hashtags}",
    "💥 {title}

Tag a friend! 👇

{hashtags}",
]

def generate_caption(title: str = "", topic: str = "general", custom: str = "") -> str:
    """
    Generate an Instagram caption.
    - If custom caption provided, use it + hashtags
    - Otherwise generate from title + template
    """
    hashtags = HASHTAG_SETS.get(topic, HASHTAG_SETS["general"])

    if custom and custom.strip():
        return f"{custom.strip()}\n\n{hashtags}"

    clean_title = title.strip() if title else "Amazing content you don't want to miss"
    # Remove Pinterest-specific text
    for remove in ["on Pinterest", "- Pinterest", "| Pinterest"]:
        clean_title = clean_title.replace(remove, "").strip()

    template = random.choice(CAPTION_TEMPLATES)
    return template.format(title=clean_title, hashtags=hashtags)


if __name__ == "__main__":
    print(generate_caption("Beautiful sunset photography", "nature"))
    print("---")
    print(generate_caption(custom="Check out this amazing recipe! 🍕"))
