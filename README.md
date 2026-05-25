# 📸 Instagram Auto Poster

> Fully automated Instagram posting system — reads Pinterest links from Google Sheet, downloads media, generates AI captions, and posts **3 times daily** using **n8n** (free).

![n8n](https://img.shields.io/badge/n8n-Automation-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)
![Instagram](https://img.shields.io/badge/Instagram-API-E4405F?style=for-the-badge&logo=instagram&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google_Sheets-34A853?style=for-the-badge&logo=google-sheets&logoColor=white)
![Pinterest](https://img.shields.io/badge/Pinterest-E60023?style=for-the-badge&logo=pinterest&logoColor=white)

---

## 🏗️ How It Works

```
Google Sheet (Pinterest links)
        ↓  every 8 hours (3x daily)
    n8n Workflow
        ↓
  Read 3 pending links
        ↓
  Download image/video from Pinterest
        ↓
  Generate caption (AI or template)
        ↓
  Upload to Instagram via Facebook API
        ↓
  Mark as "posted" in Google Sheet
```

---

## 📁 Project Structure

```
Instagram-Auto-Poster/
├── n8n/
│   └── workflow.json          # Import this into n8n
├── python/
│   ├── pinterest_downloader.py  # Download media from Pinterest
│   ├── caption_generator.py     # Generate captions
│   └── instagram_poster.py      # Post to Instagram API
├── setup/
│   ├── 01_facebook_setup.md     # Facebook App setup guide
│   ├── 02_instagram_setup.md    # Instagram API setup guide
│   ├── 03_google_sheet_setup.md # Google Sheet setup guide
│   └── 04_n8n_setup.md          # n8n setup on Render
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Setup (15 minutes total)

| Step | Task | Time |
|------|------|------|
| 1 | Create Facebook Developer App | 5 min |
| 2 | Get Instagram Access Token | 3 min |
| 3 | Set up Google Sheet | 2 min |
| 4 | Deploy n8n on Render | 3 min |
| 5 | Import workflow into n8n | 2 min |

Follow the guides in the `/setup` folder in order!

---

## 📊 Google Sheet Format

Create a sheet with these exact column headers:

| pinterest_url | description | status | posted_date | post_id |
|--------------|-------------|--------|-------------|---------|
| https://pin.it/abc | (optional caption) | pending | | |
| https://pin.it/xyz | | pending | | |

- **pinterest_url** — paste your Pinterest links here
- **description** — optional custom caption (leave blank = auto-generated)
- **status** — always write `pending` for new links
- **posted_date** — filled automatically by automation
- **post_id** — filled automatically by automation

---

## 🔑 Credentials You Need

| Credential | Where to get |
|-----------|-------------|
| `INSTAGRAM_ACCOUNT_ID` | Facebook Business Manager |
| `FACEBOOK_ACCESS_TOKEN` | Facebook Developer App |
| `GOOGLE_SHEET_ID` | From your Google Sheet URL |
| `GOOGLE_CREDENTIALS` | Google Cloud Console |

All credentials go into n8n as **Credentials** (never hardcoded).

---

## 🕐 Posting Schedule

Posts automatically at:
- **8:00 AM** — Morning post
- **2:00 PM** — Afternoon post  
- **8:00 PM** — Evening post

You can change the schedule in n8n anytime.

---

## 👨‍💻 Author

**Kadari Eshwar** — ECE Student, JNTU Hyderabad
[GitHub](https://github.com/Eshwarkadari) | [LinkedIn](https://www.linkedin.com/in/eshwar-kadari-134aa4278)
