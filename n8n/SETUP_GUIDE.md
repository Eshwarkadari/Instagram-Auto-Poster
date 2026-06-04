# Pinterest → Instagram Auto Poster
## Google Sheets Queue System — Complete Setup Guide

---

## 🎯 How It Works
1. You add Pinterest URLs to Google Sheet with Status = PENDING
2. Every day at 9AM, 2PM, 7PM IST — workflow runs automatically
3. Picks first PENDING URL → downloads image → posts to Instagram
4. Updates Status to POSTED → sends Telegram notification
5. Never posts same URL twice!

---

## 📋 STEP 1 — Google Sheet Setup

Your sheet ID: `15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960`

Make sure Row 1 has EXACTLY these headers:
```
Pinterest_URL | Status
```

To add URLs — just paste in column A, set column B = PENDING

Example:
```
Pinterest_URL                          | Status
https://pin.it/abc123                  | PENDING
https://in.pinterest.com/pin/xyz456/   | PENDING
```

---

## 📋 STEP 2 — Import Workflow into n8n

1. Open your n8n instance
2. Click **+** → **Import from file** or **Import from URL**
3. Import: `n8n/workflow_gsheets.json` from your GitHub repo

Or use raw URL:
```
https://raw.githubusercontent.com/Eshwarkadari/Instagram-Auto-Poster/main/n8n/workflow_gsheets.json
```

---

## 📋 STEP 3 — Connect Google Sheets in n8n

1. Go to **Credentials → New**
2. Select **Google Sheets OAuth2 API**
3. Name it exactly: `Google Sheets OAuth2`
4. Click **Connect** → Sign in with your Google account
5. Allow permissions

---

## 📋 STEP 4 — Connect Telegram in n8n

1. Go to **Credentials → New**
2. Select **Telegram**
3. Name it exactly: `Telegram Bot`
4. Enter your Bot Token (from @BotFather)
5. Save

Your Chat ID is already set: `7446081188`

---

## 📋 STEP 5 — Activate the Workflow

1. Open the imported workflow in n8n
2. Toggle the **Active** switch ON
3. Done! It will run automatically at 9AM, 2PM, 7PM IST

---

## 📋 STEP 6 — Test Manually

1. Open workflow in n8n
2. Click **Execute Workflow** button
3. Check your Instagram for the new post
4. Check Telegram for notification
5. Check Google Sheet — Status should change to POSTED

---

## ⏰ Auto Schedule (IST Times)
| Cron | UTC | IST |
|------|-----|-----|
| `0 3 * * *` | 3:00 AM UTC | 8:30 AM IST |
| `0 8 * * *` | 8:00 AM UTC | 1:30 PM IST |
| `0 13 * * *` | 1:00 PM UTC | 6:30 PM IST |

---

## 📊 Google Sheet Status Values
| Status | Meaning |
|--------|---------|
| `PENDING` | Waiting to be posted |
| `POSTED` | Successfully posted ✅ |
| `FAILED` | Error occurred — change back to PENDING to retry |

---

## 🔔 Telegram Notifications
**Success message:**
```
✅ Posted to Instagram!
🔗 Pinterest: https://pin.it/...
📸 Post ID: 17846...
🕐 Time: 2026-06-01 09:00:00
📊 Queue left: 15 URLs
```

**Failure message:**
```
❌ Post Failed!
🔗 URL: https://pin.it/...
⚠️ Error: ...
🔄 Change Status to PENDING in sheet to retry
```

---

## ➕ How To Add More Pinterest URLs
Just open your Google Sheet and add:
- Column A: Pinterest URL
- Column B: PENDING

That's it! System picks them automatically in order.

---

## ⚠️ Important Notes
- Instagram token expires every **60 days** — regenerate when needed
- Max **25 posts per 24 hours** (Instagram API limit)
- If a post FAILS → change Status back to PENDING in sheet to retry
- Keep adding URLs to never run out of content!

---

## 🛠️ Credentials Summary
| Item | Value |
|------|-------|
| Google Sheet ID | `15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960` |
| Instagram Account ID | `967454269255245` |
| Telegram Chat ID | `7446081188` |
| Instagram Posts/Day | 3 |
| Schedule | 9AM, 2PM, 7PM IST |
