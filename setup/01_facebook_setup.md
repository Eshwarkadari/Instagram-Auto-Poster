# Step 1 — Facebook & Instagram API Setup

## What You Need
- Facebook Developer Account
- Instagram Business Account linked to Facebook Page
- Facebook App with correct permissions

---

## Step 1.1 — Create Facebook Developer Account
1. Go to **https://developers.facebook.com**
2. Click **Get Started** → log in with Facebook
3. Verify your account with phone number

## Step 1.2 — Create a Facebook App
1. Go to **https://developers.facebook.com/apps**
2. Click **Create App**
3. Select **Business** type
4. App name: `Instagram Auto Poster`
5. Click **Create App**

## Step 1.3 — Add Instagram Graph API
1. In your app dashboard → click **Add Product**
2. Find **Instagram Graph API** → click **Set Up**

## Step 1.4 — Get Your Page Access Token
1. Go to **https://developers.facebook.com/tools/explorer**
2. Select your App from dropdown
3. Select your **Facebook Page** (not personal profile)
4. Under Permissions add:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
   - `pages_show_list`
5. Click **Generate Access Token** → approve all permissions
6. Copy this token → save as `FB_PAGE_ACCESS_TOKEN`

## Step 1.5 — Get Your Facebook Page ID
1. Go to your Facebook Page
2. Click **About** → scroll down
3. Find **Page ID** → copy it → save as `FB_PAGE_ID`

## Step 1.6 — Get Your Instagram Business Account ID
Run this in browser (replace YOUR_PAGE_ID and YOUR_TOKEN):
```
https://graph.facebook.com/v18.0/YOUR_PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN
```
Copy the `id` value → save as `IG_USER_ID`

## Step 1.7 — Get Long-Lived Token (stays valid 60 days)
```
https://graph.facebook.com/v18.0/oauth/access_token?
  grant_type=fb_exchange_token&
  client_id=YOUR_APP_ID&
  client_secret=YOUR_APP_SECRET&
  fb_exchange_token=YOUR_SHORT_TOKEN
```

---

## ✅ You should now have:
- `FB_PAGE_ID` — your Facebook Page ID
- `FB_PAGE_ACCESS_TOKEN` — long-lived access token
- `IG_USER_ID` — Instagram Business Account ID

→ Proceed to `02_google_sheet.md`
