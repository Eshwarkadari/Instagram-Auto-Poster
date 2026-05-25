# Step 2 — Google Sheet Setup

## Create Your Sheet

1. Go to **https://sheets.google.com**
2. Create a new spreadsheet
3. Name it: `Instagram Auto Poster`

## Sheet Format

Set up Row 1 as headers exactly like this:

| A | B | C | D |
|---|---|---|---|
| **pinterest_url** | **description** | **status** | **posted_date** |

## Add Your Pinterest Links

From Row 2 onwards add your Pinterest links:

| pinterest_url | description | status | posted_date |
|---------------|-------------|--------|-------------|
| https://pin.it/abc123 | | pending | |
| https://pinterest.com/pin/123456 | Check this out! 🔥 | pending | |
| https://pin.it/xyz789 | | pending | |

**Rules:**
- Column A: Pinterest URL (required)
- Column B: Custom caption (optional — leave blank for auto-generated)
- Column C: Always write `pending` for new links
- Column D: Leave empty — automation fills this

## Get Your Sheet ID

From the URL: `https://docs.google.com/spreadsheets/d/`**COPY_THIS_PART**`/edit`

Save this as `SHEET_ID`

## Enable Google Sheets API

1. Go to **https://console.cloud.google.com**
2. Create new project → name: `Instagram Poster`
3. Go to **APIs & Services** → **Enable APIs**
4. Search **Google Sheets API** → Enable it
5. Go to **Credentials** → **Create Credentials** → **API Key**
6. Copy the API Key → save as `GOOGLE_API_KEY`

## Share Your Sheet

1. Click **Share** button in your sheet
2. Set to **Anyone with the link → Editor**
3. Click **Done**

---

## ✅ You should now have:
- `SHEET_ID` — your Google Sheet ID
- `GOOGLE_API_KEY` — your Google API key

→ Proceed to `03_n8n_setup.md`
