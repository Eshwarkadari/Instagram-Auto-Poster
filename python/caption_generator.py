"""
caption_generator.py
Generates Instagram captions with hashtags
Author: Kadari Eshwar
"""
import random

CAPTIONS = [
    "✨ Beautiful moments captured. 📸\n\n#photography #beautiful #amazing #aesthetic #instagood #viral #trending #reels",
    "🌟 Life is beautiful. Enjoy every moment. 💫\n\n#life #beautiful #moments #photography #amazing #instagood #explore",
    "📸 A picture says a thousand words. 🎨\n\n#photography #art #beautiful #creative #aesthetic #instagram #photooftheday",
    "💫 Creating memories one photo at a time. ✨\n\n#photography #memories #beautiful #amazing #instagood #reels #viral",
    "🌈 Colors of life. 🎨\n\n#colorful #beautiful #photography #aesthetic #amazing #instagram #viral #trending",
    "🔥 Absolutely stunning! 😍\n\n#stunning #beautiful #photography #amazing #viral #trending #reels #instagood",
    "💎 Pure perfection. ✨\n\n#perfect #beautiful #photography #aesthetic #instagood #photooftheday #amazing",
    "🌸 Beauty is everywhere. 🌺\n\n#beauty #beautiful #nature #photography #aesthetic #amazing #instagood #flowers",
    "⚡ This is everything! 🙌\n\n#amazing #beautiful #photography #viral #trending #reels #instagood #explore",
    "🎯 Goals! 💯\n\n#goals #beautiful #amazing #photography #instagood #viral #trending #aesthetic #reels",
]

def generate(custom=None):
    """Return a caption — use custom if provided, else random."""
    if custom and len(custom.strip()) > 5:
        return custom.strip() + "\n\n#instagood #photooftheday #beautiful #photography #instagram #viral #trending"
    return random.choice(CAPTIONS)
