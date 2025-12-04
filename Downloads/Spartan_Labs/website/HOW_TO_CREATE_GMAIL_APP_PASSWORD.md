# How to Create Gmail App Password (Step-by-Step with Screenshots)

**Time Required:** 5 minutes
**Gmail Account:** naga.kvv@gmail.com

---

## 🎯 What is an App Password?

An **App Password** is a 16-character passcode that lets apps (like your COT emailer) send emails through Gmail **without** using your regular password.

**Why you need it:**
- Gmail blocks regular passwords for security
- App Passwords are safer (can be revoked anytime)
- Required for SMTP email sending

---

## 📋 Step-by-Step Instructions

### **Step 1: Open Google Account Security**

**Option A - Direct Link (Fastest):**
```
https://myaccount.google.com/security
```
Just click this link and it will take you directly to the security page.

**Option B - Manual Navigation:**
1. Open Gmail: https://mail.google.com
2. Click your **Profile Picture** (top right corner)
3. Click **"Manage your Google Account"**
4. Click **"Security"** tab on the left

---

### **Step 2: Enable 2-Step Verification (Required)**

**⚠️ IMPORTANT:** You MUST enable 2-Step Verification before you can create App Passwords.

1. **Scroll down** to the section: **"How you sign in to Google"**

2. Look for: **"2-Step Verification"**

3. **Check the status:**
   - ✅ If it says **"On"** → Skip to Step 3
   - ❌ If it says **"Off"** → Continue below

4. **Click "2-Step Verification"**

5. Click **"Get Started"** (blue button)

6. **Follow the prompts:**
   - Enter your password
   - Enter your phone number
   - Choose how to get codes (Text message or Phone call)
   - Enter the 6-digit code you receive
   - Click **"Turn On"**

7. ✅ 2-Step Verification is now **ON**

---

### **Step 3: Create App Password**

1. **Go back to Security page:**
   ```
   https://myaccount.google.com/security
   ```

2. **Use the search bar** at the top of the page:
   - Click the **search icon** (🔍) or search box at the top
   - Type: `App passwords`
   - Click **"App passwords"** in the results

   **Screenshot guide:**
   ```
   ┌─────────────────────────────────────────┐
   │ 🔍 Search Google Account                │
   │                                          │
   │ > App passwords                          │  ← Type this
   └─────────────────────────────────────────┘
   ```

3. **You may be asked to sign in again** (for security)
   - Enter your Gmail password
   - Click **"Next"**

4. **You'll see the App Passwords page:**
   ```
   ┌─────────────────────────────────────────────────┐
   │ App passwords                                    │
   │                                                   │
   │ Give apps access to your Google Account         │
   │                                                   │
   │ App name: [                    ] [Create]        │
   └─────────────────────────────────────────────────┘
   ```

5. **Enter app name:**
   - In the text box, type: `COT Emailer` (or any name you like)
   - Click **"Create"** button

6. **Google generates a 16-character password:**
   ```
   ┌─────────────────────────────────────────────────┐
   │ Your App password for your device                │
   │                                                   │
   │  abcd efgh ijkl mnop         [Copy] 📋          │
   │                                                   │
   │  You won't be able to see this code again.      │
   │  Save it somewhere secure.                       │
   │                                                   │
   │                              [Done]               │
   └─────────────────────────────────────────────────┘
   ```

7. **CRITICAL - COPY THIS PASSWORD:**
   - Click the **Copy button** (📋) OR
   - **Write it down exactly** (you can include or exclude spaces)
   - Example password: `abcd efgh ijkl mnop`

8. Click **"Done"**

---

## ✅ You Now Have Your App Password!

**Example of what you copied:**
```
abcd efgh ijkl mnop
```

OR (spaces removed):
```
abcdefghijklmnop
```

**Both formats work!** The script removes spaces automatically.

---

## 🔧 Now Update Your .env File

### **Step 4: Open .env File**

**Windows:**
```
1. Open File Explorer
2. Navigate to: C:\Users\Quantum\Downloads\Spartan_Labs\website
3. Right-click ".env"
4. Select "Open with" → "Notepad"
```

**Linux/WSL:**
```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
nano .env
```

### **Step 5: Update SMTP_PASSWORD**

1. **Find line 24** (or search for `SMTP_PASSWORD`):
   ```bash
   SMTP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD_HERE
   ```

2. **Replace with your App Password:**
   ```bash
   # BEFORE:
   SMTP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD_HERE

   # AFTER (you can include or remove spaces):
   SMTP_PASSWORD=abcdefghijklmnop
   ```

3. **Save the file:**
   - Windows Notepad: `Ctrl + S`
   - Nano (Linux): `Ctrl + O`, `Enter`, `Ctrl + X`

---

## 🧪 Test It Now!

**Run the COT emailer:**

**Windows Command Prompt:**
```cmd
cd C:\Users\Quantum\Downloads\Spartan_Labs\website
python cot_daily_emailer.py
```

**Linux/WSL Terminal:**
```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
python3 cot_daily_emailer.py
```

**Expected Output:**
```
======================================================================
SPARTAN LABS - COT DAILY EMAILER
======================================================================
Date: 2025-11-24 12:34:56
Recipient: naga.kvv@gmail.com
Sender: naga.kvv@gmail.com
======================================================================

[1/3] Fetching COT data...
✅ Loaded 49 symbols

[2/3] Generating infographic...
✅ Infographic saved: cot_reports/COT_Report_2025-11-24.png

[3/3] Sending email...
Connecting to smtp.gmail.com:587...
Logging in to Gmail...
Sending message...
✅ Email sent successfully!

======================================================================
✅ COT DAILY REPORT SENT SUCCESSFULLY!
======================================================================
```

**Check your email:** Go to naga.kvv@gmail.com and look for the COT report!

---

## ❌ Troubleshooting

### Problem: "Can't find App passwords option"

**Solution:**
1. Make sure you're signed into: naga.kvv@gmail.com
2. Verify 2-Step Verification is **ON** (required!)
3. Try this direct link: https://myaccount.google.com/apppasswords

---

### Problem: "SMTP Authentication failed"

**Common causes:**
1. ❌ You used your **regular Gmail password** instead of App Password
2. ❌ You didn't remove spaces from App Password in .env
3. ❌ You didn't save the .env file after editing

**Solution:**
1. Create a NEW App Password (delete old one if needed)
2. Update .env with the new password (remove all spaces)
3. Save the file
4. Test again: `python cot_daily_emailer.py`

---

### Problem: "App passwords option is grayed out"

**Causes:**
- 2-Step Verification is not enabled
- You're using a work/school Google account (admin restrictions)

**Solution:**
1. Enable 2-Step Verification first
2. If using work account, contact your admin

---

### Problem: "Where did my App Password go?"

**After clicking "Done", you can't see it again!**

**Solution:**
1. Go back to App passwords page
2. **Delete** the old password:
   - Click the **trash icon** (🗑️) next to "COT Emailer"
3. **Create a new one** (follow Step 3 again)
4. **Copy it immediately** this time

---

## 🔐 Security Tips

### ✅ Good Practices:
- App Passwords are SAFER than regular passwords
- Each app gets its own password
- You can revoke App Passwords anytime
- Doesn't give access to your entire Google account

### 🚨 Keep Secure:
- Don't share your App Password
- Don't commit .env file to GitHub
- If compromised, revoke it immediately

### 🗑️ How to Revoke an App Password:
1. Go to: https://myaccount.google.com/apppasswords
2. Find the app password (e.g., "COT Emailer")
3. Click the **trash icon** (🗑️)
4. Click **"Remove"**
5. The password is immediately disabled

---

## 📸 Visual Guide (What You'll See)

### **Screen 1: Google Account Security**
```
┌───────────────────────────────────────────────────────┐
│  Google Account                                        │
│  ┌─────┬─────┬─────┬─────┐                           │
│  │ Home│ Data│Secur│ More│                            │
│  └─────┴─────┴─────┴─────┘                           │
│                                                        │
│  How you sign in to Google                            │
│  ┌──────────────────────────────────────────┐        │
│  │ 2-Step Verification            ON   >    │        │
│  └──────────────────────────────────────────┘        │
│                                                        │
└───────────────────────────────────────────────────────┘
```

### **Screen 2: App Passwords Page**
```
┌───────────────────────────────────────────────────────┐
│  App passwords                                         │
│                                                        │
│  Give apps access to your Google Account              │
│                                                        │
│  App name: [COT Emailer          ] [Create]           │
│                                                        │
│  Your app passwords:                                   │
│  COT Emailer                            🗑️            │
│  Created Nov 24, 2025                                  │
└───────────────────────────────────────────────────────┘
```

### **Screen 3: Generated Password**
```
┌───────────────────────────────────────────────────────┐
│  Your App password for your device                     │
│                                                        │
│  ┌──────────────────────────────────────┐            │
│  │  abcd efgh ijkl mnop      [Copy] 📋 │            │
│  └──────────────────────────────────────┘            │
│                                                        │
│  You won't be able to see this code again.            │
│  Save it somewhere secure.                             │
│                                                        │
│                                      [Done]            │
└───────────────────────────────────────────────────────┘
```

---

## ✅ Quick Checklist

Complete these steps in order:

- [ ] Opened: https://myaccount.google.com/security
- [ ] Enabled 2-Step Verification (if wasn't on)
- [ ] Searched for "App passwords"
- [ ] Clicked "App passwords" in results
- [ ] Signed in again (if prompted)
- [ ] Typed app name: "COT Emailer"
- [ ] Clicked "Create"
- [ ] **COPIED** the 16-character password
- [ ] Clicked "Done"
- [ ] Opened .env file
- [ ] Updated SMTP_PASSWORD line
- [ ] Saved .env file
- [ ] Ran: python cot_daily_emailer.py
- [ ] ✅ Received email at naga.kvv@gmail.com

---

## 🎉 Success!

Once you complete all steps and see:
```
✅ Email sent successfully!
```

**You're done!** Now run the setup script to automate daily emails:

**Windows:**
```cmd
Right-click: SETUP_COT_DAILY_EMAIL.bat
Select: "Run as administrator"
```

**Linux/WSL:**
```bash
bash setup_cot_daily_email.sh
```

---

## 📞 Still Need Help?

**Can't find App passwords option?**
- Make sure 2-Step Verification is ON
- Try direct link: https://myaccount.google.com/apppasswords
- Clear browser cache and try again

**Authentication still failing?**
- Delete the App Password and create a new one
- Make sure you're editing the RIGHT .env file:
  ```
  C:\Users\Quantum\Downloads\Spartan_Labs\website\.env
  ```
- Verify no extra spaces before or after the password

**Email not arriving?**
- Check spam folder
- Verify sender email: naga.kvv@gmail.com
- Make sure Gmail isn't blocking it

---

**Last Updated:** November 24, 2025
**For:** COT Daily Emailer Setup
