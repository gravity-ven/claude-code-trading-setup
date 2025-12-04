# How to Regenerate Gmail App Password

## Step-by-Step Guide for naga.kvv@gmail.com

### Step 1: Enable 2-Factor Authentication (Required)

1. Go to: https://myaccount.google.com/security
2. **IMPORTANT**: Log into **naga.kvv@gmail.com** (the account you want to send emails from)
3. Scroll to "2-Step Verification"
4. Click "Get Started"
5. Follow prompts to enable 2FA (you'll need your phone)
6. **Complete this before proceeding** - app passwords ONLY work with 2FA enabled

### Step 2: Generate App Password

1. Go to: https://myaccount.google.com/apppasswords
2. **Verify you're logged into naga.kvv@gmail.com** (check top-right corner)
3. Select:
   - **App**: Mail
   - **Device**: Other (Custom name) → Type "Nano Banana Cron"
4. Click "Generate"
5. **Copy the 16-character password** shown on screen
   - Format: `abcd efgh ijkl mnop`
   - Example display: Four groups of four characters with spaces
   - **Remove all spaces when using it**
   - Example for use: `abcdefghijklmnop`

### Step 3: Store Password Securely

**The password is shown ONLY ONCE.** Save it immediately.

### Step 4: Test with New Password

```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/scripts

# Export credentials with NEW password
export SENDER_EMAIL="naga.kvv@gmail.com"
export SENDER_PASSWORD="your_new_16_char_password"  # No spaces
export RECEIVER_EMAIL="naga.kvv@gmail.com"

# Test send
python3 nano_banana_daily_email.py
```

### Troubleshooting

**Error: "App passwords not available"**
- Solution: Enable 2FA first (Step 1)

**Error: "Username and Password not accepted"**
- Check you're logged into correct Gmail account
- Verify 2FA is enabled
- Make sure password has no spaces: `abcdefghijklmnop`
- Try regenerating the app password

**Can't find App Passwords option**
- Make sure 2FA is fully enabled and active
- Wait 5 minutes after enabling 2FA
- Try: https://security.google.com/settings/security/apppasswords

## Quick Verification

Before generating app password, verify:

1. ✓ Logged into naga.kvv@gmail.com (check Gmail top-right)
2. ✓ 2-Factor Authentication is enabled
3. ✓ Can access: https://myaccount.google.com/apppasswords

## After You Have New Password

Provide the new 16-character password (with spaces is fine, I'll remove them):

```
Example: abcd efgh ijkl mnop
```

Then I'll send the test email immediately.
