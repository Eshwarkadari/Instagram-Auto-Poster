# Step 4 — Import Workflow & Go Live!

## Import n8n Workflow

1. Open your n8n URL: `https://instagram-auto-poster.onrender.com`
2. Log in with admin / your password
3. Click **+** → **Import from File**
4. Upload `n8n/workflow.json` from this repo
5. Click **Save**

## Activate the Workflow

1. Open the workflow
2. Toggle the switch to **Active** (top right)
3. The automation will now run at:
   - **9:00 AM IST** (3:00 UTC)
   - **1:00 PM IST** (7:00 UTC)
   - **6:00 PM IST** (12:00 UTC)

## Test Manually

1. In n8n, open the workflow
2. Click **Execute Workflow** (play button)
3. Watch it run in real time!
4. Check your Google Sheet — posted links will show `posted` status
5. Check your Instagram page — post should appear!

## Add More Pinterest Links

Just add more rows to your Google Sheet with `status = pending`.
The automation picks the next 3 pending links each time it runs.

---

## 🎉 You're Live!

Your Instagram page will now get:
- 3 posts every day automatically
- AI-generated captions with hashtags
- Content sourced from your Pinterest links
- Status tracking in Google Sheet

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No posts appearing | Check FB_PAGE_ACCESS_TOKEN is valid |
| Sheet not reading | Check SHEET_ID and GOOGLE_API_KEY |
| Download failing | Try different Pinterest URL format |
| Token expired | Refresh long-lived token (valid 60 days) |
