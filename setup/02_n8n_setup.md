# Step 2 — Deploy n8n FREE on Render + Import Workflow

## 1. Deploy n8n on Render
1. Go to **render.com** → sign in with GitHub
2. Click **New + → Web Service**
3. Connect your `n8n-render` GitHub repo
4. Settings:
   - Runtime: **Docker**
   - Image URL: `docker.io/n8nio/n8n:latest`
   - Plan: **Free**
5. Click **Deploy** → wait 3 minutes

## 2. Add Environment Variables in Render
Go to your Render service → **Environment** tab → Add:

| Key | Value |
|-----|-------|
| `N8N_BASIC_AUTH_ACTIVE` | `true` |
| `N8N_BASIC_AUTH_USER` | `admin` |
| `N8N_BASIC_AUTH_PASSWORD` | `choose a password` |
| `INSTAGRAM_ACCOUNT_ID` | your Instagram account ID |
| `FACEBOOK_ACCESS_TOKEN` | your Facebook access token |
| `GITHUB_TOKEN` | new GitHub token (repo scope only) |
| `GITHUB_REPO` | `Eshwarkadari/Instagram-Auto-Poster` |

Click **Save Changes** → service restarts

## 3. Open n8n
Go to your Render URL (e.g. `https://n8n-xxxx.onrender.com`)
Login with admin + your password

## 4. Import Workflow
1. Click **+** → **Import from file**
2. Upload `n8n/workflow.json` from this repo
3. Click **Save**
4. Click **Activate** toggle (top right) → turns green ✅

## 5. Test It
Click **Execute Workflow** button to test manually.
Check your Instagram — post should appear! 📸

## ✅ Automation is LIVE!
Every 8 hours it will:
1. Read 3 links from `links.txt`
2. Download from Pinterest
3. Post to Instagram
4. Remove posted links from `links.txt`
