# 📸 Instagram Auto Poster

> Fully automated Instagram posting system — reads Pinterest links from Google Sheet, downloads media, generates AI captions, and posts **3 times daily** — completely FREE using n8n on Render.

![n8n](https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)
![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google_Sheets-34A853?style=for-the-badge&logo=google-sheets&logoColor=white)
![Pinterest](https://img.shields.io/badge/Pinterest-E60023?style=for-the-badge&logo=pinterest&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

---

## 🔄 How It Works

```
Google Sheet (Pinterest URLs)
        ↓  every day at 9am, 1pm, 6pm
    n8n Workflow (free on Render)
        ↓
    Python Script
        ↓  downloads image/video from Pinterest
    Media File
        ↓  generates caption using AI or template
    Caption
        ↓  posts via Facebook Graph API
    Instagram Business Page
        ↓  marks as posted
    Google Sheet (status = posted ✅)
```

---

## ✨ Features

- 📋 **Google Sheet as database** — just paste Pinterest links
- 📥 **Auto download** images & videos from Pinterest
- 🤖 **Auto caption** generation from image metadata
- 📅 **Posts 3x daily** — 9 AM, 1 PM, 6 PM (IST)
- ✅ **Tracks posted** — marks status in Google Sheet
- 🔁 **Never reposts** — skips already posted links
- 🆓 **100% FREE** — n8n on Render free tier
- 📊 **Multiple links supported** — handles 100s of links

---

## 🗂️ Project Structure

```
Instagram-Auto-Poster/
├── n8n/
│   └── workflow.json          # Import this into n8n
├── python/
│   ├── pinterest_downloader.py   # Download media from Pinterest
│   ├── caption_generator.py      # Generate captions
│   ├── instagram_poster.py       # Post to Instagram
│   └── sheet_manager.py          # Read/write Google Sheet
├── render/
│   └── render.yaml            # Deploy n8n on Render
├── setup/
│   ├── 01_facebook_setup.md   # Step-by-step Facebook API setup
│   ├── 02_google_sheet.md     # Google Sheet setup
│   ├── 03_n8n_setup.md        # n8n setup on Render
│   └── 04_run.md              # Final run instructions
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Setup (follow in order)

1. Read `setup/01_facebook_setup.md` → get Instagram credentials
2. Read `setup/02_google_sheet.md` → set up your sheet
3. Read `setup/03_n8n_setup.md` → deploy n8n free on Render
4. Read `setup/04_run.md` → import workflow and go live

---

## 👨‍💻 Author

**Kadari Eshwar** — ECE Student, JNTU Hyderabad
[GitHub](https://github.com/Eshwarkadari) | [LinkedIn](https://www.linkedin.com/in/eshwar-kadari-134aa4278)
