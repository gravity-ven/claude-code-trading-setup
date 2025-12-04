# COT Daily Email Setup Guide

**Spartan Labs - CFTC Commitment of Traders Daily Report**

This guide walks you through setting up automated daily emails with COT (Commitment of Traders) infographics showing extreme positioning across 40+ futures markets.

---

## 📋 What You'll Get

Every day at your chosen time, you'll receive an email with:

- 📊 **Professional infographic** showing COT Index for 40+ futures (Bitcoin, Gold, Oil, S&P 500, etc.)
- 🔺 **Extreme LONG signals** (≥95%) - Commercials net long → Buy opportunities
- 🔻 **Extreme SHORT signals** (≤5%) - Commercials net short → Sell opportunities
- 📈 **Clear visual indicators** - Green bars (buy), Red bars (sell), Grey (neutral)

**Example**: If Natural Gas shows 100% COT Index, it means commercials are maximally long → contrarian BUY signal.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Create Gmail App Password (5 minutes)

**⚠️ CRITICAL**: You **CANNOT** use your regular Gmail password for SMTP. You **MUST** create an App Password.

1. **Go to Google Account Security**
   - Visit: https://myaccount.google.com/security
   - Or: Gmail → Profile Icon → "Manage your Google Account" → "Security"

2. **Enable 2-Step Verification** (if not already enabled)
   - Scroll down to "How you sign in to Google"
   - Click "2-Step Verification"
   - Follow the prompts to enable it (you'll need your phone)

3. **Create App Password**
   - In the search bar at the top, type: `App passwords`
   - Click "App passwords" in the results
   - You may be asked to sign in again
   - Select app: **Mail**
   - Select device: **Windows Computer** (or choose "Other" and name it "COT Emailer")
   - Click **Generate**

4. **Copy the 16-character password**
   - Google shows a 16-character password like: `abcd efgh ijkl mnop`
   - **Copy this exactly** (you can include or remove spaces, script handles both)
   - **SAVE THIS** - You'll need it in the next step

5. **Click "Done"**

---

### Step 2: Configure Email Settings

1. **Open the `.env` file**
   ```
   Windows: C:\Users\Quantum\Downloads\Spartan_Labs\website\.env
   Linux:   /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/.env
   ```

2. **Find the email configuration section** (around line 24):
   ```bash
   SMTP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD_HERE
   ```

3. **Replace with your App Password**:
   ```bash
   # Before:
   SMTP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD_HERE

   # After (remove spaces):
   SMTP_PASSWORD=abcdefghijklmnop
   ```

4. **Verify sender and recipient emails**:
   ```bash
   SMTP_USER=naga.kvv@gmail.com              # ✅ Already set
   COT_RECIPIENT_EMAIL=naga.kvv@gmail.com    # ✅ Already set
   ```

5. **Save the file**

---

### Step 3: Set Up Daily Automation

Choose your operating system:

#### **Option A: Windows (Task Scheduler)**

1. **Navigate to the website directory**:
   ```
   C:\Users\Quantum\Downloads\Spartan_Labs\website
   ```

2. **Right-click `SETUP_COT_DAILY_EMAIL.bat`**
   - Select **"Run as administrator"**

3. **Follow the prompts**:
   - It will ask for the time (default: 08:00 AM)
   - Enter your preferred time in 24-hour format (e.g., `14:30` for 2:30 PM)

4. **Done!** The task is now scheduled.

5. **Verify it worked**:
   - Press `Windows Key` + type `Task Scheduler`
   - Navigate to: **Task Scheduler Library**
   - Look for: **SpartanLabs_COT_Daily**
   - You should see it scheduled to run daily

---

#### **Option B: Linux/WSL (Cron)**

1. **Navigate to the website directory**:
   ```bash
   cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
   ```

2. **Run the setup script**:
   ```bash
   bash setup_cot_daily_email.sh
   ```

3. **Follow the prompts**:
   - It will ask for the time (default: 08:00 AM)
   - Enter your preferred time in 24-hour format (e.g., `14:30` for 2:30 PM)

4. **Done!** The cron job is now configured.

5. **Verify it worked**:
   ```bash
   crontab -l
   ```
   You should see an entry like:
   ```
   0 8 * * * /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/run_cot_daily.sh
   ```

---

## 🧪 Test the Setup

**Before waiting for the scheduled time**, test that everything works:

### Windows Test:
```cmd
cd C:\Users\Quantum\Downloads\Spartan_Labs\website
python cot_daily_emailer.py
```

### Linux/WSL Test:
```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
python3 cot_daily_emailer.py
```

**Expected Output**:
```
======================================================================
SPARTAN LABS - COT DAILY EMAILER
======================================================================
Date: 2025-11-24 12:34:56
Recipient: naga.kvv@gmail.com
Sender: naga.kvv@gmail.com
======================================================================

[1/3] Fetching COT data...
✅ Loaded 46 symbols

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

**Check your email**: You should receive the COT report at `naga.kvv@gmail.com`.

---

## 🔧 Troubleshooting

### ❌ "SMTP Authentication failed"

**Cause**: You're using your regular Gmail password instead of an App Password.

**Solution**:
1. Go back to **Step 1** and create an App Password
2. Update `.env` with the **16-character App Password** (not your regular password)
3. Test again

---

### ❌ "No module named 'matplotlib'"

**Cause**: Required Python packages not installed.

**Solution**:
```bash
# Windows:
pip install matplotlib pandas numpy requests python-dotenv

# Linux/WSL:
pip3 install matplotlib pandas numpy requests python-dotenv
```

---

### ❌ "SMTP_PASSWORD not set"

**Cause**: The `.env` file doesn't have the App Password configured.

**Solution**:
1. Open `.env` file
2. Find line: `SMTP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD_HERE`
3. Replace with your actual App Password
4. Save the file

---

### ❌ Email not arriving on schedule

**Windows**:
1. Open Task Scheduler
2. Find: **SpartanLabs_COT_Daily**
3. Right-click → **Run** (manual test)
4. Check "Last Run Result" column (should be 0x0 if successful)
5. If it failed, check the log file: `cot_daily_emailer.log`

**Linux/WSL**:
1. Check cron log:
   ```bash
   cat /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/cot_daily_cron.log
   ```
2. Verify cron is running:
   ```bash
   sudo service cron status
   ```
3. If not running:
   ```bash
   sudo service cron start
   ```

---

## 📊 Understanding COT Signals

### What is COT?

**COT (Commitment of Traders)** is a weekly report from the CFTC showing positioning of:
- **Commercial traders** (producers, hedgers, industry insiders) - "Smart Money"
- **Non-commercial traders** (speculators, hedge funds) - "Dumb Money"

### How to Read COT Index

The **COT Index** (0-100) shows commercial net positioning:

- **95-100%** = Commercials heavily NET LONG → **BUY SIGNAL** (contrarian)
- **0-5%** = Commercials heavily NET SHORT → **SELL SIGNAL** (contrarian)
- **6-94%** = Neutral positioning → No extreme signal

### Why It Works

Commercial traders are **industry insiders** with superior information:
- Gold miners hedge when they expect prices to RISE (buy gold forwards)
- Oil producers hedge when they expect prices to FALL (sell oil forwards)
- Airlines hedge jet fuel when they expect prices to RISE

When commercials are at **extremes**, they're positioning for a reversal:
- **Extreme long** (95%+) = They expect prices to rise → contrarian BUY
- **Extreme short** (5%-) = They expect prices to fall → contrarian SELL

### Example Trading Strategy

**Daily Email Shows**:
- Natural Gas: **100%** (Extreme Long) 🔺
- Sugar #11: **96%** (Extreme Long) 🔺
- 5-Year T-Note: **0%** (Extreme Short) 🔻
- Mexican Peso: **0%** (Extreme Short) 🔻

**Action**:
- Consider **LONG** positions in Natural Gas and Sugar (commercials bullish)
- Consider **SHORT** positions in 5-Year T-Note and Mexican Peso (commercials bearish)
- Use proper risk management (stop losses, position sizing)

---

## 📁 Files Created

After setup, you'll have:

```
Spartan_Labs/website/
├── cot_daily_emailer.py              # Main script
├── SETUP_COT_DAILY_EMAIL.bat         # Windows setup (Task Scheduler)
├── setup_cot_daily_email.sh          # Linux setup (Cron)
├── COT_DAILY_EMAIL_SETUP_GUIDE.md    # This guide
├── .env                               # Email credentials (updated)
├── cot_reports/                       # Generated infographics
│   └── COT_Report_2025-11-24.png
├── cot_daily_emailer.log             # Script execution log
└── run_cot_daily.sh                   # Cron wrapper (Linux only)
```

---

## 🔐 Security Notes

1. **Never commit `.env` to Git** - Contains your App Password
2. **App Password is safer than regular password** - Can be revoked anytime
3. **Revoke App Password if compromised**:
   - Go to: https://myaccount.google.com/security
   - Click "App passwords"
   - Click the trash icon next to the password
   - Generate a new one

---

## ⚙️ Advanced Configuration

### Change Email Time

**Windows**:
1. Open Task Scheduler
2. Right-click **SpartanLabs_COT_Daily** → **Properties**
3. Go to **Triggers** tab
4. Edit the trigger and change time
5. Click **OK**

**Linux/WSL**:
1. Edit cron:
   ```bash
   crontab -e
   ```
2. Change the time in the cron entry:
   ```
   # Format: MM HH * * * /path/to/script
   # Example: 14 30 * * * (runs at 2:30 PM)
   30 14 * * * /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/run_cot_daily.sh
   ```
3. Save and exit

### Send to Multiple Recipients

Edit `.env`:
```bash
# Single recipient (current):
COT_RECIPIENT_EMAIL=naga.kvv@gmail.com

# Multiple recipients (comma-separated):
COT_RECIPIENT_EMAIL=naga.kvv@gmail.com,other@email.com,another@email.com
```

### Disable Daily Email

**Windows**:
1. Open Task Scheduler
2. Right-click **SpartanLabs_COT_Daily** → **Disable**

**Linux/WSL**:
1. Remove cron job:
   ```bash
   crontab -e
   ```
2. Delete the line containing `run_cot_daily.sh`
3. Save and exit

---

## 📞 Support

**Issues**:
- Check logs: `cot_daily_emailer.log`
- Verify `.env` configuration
- Test manually: `python cot_daily_emailer.py`

**Email Not Sending**:
- Double-check App Password (not regular password!)
- Verify 2-Step Verification is enabled
- Try revoking and creating new App Password

**Cron Not Running (Linux)**:
- Check cron service: `sudo service cron status`
- View cron log: `cat cot_daily_cron.log`
- Verify cron entry: `crontab -l`

---

## ✅ Summary Checklist

- [ ] Created Gmail App Password (16 characters)
- [ ] Updated `.env` with `SMTP_PASSWORD`
- [ ] Ran setup script (Windows `.bat` or Linux `.sh`)
- [ ] Tested manually: `python cot_daily_emailer.py`
- [ ] Received test email successfully
- [ ] Verified scheduled task/cron job
- [ ] Set preferred daily email time

**You're all set!** 🎉

You'll now receive daily COT reports showing extreme positioning across 40+ futures markets.

---

**Last Updated**: November 24, 2025
**Version**: 1.0.0
**Author**: Spartan Labs
