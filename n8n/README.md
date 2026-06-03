# Pinterest to Instagram - n8n Workflow

## 🚀 What This Does
Paste a Pinterest URL → AI analyzes image → Generates caption → Posts to Instagram automatically!

## 📋 Prerequisites
- n8n instance (cloud or self-hosted)
- OpenAI API key (GPT-4o)
- Instagram Business Account + Facebook Developer App

## ⚙️ Setup Steps

### Step 1 — Import Workflow
1. Open n8n
2. Click **+** → **Import from file**
3. Upload `n8n_workflow.json`

### Step 2 — Add n8n Variables
Go to **Settings → Variables** and add:

| Variable Name | Value |
|---|---|
| `INSTAGRAM_ACCESS_TOKEN` | Your Instagram token |
| `INSTAGRAM_ACCOUNT_ID` | `1108019899065402` |

### Step 3 — Add OpenAI Credential
1. Go to **Credentials → New**
2. Type: **HTTP Header Auth**
3. Name: `OpenAI API Key`
4. Header Name: `Authorization`
5. Header Value: `Bearer YOUR_OPENAI_API_KEY`

### Step 4 — Test It
**Manual Test:**
1. Open the workflow
2. In "Validate Input URL" node → edit line:
   `pinterestUrl = 'https://pin.it/YOUR_PIN_HERE';`
3. Click **Execute Workflow**

**Webhook Test:**
Send POST request:
```bash
curl -X POST https://YOUR_N8N_URL/webhook/pinterest-to-instagram \
  -H "Content-Type: application/json" \
  -d '{"pinterest_url": "https://pin.it/YOUR_PIN"}'
```

## 🔄 Workflow Steps
1. **Trigger** → Manual or Webhook with Pinterest URL
2. **Validate** → Check URL is valid
3. **Extract** → Get image from Pinterest oEmbed API
4. **Download** → Download highest quality image
5. **Upload** → Re-host image on public CDN
6. **AI Caption** → GPT-4o Vision analyzes & generates caption
7. **Post** → Create Instagram media container
8. **Wait** → 15 second processing delay
9. **Publish** → Publish to Instagram feed
10. **Log** → Record post details

## 🔐 Environment Variables
```
INSTAGRAM_ACCESS_TOKEN=your_token_here
INSTAGRAM_ACCOUNT_ID=your_account_id_here
OPENAI_API_KEY=sk-your-key-here
```

## ⚠️ Important Notes
- Instagram token expires every 60 days — refresh it!
- Max 25 posts per 24 hours (Instagram API limit)
- Image must be publicly accessible URL
- Minimum image size: 320x320px
