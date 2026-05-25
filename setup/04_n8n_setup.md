# Step 4 — Deploy n8n FREE on Render

## 1. Deploy n8n on Render (Free)
1. Go to **render.com** → Sign in with GitHub
2. Click **New + → Web Service**
3. Connect your `n8n-render` repo (you already have this!)
4. Settings:
   - Runtime: **Docker**
   - Image: `docker.io/n8nio/n8n:latest`
   - Plan: **Free**
5. Add Environment Variables:
   - `N8N_BASIC_AUTH_ACTIVE` = `true`
   - `N8N_BASIC_AUTH_USER` = `admin`
   - `N8N_BASIC_AUTH_PASSWORD` = `yourpassword`
   - `WEBHOOK_URL` = `https://your-app.onrender.com`
6. Click **Deploy**
7. Wait 3 minutes → you get a URL like `https://n8n-xxxx.onrender.com`

## 2. Open n8n
1. Go to your Render URL
2. Login with admin/yourpassword
3. You'll see the n8n editor

## 3. Add Credentials in n8n
Go to **Settings → Credentials → Add Credential**:

### Facebook/Instagram Credential
- Type: **HTTP Request** (Custom Auth)
- Name: `Instagram API`
- Header: `Authorization: Bearer YOUR_ACCESS_TOKEN`

### Google Sheets Credential  
- Type: **Google Sheets OAuth2**
- Paste your Service Account JSON

## 4. Import the Workflow
1. In n8n, click **"+"** → **"Import from file"**
2. Upload `n8n/workflow.json` from this repo
3. Update credentials in each node
4. Click **"Activate"** toggle (top right)

## ✅ Automation is now LIVE!
It will post 3 times daily automatically.
