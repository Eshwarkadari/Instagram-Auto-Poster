# Step 3 — Deploy n8n FREE on Render

## Get Free Image Hosting (imgbb)
Instagram API needs public image URLs — imgbb gives free hosting.

1. Go to **https://api.imgbb.com**
2. Sign up free
3. Get your API key → save as `IMGBB_API_KEY`

## Deploy on Render

1. Go to **https://render.com** → sign up with GitHub
2. Click **New +** → **Web Service**
3. Connect your GitHub repo: `Instagram-Auto-Poster`
4. Settings:
   - Name: `instagram-auto-poster`
   - Root Directory: (leave empty)
   - Dockerfile Path: `render/Dockerfile`
   - Plan: **Free**
5. Add all Environment Variables:

| Key | Value |
|-----|-------|
| SHEET_ID | your sheet ID |
| GOOGLE_API_KEY | your google API key |
| FB_PAGE_ID | your page ID |
| FB_PAGE_ACCESS_TOKEN | your access token |
| IG_USER_ID | your instagram user ID |
| IMGBB_API_KEY | your imgbb key |
| N8N_BASIC_AUTH_ACTIVE | true |
| N8N_BASIC_AUTH_USER | admin |
| N8N_BASIC_AUTH_PASSWORD | choose a password |

6. Click **Create Web Service**
7. Wait 3-5 minutes for deployment
8. Your n8n URL: `https://instagram-auto-poster.onrender.com`

→ Proceed to `04_run.md`
