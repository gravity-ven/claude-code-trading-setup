# Nano Banana Daily Email - Setup Guide

## Overview

This cron job sends a daily contrarian trading report at **08:01 AM** with:
- Bitcoin market regime analysis
- Crowded long/short positions (funding rates)
- CFTC Commitment of Traders data
- Contrarian trade opportunities

**Smart Features:**
- ✅ Runs at 08:01 AM daily
- ✅ Catches up on missed runs (if computer was off)
- ✅ Runs on boot with 60-second delay
- ✅ Prevents duplicate runs on same day
- ✅ Comprehensive logging

---

## Prerequisites

### 1. Python Dependencies

```bash
# If using virtual environment (recommended)
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install required packages
pip install pandas pandas_ta requests
```

### 2. Gmail App Password (REQUIRED)

**You CANNOT use your regular Gmail password for automated scripts. You must generate an App Password.**

#### Step-by-Step: Create Gmail App Password

1. **Enable 2-Factor Authentication**:
   - Go to: https://myaccount.google.com/security
   - Scroll to "2-Step Verification"
   - Click "Get Started" and follow the prompts
   - **Important**: App Passwords only work if 2FA is enabled

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Or: Google Account → Security → App Passwords
   - Select app: **Mail**
   - Select device: **Other (Custom name)** → Type "Nano Banana Cron"
   - Click **Generate**
   - **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)
   - Remove spaces: `abcdefghijklmnop`

3. **Store Securely**:
   - This password is shown only once
   - Save it in a password manager or secure note
   - You'll need it for the next step

---

## Installation

### Step 1: Make Setup Script Executable

```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/scripts
chmod +x setup_nano_banana_cron.sh
chmod +x nano_banana_daily_email.py
```

### Step 2: Configure Environment Variables

**Option A: Temporary (for testing)**

```bash
export SENDER_EMAIL="your_email@gmail.com"
export SENDER_PASSWORD="abcdefghijklmnop"  # Your 16-char app password
export RECEIVER_EMAIL="naga.kvv@gmail.com"
```

**Option B: Permanent (recommended)**

Add to `~/.bashrc` (Linux/WSL) or `~/.zshrc` (macOS):

```bash
# Nano Banana Email Configuration
export SENDER_EMAIL="your_email@gmail.com"
export SENDER_PASSWORD="abcdefghijklmnop"  # Gmail App Password
export RECEIVER_EMAIL="naga.kvv@gmail.com"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

**Option C: .env File (alternative)**

Create `.env` in the `website` directory:

```bash
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=abcdefghijklmnop
RECEIVER_EMAIL=naga.kvv@gmail.com
```

Then modify the Python script to load from .env:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Step 3: Run Setup Script

```bash
./setup_nano_banana_cron.sh
```

**What it does:**
- ✅ Checks dependencies
- ✅ Creates wrapper script with catch-up logic
- ✅ Installs cron job (08:01 AM + on boot)
- ✅ Validates installation
- ✅ Offers test run

**Expected output:**
```
========================================
  Nano Banana Daily Email Cron Setup
========================================
✓ Made script executable
✓ Using virtual environment: /path/to/venv/bin/python3
✓ All dependencies installed
✓ Created logs directory
✓ Created wrapper script
✓ Cron job installed successfully!
✓ Cron job verified in crontab

         Setup Complete!
========================================
```

### Step 4: Verify Installation

```bash
# Check cron job is installed
crontab -l | grep nano_banana

# Should show:
# 1 8 * * * /path/to/nano_banana_wrapper.sh >> /path/to/logs/nano_banana_cron.log 2>&1
# @reboot sleep 60 && /path/to/nano_banana_wrapper.sh >> /path/to/logs/nano_banana_cron.log 2>&1
```

---

## Testing

### Test Immediate Run

```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/scripts
./nano_banana_wrapper.sh
```

**Check results:**

```bash
# View cron log
tail -f ../logs/nano_banana_cron.log

# View detailed script log
tail -f ../logs/nano_banana_$(date +%Y%m).log
```

**Successful output example:**
```
2025-11-24 08:01:00 - INFO - Starting Nano Banana Daily Report Generation
2025-11-24 08:01:02 - INFO - Fetching Binance funding rates...
2025-11-24 08:01:03 - INFO - Retrieved funding data for 150 symbols
2025-11-24 08:01:04 - INFO - Checking regime for BTCUSDT...
2025-11-24 08:01:05 - INFO - BTCUSDT regime: 🟢 BULL REGIME (Buy Dips)
2025-11-24 08:01:06 - INFO - Fetching CFTC COT data...
2025-11-24 08:01:10 - INFO - COT data downloaded: 5000 records
2025-11-24 08:01:11 - INFO - Sending email to naga.kvv@gmail.com...
2025-11-24 08:01:13 - INFO - ✅ Email sent successfully!
```

---

## Schedule Details

### Daily Run
- **Time**: 08:01 AM (local system time)
- **Cron Expression**: `1 8 * * *`
- **What happens**: Sends email if not already sent today

### Boot Catch-Up Run
- **Trigger**: System boot/startup
- **Delay**: 60 seconds (allows network to initialize)
- **Logic**: Only runs if today's email hasn't been sent yet

### Duplicate Prevention
- State file: `/logs/.last_run_nano_banana`
- Stores date of last successful run
- Prevents multiple emails on same day
- Resets automatically at midnight

---

## Maintenance

### View Logs

```bash
# Cron execution log
tail -f /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/nano_banana_cron.log

# Detailed script log (monthly rotation)
tail -f /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/nano_banana_202511.log
```

### Manual Test Run

```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/scripts
./nano_banana_wrapper.sh
```

### Edit Cron Schedule

```bash
# Open crontab editor
crontab -e

# Change time (example: 07:30 AM instead of 08:01 AM)
# Change: 1 8 * * *
# To:     30 7 * * *

# Save and exit
```

### Remove Cron Job

```bash
# Edit crontab
crontab -e

# Delete lines containing "nano_banana_wrapper.sh"
# Save and exit

# Or remove all cron jobs (careful!)
crontab -r
```

### Update Script

If you modify the Python script:

```bash
# No need to reinstall cron job, just restart cron service (optional)
# The cron job will automatically use the updated script

# On Linux/WSL:
sudo service cron restart

# On macOS:
# Cron automatically picks up changes
```

---

## Troubleshooting

### Email Not Sending

**1. Check environment variables:**
```bash
echo $SENDER_EMAIL
echo $SENDER_PASSWORD
echo $RECEIVER_EMAIL
```

**2. Check Gmail App Password:**
- Make sure it's the 16-character app password (no spaces)
- NOT your regular Gmail password
- 2FA must be enabled on Gmail account

**3. Check logs:**
```bash
tail -50 /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/nano_banana_*.log
```

**Common errors:**
- `smtplib.SMTPAuthenticationError` → Wrong app password
- `SENDER_PASSWORD not set` → Environment variable not configured
- `Crypto funding fetch error` → Network issue, try again

### Cron Job Not Running

**1. Check if cron service is running:**
```bash
# Linux/WSL:
sudo service cron status

# macOS:
sudo launchctl list | grep cron
```

**2. Check cron job exists:**
```bash
crontab -l | grep nano_banana
```

**3. Check system time:**
```bash
date
# Make sure it matches your timezone
```

**4. Test wrapper script manually:**
```bash
./nano_banana_wrapper.sh
# Check for errors
```

### Data Fetch Failures

**1. Binance API issues:**
- Check https://www.binance.com/en/futures/funding-history/perpetual
- Verify internet connection
- Binance may have rate limits (script handles this)

**2. CFTC COT data issues:**
- COT data updates weekly (Friday)
- URL might need year adjustment (2025 → 2026)
- Edit script: Change `deacot2025.zip` to `deacot2026.zip`

**3. Network timeout:**
- Increase timeout in script (default: 10s for most calls)
- Check firewall settings

---

## Customization

### Change Email Time

Edit crontab:
```bash
crontab -e

# Current: 1 8 * * * (08:01 AM)
# Change to 07:30 AM: 30 7 * * *
# Change to 09:00 AM: 0 9 * * *
```

### Add More Recipients

Edit `nano_banana_daily_email.py`:
```python
RECEIVER_EMAIL = "naga.kvv@gmail.com,another@email.com"
```

Or use BCC:
```python
msg["Bcc"] = "additional@email.com"
```

### Change Symbols

Edit the `check_regime_crypto()` function:
```python
# Add Ethereum regime check
eth_regime, eth_price, eth_line = check_regime_crypto("ETHUSDT")
```

### Adjust Crowded Trade Threshold

Edit `get_crypto_funding()`:
```python
# Show top 10 instead of 5
crowded_longs = df.sort_values(by='fundingRate', ascending=False).head(10)
crowded_shorts = df.sort_values(by='fundingRate', ascending=True).head(10)
```

---

## Security Notes

1. **Never commit App Password to git**:
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use environment variables** (preferred over .env file in production)

3. **Restrict log file permissions**:
   ```bash
   chmod 600 /path/to/logs/*.log
   ```

4. **Rotate Gmail App Passwords periodically** (every 6-12 months)

---

## Advanced: Systemd Timer (Alternative to Cron)

For more reliable scheduling with automatic catch-up:

### Create Service File

`/etc/systemd/system/nano-banana.service`:
```ini
[Unit]
Description=Nano Banana Daily Email
After=network-online.target

[Service]
Type=oneshot
User=your_username
Environment="SENDER_EMAIL=your_email@gmail.com"
Environment="SENDER_PASSWORD=your_app_password"
Environment="RECEIVER_EMAIL=naga.kvv@gmail.com"
ExecStart=/path/to/venv/bin/python3 /path/to/nano_banana_daily_email.py
StandardOutput=journal
StandardError=journal
```

### Create Timer File

`/etc/systemd/system/nano-banana.timer`:
```ini
[Unit]
Description=Nano Banana Daily Email Timer

[Timer]
OnCalendar=08:01:00
Persistent=true
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
```

### Enable Timer

```bash
sudo systemctl daemon-reload
sudo systemctl enable nano-banana.timer
sudo systemctl start nano-banana.timer

# Check status
sudo systemctl status nano-banana.timer
sudo systemctl list-timers --all | grep nano-banana
```

**Benefits of systemd timer:**
- `Persistent=true` → Runs missed jobs on boot
- Better logging (journalctl)
- More precise scheduling
- Easier to monitor

---

## Support

### Check Script Status

```bash
# Last 20 lines of main log
tail -20 /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/nano_banana_$(date +%Y%m).log

# Check if email sent today
cat /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/.last_run_nano_banana
```

### Force Run (Ignore State)

```bash
# Temporarily delete state file
rm /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/.last_run_nano_banana

# Run wrapper
./nano_banana_wrapper.sh
```

### Debug Mode

Add to Python script:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose logs
```

---

## Summary

**What you need:**
1. Gmail App Password (16 characters)
2. Environment variables set (SENDER_EMAIL, SENDER_PASSWORD)
3. Run `./setup_nano_banana_cron.sh`

**What you get:**
- Daily email at 08:01 AM
- Automatic catch-up if computer was off
- No duplicate emails on same day
- Comprehensive logging
- Contrarian trade opportunities

**Commands:**
```bash
# Setup
./setup_nano_banana_cron.sh

# Test
./nano_banana_wrapper.sh

# Monitor
tail -f ../logs/nano_banana_cron.log

# Remove
crontab -e  # Delete nano_banana lines
```

---

**Ready to Trade Contrarian? 🍌**
