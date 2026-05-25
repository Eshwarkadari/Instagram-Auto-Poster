"""
caption_generator.py
Generates Instagram captions for posts
Author: Kadari Eshwar | B.Tech ECE, JNTU Hyderabad
"""

import random

# Caption templates by category
CAPTIONS = {
    "nature": [
        "🌿 Nature never goes out of style. ✨ #nature #beautiful #photography #naturelover #aesthetic",
        "🍃 Find peace in every leaf. 🌱 #nature #green #peaceful #photography #naturalbeauty",
        "🌸 Beauty is everywhere you look. 🌺 #flowers #nature #photography #beautiful #colorful",
    ],
    "travel": [
        "✈️ The world is too beautiful not to explore. 🌍 #travel #explore #wanderlust #adventure #photography",
        "🗺️ Every journey begins with a single step. 👣 #travel #adventure #explore #wanderlust #travelblogger",
        "🌅 Collecting memories, not things. 📸 #travel #memories #explore #beautiful #photography",
    ],
    "food": [
        "🍽️ Good food = Good mood! 😋 #food #foodie #delicious #yummy #foodphotography",
        "👨‍🍳 Life is too short for bad food. 🍴 #food #foodlover #delicious #foodphotography #yummy",
        "🤤 Eating my way through life. 😍 #food #foodie #delicious #tasty #foodphotography",
    ],
    "fashion": [
        "👗 Style is a way to say who you are. ✨ #fashion #style #ootd #fashionista #aesthetic",
        "💫 Dress like you're already famous. 👑 #fashion #style #ootd #outfitoftheday #fashionblogger",
        "🌟 Confidence is the best outfit. 💃 #fashion #style #ootd #fashionista #beautiful",
    ],
    "motivation": [
        "💪 Dream it. Believe it. Achieve it. 🚀 #motivation #inspiration #success #mindset #hustle",
        "✨ Every day is a new beginning. 🌅 #motivation #inspiration #positivity #mindset #success",
        "🔥 Work hard in silence. Let success make the noise. 💯 #motivation #success #hustle #grind #goals",
    ],
    "default": [
        "✨ Beautiful moments captured. 📸 #photography #beautiful #amazing #aesthetic #instagood",
        "🌟 Life is beautiful. Enjoy every moment. 💫 #life #beautiful #moments #photography #amazing",
        "📸 A picture says a thousand words. 🎨 #photography #art #beautiful #creative #aesthetic",
        "💫 Creating memories one photo at a time. ✨ #photography #memories #beautiful #amazing #instagood",
        "🌈 Colors of life. 🎨 #colorful #beautiful #photography #aesthetic #amazing",
    ]
}

HASHTAG_SETS = [
    "#instagood #photooftheday #beautiful #photography #picoftheday #instagram #photo #art #follow #nature",
    "#instadaily #photography #love #beautiful #happy #cute #fashion #art #photographer #style",
    "#explore #viral #trending #reels #instareels #share #like #comment #follow #fyp",
]

def generate_caption(custom_caption=None, category="default"):
    """
    Generate a caption for an Instagram post.
    If custom_caption provided, enhance it with hashtags.
    Otherwise generate from templates.
    """
    if custom_caption and len(custom_caption.strip()) > 5:
        # Enhance custom caption with hashtags
        hashtags = random.choice(HASHTAG_SETS)
        return f"{custom_caption.strip()}

{hashtags}"

    # Generate from template
    templates = CAPTIONS.get(category, CAPTIONS["default"])
    caption   = random.choice(templates)

    # Add extra hashtag set
    extra_tags = random.choice(HASHTAG_SETS)
    return f"{caption}

{extra_tags}"

def detect_category(pinterest_url):
    """Try to detect content category from URL."""
    url_lower = pinterest_url.lower()
    if any(w in url_lower for w in ["nature","flower","forest","plant","green"]):
        return "nature"
    if any(w in url_lower for w in ["travel","trip","city","explore","wanderlust"]):
        return "travel"
    if any(w in url_lower for w in ["food","recipe","cook","eat","restaurant"]):
        return "food"
    if any(w in url_lower for w in ["fashion","style","outfit","dress","clothing"]):
        return "fashion"
    if any(w in url_lower for w in ["motivation","quote","success","inspire"]):
        return "motivation"
    return "default"

if __name__ == "__main__":
    print("=== Caption Generator Test ===")
    print("\nAuto-generated caption:")
    print(generate_caption())
    print("\nCustom caption enhanced:")
    print(generate_caption("Check out this amazing view!"))
