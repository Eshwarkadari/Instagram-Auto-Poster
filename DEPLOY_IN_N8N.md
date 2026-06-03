# 🚀 DEPLOY IN YOUR EXISTING N8N - STEP BY STEP

You already have n8n running. Here's exactly what to do to activate the Pinterest-to-Instagram automation.

---

## 📋 WHAT YOU HAVE

In your GitHub `/n8n` folder:
```
✅ complete-pinterest-instagram-workflow.json  ← USE THIS ONE
✅ pinterest_instagram_workflow.json           (alternative)
✅ workflow.json                               (alternative)
✅ SETUP_GUIDE.md                              (instructions)
✅ NODE_CONFIGURATION_REFERENCE.md             (node details)
```

---

## 🎯 YOUR EXACT STEPS

### STEP 1: Download the Main Workflow File

```
Go to: https://github.com/Eshwarkadari/Instagram-Auto-Poster/tree/main/n8n

Click on: complete-pinterest-instagram-workflow.json

Click: Download (or Raw → Right-click → Save As)

Save to your computer as: complete-pinterest-instagram-workflow.json
```

---

### STEP 2: Open Your n8n Dashboard

```
Open your n8n instance:
- If cloud: https://app.n8n.cloud
- If self-hosted: Your n8n URL (e.g., http://localhost:5678)

Login with your credentials
```

---

### STEP 3: Import the Workflow

```
In n8n:
1. Click: Workflows (left sidebar)
2. Click: + New (or New Workflow button)
3. Click: Import from file (if you see this option)
   OR
   Click: ⋮ (three dots) → Import from file

Select the downloaded file: complete-pinterest-instagram-workflow.json

Click: Import / Open
```

---

### STEP 4: Wait for Load

```
⏳ Workflow will load in 20-30 seconds

You should see:
- Large workflow diagram
- 26 nodes connected
- All nodes with green checkmarks
```

---

### STEP 5: Add Google Sheets Credential (IMPORTANT)

```
Left sidebar → Credentials

Click: + New

Search: Google Sheets

Select: Google Sheets OAuth2 (NOT service account)

Click: Authenticate with Google
  - Login with your Google account
  - Accept permissions
  - Should show: "Successfully authenticated"

Name it: Google Sheets API

Click: Save
```

---

### STEP 6: Verify Node Configuration

```
In the workflow, find the node: "Read Google Sheet"

Double-click it

Verify:
  ✅ Authentication: Google Sheets API (dropdown)
  ✅ Document ID: 15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960
  ✅ Sheet Name: Sheet1
  ✅ Range: A:F

If different, update to above values

Click: Save Node
```

---

### STEP 7: Test the Workflow (Manual)

```
In the workflow:

Find node: "Trigger - Schedule Daily Posts"

Click the node (select it)

Look for: Execute button (▶️ or play icon)

Click: Execute

Watch the workflow run in real-time:
  - Nodes turn blue as they execute
  - Should complete in 30-60 seconds
  - No errors should appear
```

---

### STEP 8: Verify Test Results

```
After test execution, check 3 places:

1️⃣ INSTAGRAM
   Go to: https://www.instagram.com
   Login to your account
   Check: Does your feed have a NEW POST? ✅

2️⃣ GOOGLE SHEET
   Go to: https://docs.google.com/spreadsheets/d/15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960/edit
   Check first row with URL:
   - Column B (Status): Should now be POSTED (was PENDING)
   - Column D (Posted_Date): Should show current date & time
   - Column E (Instagram_Post_ID): Should have a number

3️⃣ TELEGRAM
   Open Telegram app
   Check your messages
   Should see: ✅ Posted Successfully
               Pinterest URL: ...
               Instagram Post ID: ...
```

---

### STEP 9: Activate Automation

```
Top RIGHT corner of the workflow:

Find: Active toggle (should be OFF - gray)

Click: Toggle it ON (will turn GREEN)

A message appears: "Workflow activated"

✅ DONE! Automation is now LIVE
```

---

## ⏰ WHAT HAPPENS NOW

```
Every day, AUTOMATICALLY:

🕘 09:00 AM UTC
   • System reads Google Sheet
   • Finds first URL with Status=PENDING
   • Downloads image from Pinterest
   • Posts to Instagram
   • Updates Google Sheet
   • Sends Telegram notification

🕐 01:00 PM UTC
   • (Repeat above with next URL)

🕖 07:00 PM UTC
   • (Repeat above with next URL)

Next day → Cycle repeats with next 3 URLs
```

---

## 📱 ADD MORE PINTEREST URLS (Anytime)

```
Open your Google Sheet:
https://docs.google.com/spreadsheets/d/15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960/edit

Column A: Paste Pinterest URL
  Example: https://pin.it/abc123

Column B: Type: PENDING

Click: Save

System will automatically post it in next cycle!
```

---

## ✅ VERIFICATION CHECKLIST

After activation, verify everything works:

- [ ] Workflow shows "Active" (green toggle)
- [ ] Manual test execution completed successfully
- [ ] New post appeared on Instagram
- [ ] Google Sheet Status changed to POSTED
- [ ] Posted_Date filled with timestamp
- [ ] Instagram_Post_ID shows in column E
- [ ] Telegram notification received
- [ ] No error messages in n8n

**All checked? ✅ You're done!**

---

## 🐛 TROUBLESHOOTING

### Problem: Workflow won't import
**Solution:**
- Make sure file is: `complete-pinterest-instagram-workflow.json`
- Try: Menu → Import Workflow → Select file
- File might be corrupted, re-download from GitHub

### Problem: Google Sheets credential fails
**Solution:**
- Make sure you're authorizing with correct Google account
- Account must have edit access to the sheet
- Try removing credential and creating new one

### Problem: Manual test runs but nothing happens
**Solution:**
1. Check error messages in n8n (red nodes)
2. Click on red node to see error
3. Usually: Wrong credential or wrong sheet ID
4. Fix and re-test

### Problem: Instagram post not appearing
**Solution:**
- Account must be Business account (not Personal)
- Token might be expired (>60 days old)
- Check n8n Executions tab for error
- Verify Instagram Account ID: 967454269255245

### Problem: Telegram not sending
**Solution:**
- Open Telegram and check notifications are enabled
- Make sure you didn't block notifications
- Chat ID is hardcoded: 7446081188
- Check Telegram account is active

### Problem: Google Sheet not updating
**Solution:**
- Refresh the sheet (F5)
- Make sure Google Sheets credential is authorized
- Check n8n Executions for errors
- Try re-authorizing credential

---

## 🎯 DAILY OPERATION

After activation:

```
✅ You: Just add Pinterest URLs to Google Sheet

✅ System: Automatically:
   • Posts 3 times per day
   • Never posts same URL twice
   • Updates Google Sheet with Status & ID
   • Sends Telegram notifications
   • Retries failed posts

✅ Result: 3 new Instagram posts daily, forever
```

---

## 📊 Monitor Your Automation

### Check in n8n:
```
Left sidebar → Executions

You should see:
- 3 successful executions per day
- Each one shows:
  • Time executed
  • Status: Success ✅
  • Duration: ~2-3 minutes
```

### Check in Google Sheet:
```
Columns you'll see filling:
- Column B (Status): PENDING → POSTED
- Column D (Posted_Date): Auto-filled timestamp
- Column E (Instagram_Post_ID): Instagram ID number
```

### Check on Instagram:
```
Your feed should show:
- 3 new posts per day
- Each post has fixed caption:
  "🔥 Men's Fashion Inspiration..."
- All automated
```

### Check in Telegram:
```
You'll receive:
- 3 notifications per day
- Each says:
  ✅ Posted Successfully
  Pinterest URL: ...
  Instagram Post ID: ...
```

---

## 🔄 REFRESH INSTAGRAM TOKEN (Every 60 Days)

Instagram tokens expire every 60 days.

When it expires:
```
1. Go to: https://developers.facebook.com/

2. Apps → Select your app

3. Instagram Basic Display → Settings

4. Generate new Long-Lived Access Token

5. Copy the token

6. In n8n:
   Find node: "Prepare Instagram Upload"
   Double-click
   Update the token value
   Save

7. Test again to verify
```

---

## 🎉 YOU'RE DONE!

Your Instagram will now:
```
✅ Post 3 times daily automatically
✅ Never post same URL twice
✅ Track everything in Google Sheet
✅ Notify you via Telegram
✅ Work forever with zero manual work
```

---

## 📞 SUMMARY

### What just happened:
1. ✅ Imported complete workflow
2. ✅ Added Google Sheets credential
3. ✅ Tested manually (everything worked)
4. ✅ Activated automation
5. ✅ Instagram posts 3x daily from now on

### What you do going forward:
- Add Pinterest URLs to Google Sheet (Column A)
- System automatically posts them
- That's it!

### Time invested:
- 15 minutes to setup
- 0 minutes per day ongoing

---

## 🚀 NEXT: Add Your First URLs

Open Google Sheet:
https://docs.google.com/spreadsheets/d/15jDXVQTA7mjc9vWkF134EGWGvmvdNrzchNsjdSbN960/edit

Add 5-10 Pinterest URLs to Column A with Status=PENDING

Next automated run (09:00 AM, 01:00 PM, or 07:00 PM UTC):
- System picks first PENDING URL
- Downloads image
- Posts to Instagram
- Updates sheet
- Sends Telegram notification

Done! ✅
