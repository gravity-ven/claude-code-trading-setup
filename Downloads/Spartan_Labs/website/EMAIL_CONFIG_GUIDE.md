# 📧 EMAIL ALERT CONFIGURATION GUIDE

## Quick Setup (Gmail - Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow the setup wizard

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select app: "Mail"
3. Select device: "Other" (name it "Spartan Audit")
4. Click "Generate"
5. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

### Step 3: Configure the Audit Script
Edit `data_integrity_audit.py` (around line 305):

```python
# BEFORE (lines 304-305):
sender_email = "spartan.labs.alerts@gmail.com"  # Configure with your email
sender_password = "your_app_password"  # Use Gmail App Password

# AFTER:
sender_email = "your_email@gmail.com"  # Your Gmail address
sender_password = "abcd efgh ijkl mnop"  # Your 16-char App Password
```

### Step 4: Uncomment SMTP Lines
Uncomment lines 319-324 in `data_integrity_audit.py`:

```python
# BEFORE (commented):
# server = smtplib.SMTP('smtp.gmail.com', 587)
# server.starttls()
# server.login(sender_email, sender_password)
# text = msg.as_string()
# server.sendmail(sender_email, ALERT_EMAIL, text)
# server.quit()

# AFTER (uncommented):
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(sender_email, sender_password)
text = msg.as_string()
server.sendmail(sender_email, ALERT_EMAIL, text)
server.quit()
```

### Step 5: Test Email
```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
python3 data_integrity_audit.py
```

You should receive an email at: **naga.kvv@gmail.com**

---

## Alternative: Using SendGrid (Production-Grade)

### Step 1: Create SendGrid Account
1. Go to: https://sendgrid.com/
2. Sign up for free tier (100 emails/day)
3. Verify your email
4. Create API Key: Settings → API Keys → Create API Key

### Step 2: Install SendGrid
```bash
pip install sendgrid
```

### Step 3: Update Audit Script
Replace email section in `data_integrity_audit.py`:

```python
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

def send_email_alert(self, report):
    sg = sendgrid.SendGridAPIClient(api_key='YOUR_SENDGRID_API_KEY')

    from_email = Email("alerts@spartanlabs.com")
    to_email = To("naga.kvv@gmail.com")
    subject = f"🚨 Data Integrity Alert - {AUDIT_TIMESTAMP}"
    content = Content("text/plain", report)

    mail = Mail(from_email, to_email, subject, content)
    response = sg.client.mail.send.post(request_body=mail.get())

    print(f"Email sent: {response.status_code}")
```

---

## Email Alert Triggers

The audit system will email you when:

✅ **Daily Summary** (optional):
- Runs every day at 12:00 AM
- Shows all checks passed
- Summary report

🚨 **Immediate Alerts** (critical):
- Fake data detected (`Math.random()` for data)
- Mock/placeholder values found
- API returning test data
- CFTC source URL changed
- Fallback data generation detected

---

## Email Content Example

### Subject Line:
```
🚨 URGENT: Data Integrity Violations Detected - 2025-11-24 00:00:00
```

### Body:
```
URGENT: Data Integrity Audit has detected 3 violation(s).

Critical Violations: 2
High Violations: 1

IMMEDIATE ACTION REQUIRED

Full report below:
================================================================================

DATA INTEGRITY AUDIT REPORT
================================================================================

[1] CRITICAL - JavaScript: capital_flow_visualizer.js
    Description: Fake data pattern detected: Math.random() used for data generation
    Evidence: const fakeData = Math.random() * 100;
    Time: 2025-11-24 00:00:00

[2] CRITICAL - HTML: index.html
    Description: Fake data pattern detected: Random number multiplication
    Evidence: value = 50 * Math.random();
    Time: 2025-11-24 00:00:00

[3] HIGH - API: COT API - Natural Gas
    Description: Test/mock data detected in API response
    Evidence: Response: {"status": "ok", "data": "test_data"}
    Time: 2025-11-24 00:00:00

================================================================================
```

---

## Troubleshooting

### Gmail: "Less secure app access"
- **Solution**: Use App Password (not your regular password)
- Enable 2FA first, then generate App Password

### Gmail: "Authentication failed"
- **Check**: Email and password are correct
- **Check**: App Password has no spaces
- **Check**: 2FA is enabled

### No email received
- **Check spam folder**
- **Check**: Email is configured correctly
- **Test**: Run script manually and check console output

### Script running but no audit
- **Check cron logs**: `cat audit_log.txt`
- **Check cron service**: `systemctl status cron`
- **Test manually**: `python3 data_integrity_audit.py`

---

## Security Notes

⚠️ **NEVER commit email credentials to Git**

Add to `.gitignore`:
```
*_config.py
.env
audit_log.txt
```

✅ **Best Practice**: Use environment variables
```python
import os

sender_email = os.getenv('AUDIT_EMAIL')
sender_password = os.getenv('AUDIT_PASSWORD')
```

---

## Support

If you need help configuring email alerts:
1. Check Gmail App Password setup
2. Verify SMTP settings are uncommented
3. Test manually before relying on cron
4. Check `audit_log.txt` for errors

---

**Last Updated**: November 24, 2025
**Contact**: naga.kvv@gmail.com
**System**: Spartan Labs Data Integrity Audit
