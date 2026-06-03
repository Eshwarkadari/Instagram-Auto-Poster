"""
caption_generator.py
AI-powered Instagram caption generator for men's fashion
Uses OpenAI GPT-4o Vision to analyze outfit images
Author: Kadari Eshwar
"""

import os
import base64
import logging
import random
import requests

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

SYSTEM_PROMPT = """You are an expert Instagram men's fashion content creator.
Your task is to analyze the fashion image provided and generate a highly engaging Instagram caption.

Follow this exact structure:

🔥 [Create a short, catchy outfit title]

[Write 1-2 short sentences describing the outfit. Mention where it can be worn such as college, casual outings, office, dates, parties, travel, etc. Make it stylish and aspirational.]

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

[Generate 15 highly relevant hashtags]

Rules:
- Focus only on men's fashion
- Caption must be under 100 words
- Make the title catchy and modern
- Use emojis naturally
- Do not mention Pinterest, AI, or image analysis
- Do not use quotation marks except around the word LINK
- Generate different captions for every image
- Hashtags must be relevant to the outfit style detected in the image
- Include hashtags for men's fashion, style, outfits, streetwear, casual wear, formal wear, fashion trends
- Return only the final Instagram caption
- No explanations, no markdown
- Output must be ready to post directly on Instagram"""

FALLBACK_CAPTIONS = [
    """🔥 Clean Casual Vibes

A minimal and stylish look perfect for college, weekend outings, and coffee dates. Easy to wear, hard to ignore.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #mensstyle #outfitideas #styleformen #menswear #streetwear #fashion #casualstyle #outfitinspiration #fashionreels #styleinspo #indianmensfashion #fashiontips #trendystyle #dailyoutfit""",

    """🔥 Effortless Street Style

This fresh outfit brings together comfort and style — ideal for casual meetups, college hangouts, and city walks.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #streetwear #ootd #mensstyle #casualwear #fashionformen #outfitoftheday #styleinspo #indianfashion #trendingoutfit #menswear #lookbook #fashionblogger #outfitgoals #swag""",

    """🔥 Smart & Sharp Look

Dress to impress with this versatile outfit that transitions effortlessly from office to evening outings.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #smartcasual #officewear #mensstyle #fashionformen #outfitinspiration #styleformen #menswear #dressedtoimpress #indianmensfashion #fashiontips #outfitideas #trendingfashion #lookoftheday #gentlemanstyle""",

    """🔥 Weekend Ready Fit

Keep it cool and stylish this weekend with this fresh combination — works great for brunch, travel, or a quick grocery run.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #weekendvibes #casualstyle #menswear #ootdmen #streetstyle #outfitcheck #fashionformen #styleinspo #indianmensstyle #trendingoutfit #mensfashionblogger #simplestyle #dailyoutfit #outfitgoals""",

    """🔥 Bold & Trendy

Make a statement with this bold outfit that's perfect for parties, dates, and nights out with friends.

💬 Comment "LINK" for product links
📌 Save this look for later
👔 Follow @styleformenindia for daily men's fashion inspiration

#mensfashion #boldstyle #partyoutfit #menswear #fashionformen #trendingfashion #styleformen #nightout #outfitinspiration #indianfashion #mensstyleinspo #fashionreels #lookbook #outfitoftheday #swagstyle""",
]


def generate_ai_caption(image_path: str) -> str:
    """Use OpenAI GPT-4o Vision to generate caption from outfit image"""
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key found, using fallback caption")
        return random.choice(FALLBACK_CAPTIONS)

    try:
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = image_path.split(".")[-1].lower()
        mime_type = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"

        logger.info("Sending image to OpenAI Vision...")

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "max_tokens": 500,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT
                        }
                    ]
                }]
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()
        caption = result["choices"][0]["message"]["content"].strip()
        logger.info("✅ AI caption generated successfully")
        return caption

    except Exception as e:
        logger.error(f"OpenAI Vision failed: {e}, using fallback")
        return random.choice(FALLBACK_CAPTIONS)


def generate_ai_caption_from_url(image_url: str) -> str:
    """Use OpenAI GPT-4o Vision to generate caption from image URL"""
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key found, using fallback caption")
        return random.choice(FALLBACK_CAPTIONS)

    try:
        logger.info(f"Sending image URL to OpenAI Vision: {image_url[:60]}...")

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "max_tokens": 500,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        },
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT
                        }
                    ]
                }]
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()
        caption = result["choices"][0]["message"]["content"].strip()
        logger.info("✅ AI caption generated successfully")
        return caption

    except Exception as e:
        logger.error(f"OpenAI Vision failed: {e}, using fallback")
        return random.choice(FALLBACK_CAPTIONS)


def generate(custom=None, image_path=None, image_url=None):
    """
    Main caption generator function.
    Priority: AI Vision (image_path) > AI Vision (image_url) > custom > fallback
    """
    if image_path and os.path.exists(image_path) and OPENAI_API_KEY:
        return generate_ai_caption(image_path)
    
    if image_url and OPENAI_API_KEY:
        return generate_ai_caption_from_url(image_url)
    
    if custom and len(custom.strip()) > 5:
        return custom.strip()
    
    return random.choice(FALLBACK_CAPTIONS)
