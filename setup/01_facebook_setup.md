# Step 1 — Facebook Developer App Setup

## 1. Create Facebook Developer Account
1. Go to **https://developers.facebook.com**
2. Click **"Get Started"**
3. Log in with your Facebook account
4. Verify your account

## 2. Create a New App
1. Click **"Create App"**
2. Select **"Business"** as app type
3. App name: `Instagram Auto Poster`
4. Contact email: your email
5. Click **"Create App"**

## 3. Add Instagram Graph API
1. In your app dashboard, click **"Add Product"**
2. Find **"Instagram Graph API"** → click **"Set Up"**

## 4. Add Your Facebook Page
1. Go to **App Settings → Basic**
2. Scroll down → **"Add Platform"** → **"Website"**
3. Add your website URL (or use `https://localhost`)

## 5. Get a Long-Lived Access Token
1. Go to **Tools → Graph API Explorer**
2. Select your app from dropdown
3. Click **"Generate Access Token"**
4. Check these permissions:
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`
   - ✅ `pages_read_engagement`
   - ✅ `pages_show_list`
5. Click **"Generate Access Token"**
6. Copy this token — you'll need it in n8n

## 6. Get Your Instagram Business Account ID
Run this in your browser (replace YOUR_TOKEN):
```
https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_TOKEN
```
Find your page ID, then:
```
https://graph.facebook.com/v18.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN
```
Copy the `id` value — this is your **Instagram Account ID**

## ✅ You now have:
- Facebook Access Token
- Instagram Account ID

→ Go to **Step 2: Instagram Setup**
