# Pinterest → Instagram Automation - Complete Setup Guide

## 🎯 What This Does
- Paste Pinterest URLs anytime via webhook
- Auto-posts 3x daily (9AM, 1PM, 7PM IST)
- Never reposts same URL twice
- Sends Telegram notifications
- Tracks everything in Google Sheets

---

## 📋 STEP 1 — Create Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com)
2. Create new spreadsheet named: `Pinterest Instagram Queue`
3. Add these exact column headers in Row 1:

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| ID | Pinterest_URL | Status | Added_Date | Posted_Date | Instagram_Post_ID |

4. Copy the Sheet ID from URL:
   `https://docs.google.com/spreadsheets/d/`**`THIS_IS_YOUR_SHEET_ID`**`/edit`

---

## 📋 STEP 2 — Create Telegram Bot

1. Open Telegram → search `@BotFather`
2. Send `/newbot`
3. Give it a name: `StyleForMenIndia Bot`
4. Copy the **Bot Token**
5. Start your bot → send any message
6. Get your Chat ID:
   Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Find `"chat":{"id":YOUR_CHAT_ID}`

---

## 📋 STEP 3 — Import Workflow into n8n

1. Open your n8n instance
2. Click **+** → **Import from file**
3. Upload `pinterest_instagram_workflow.json`

---

## 📋 STEP 4 — Add Credentials in n8n

### Google Sheets:
1. Credentials → New → **Google Sheets OAuth2**
2. Follow OAuth setup
3. Name it: `Google Sheets`

### Telegram:
1. Credentials → New → **Telegram**
2. Enter your Bot Token
3. Name it: `Telegram Bot`

---

## 📋 STEP 5 — Add Variables in n8n

Go to **Settings → Variables** → Add these:

| Variable | Value |
|---|---|
| `GOOGLE_SHEET_ID` | Your Sheet ID from Step 1 |
| `INSTAGRAM_ACCESS_TOKEN` | Your Instagram token |
| `INSTAGRAM_ACCOUNT_ID` | `1108019899065402` |
| `TELEGRAM_CHAT_ID` | Your Chat ID from Step 2 |

---

## 📋 STEP 6 — Add Pinterest URLs

**Method 1 — Webhook (Recommended):**
```bash
curl -X POST https://YOUR_N8N_URL/webhook/add-pinterest-url \
  -H "Content-Type: application/json" \
  -d '{"pinterest_url": "https://pin.it/ABC123"}'
```

**Method 2 — Direct in Google Sheet:**
- Paste URL in column B
- Set Status = `PENDING` in column C
- Set Added_Date in column D

---

## 📋 STEP 7 — Activate Both Workflows

1. Open `Webhook - Add URL` workflow → Toggle **Active**
2. Open `Cron - 9AM 1PM 7PM IST` workflow → Toggle **Active**

---

## ⏰ Auto Schedule (IST Times)
| Cron | IST Time |
|---|---|
| `0 3 * * *` | 9:00 AM |
| `0 7 * * *` | 1:00 PM |
| `0 13 * * *` | 7:00 PM |

---

## 📊 Google Sheet Status Values
| Status | Meaning |
|---|---|
| `PENDING` | Waiting to be posted |
| `POSTED` | Successfully posted |
| `FAILED` | Error - will retry |

---

## 🔔 Telegram Notifications
**Success:** ✅ Post ID + Pinterest URL + Time
**Failure:** ❌ Error message + URL marked FAILED

---

## ⚠️ Important Notes
- Instagram token expires every 60 days — refresh regularly!
- Max 25 posts per 24 hours (Instagram limit)
- FAILED URLs can be reset to PENDING manually to retry
- Add unlimited URLs — system posts in order

---

## 🛠️ Troubleshooting

**"No PENDING URLs"** → Add more Pinterest URLs to queue

**"Host not in allowlist"** → Switch Facebook App to Live mode

**"Invalid token"** → Regenerate Instagram token in Graph API Explorer

**Image not posting** → Pinterest URL may have expired — add fresh URLs
