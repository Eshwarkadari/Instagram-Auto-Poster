# Step 3 — Google Sheet Setup

## 1. Create the Google Sheet
1. Go to **sheets.google.com**
2. Create a new sheet
3. Name it: `Instagram Auto Poster`

## 2. Set Up Columns (Row 1 = Headers)
Copy these exact headers into Row 1:

| A | B | C | D | E |
|---|---|---|---|---|
| pinterest_url | description | status | posted_date | post_id |

## 3. Add Your Pinterest Links
From Row 2 onwards, add your links:

| pinterest_url | description | status | posted_date | post_id |
|---|---|---|---|---|
| https://pin.it/abc123 | Amazing sunset view! #nature | pending | | |
| https://pin.it/xyz456 | | pending | | |
| https://www.pinterest.com/pin/123456 | | pending | | |

**Tips:**
- Leave `description` empty = auto caption generated
- Always set `status` to `pending` for new links
- You can add 100+ links — automation picks 3 per day

## 4. Share the Sheet
1. Click **Share** button (top right)
2. Change to **"Anyone with the link"**
3. Set permission to **"Editor"**
4. Copy the link

## 5. Get the Sheet ID
From the URL:
```
https://docs.google.com/spreadsheets/d/SHEET_ID_IS_HERE/edit
```
Copy the long ID between `/d/` and `/edit`

## 6. Set Up Google Sheets API
1. Go to **console.cloud.google.com**
2. Create a new project: `Instagram Poster`
3. Enable **Google Sheets API**
4. Go to **Credentials → Create Credentials → Service Account**
5. Name: `instagram-poster`
6. Download the **JSON key file**
7. Share your Google Sheet with the service account email

## ✅ You now have:
- Google Sheet ID
- Google Service Account JSON

→ Go to **Step 4: n8n Setup**
