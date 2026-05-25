# Step 1 — Get Facebook Access Token & Instagram Account ID

## 1. Create Facebook Developer App
1. Go to **https://developers.facebook.com**
2. Click **My Apps → Create App**
3. Select **Business** → Next
4. App name: `Instagram Auto Poster` → Create

## 2. Add Instagram Graph API Product
1. In app dashboard → **Add Product**
2. Find **Instagram Graph API** → Set Up

## 3. Get Your Access Token
1. Go to **Tools → Graph API Explorer**
2. Select your app from the top dropdown
3. Click **Generate Access Token**
4. Select these permissions:
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`
   - ✅ `pages_read_engagement`
   - ✅ `pages_show_list`
5. Click **Generate Access Token** → Copy it

## 4. Get Long-Lived Token (60 days)
Paste this URL in browser (replace values):
```
https://graph.facebook.com/v18.0/oauth/access_token?
  grant_type=fb_exchange_token&
  client_id=YOUR_APP_ID&
  client_secret=YOUR_APP_SECRET&
  fb_exchange_token=YOUR_SHORT_TOKEN
```
Copy the new `access_token` from response.

## 5. Get Your Instagram Account ID
Paste in browser:
```
https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_TOKEN
```
Copy your `id` (page ID), then:
```
https://graph.facebook.com/v18.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN
```
Copy the `id` inside `instagram_business_account` — this is your **INSTAGRAM_ACCOUNT_ID**

## ✅ You now have:
- `FACEBOOK_ACCESS_TOKEN`
- `INSTAGRAM_ACCOUNT_ID`

→ Go to Step 2: n8n Setup
