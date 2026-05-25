# Step 2 — Instagram API Setup

## Requirements
- Instagram account must be a **Business** or **Creator** account
- Must be connected to a **Facebook Page**

## Convert to Business Account (if not already)
1. Open Instagram app
2. Go to **Settings → Account**
3. Tap **"Switch to Professional Account"**
4. Choose **"Business"**
5. Connect to your Facebook Page

## Verify Connection
1. Go to your Facebook Page
2. Click **Settings → Instagram**
3. You should see your Instagram account connected

## Test Your Access Token
Open this URL in browser:
```
https://graph.facebook.com/v18.0/YOUR_INSTAGRAM_ACCOUNT_ID?fields=id,name,username&access_token=YOUR_ACCESS_TOKEN
```

You should see your Instagram username in the response.

## Important: Token Expiry
- Short-lived tokens expire in **1 hour**
- Long-lived tokens expire in **60 days**
- We will set up **automatic token refresh** in n8n

## ✅ You now have everything for Instagram posting!
→ Go to **Step 3: Google Sheet Setup**
