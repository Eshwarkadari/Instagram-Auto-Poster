# 📸 Instagram Auto Poster

> Fully automated Instagram posting system — reads Pinterest links from **`links.txt`** in this repo, downloads media, generates captions, posts **3 times daily** using **n8n** (free) and **GitHub as database**.

![n8n](https://img.shields.io/badge/n8n-Automation-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)
![Instagram](https://img.shields.io/badge/Instagram-API-E4405F?style=for-the-badge&logo=instagram&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-Database-100000?style=for-the-badge&logo=github&logoColor=white)
![Pinterest](https://img.shields.io/badge/Pinterest-E60023?style=for-the-badge&logo=pinterest&logoColor=white)

---

## 🏗️ How It Works

```
links.txt (in this GitHub repo)
        ↓  every 8 hours (3x daily)
    n8n Workflow
        ↓
  Read 3 links from links.txt via GitHub API
        ↓
  Download image/video from Pinterest
        ↓
  Generate caption automatically
        ↓
  Post to Instagram via Facebook API
        ↓
  Move posted links to posted.txt in GitHub
```

---

## 📝 How to Add Links (Super Simple!)

1. Open **`links.txt`** in this repo
2. Click the **pencil icon** (Edit)
3. Add your Pinterest links — one per line:
```
https://pin.it/abc123
https://pin.it/xyz456
https://www.pinterest.com/pin/123456789
```
4. Click **Commit changes**
5. Done! Automation picks 3 daily ✅

---

## 📁 Project Structure

```
Instagram-Auto-Poster/
├── links.txt              ← ADD YOUR PINTEREST LINKS HERE
├── posted.txt             ← Automatically updated (posted links)
├── n8n/
│   └── workflow.json      ← Import this into n8n
├── python/
│   ├── poster.py          ← Run manually to test
│   ├── pinterest_downloader.py
│   └── caption_generator.py
├── setup/
│   ├── 01_facebook_setup.md
│   ├── 02_n8n_setup.md
│   └── 03_credentials.md
└── README.md
```

---

## ⚡ Setup Steps (15 mins total)

| Step | Task | Time |
|------|------|------|
| 1 | Get Facebook Access Token + Instagram Account ID | 8 min |
| 2 | Deploy n8n FREE on Render | 5 min |
| 3 | Import workflow + add credentials | 2 min |
| 4 | Add links to links.txt | 1 min |

---

## 🔑 Credentials Needed

| Credential | Where to get |
|-----------|-------------|
| `INSTAGRAM_ACCOUNT_ID` | Facebook Graph API Explorer |
| `FACEBOOK_ACCESS_TOKEN` | Facebook Developer App |
| `GITHUB_TOKEN` | github.com/settings/tokens |
| `GITHUB_REPO` | `Eshwarkadari/Instagram-Auto-Poster` |

---

## 🕐 Posting Schedule

Posts automatically at:
- **8:00 AM** — Morning post
- **2:00 PM** — Afternoon post
- **8:00 PM** — Evening post

---

## 👨‍💻 Author

**Kadari Eshwar** — ECE Student, JNTU Hyderabad
[GitHub](https://github.com/Eshwarkadari) | [LinkedIn](https://www.linkedin.com/in/eshwar-kadari-134aa4278)
