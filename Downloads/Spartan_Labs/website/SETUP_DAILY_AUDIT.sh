#!/bin/bash
#
# SETUP DAILY DATA INTEGRITY AUDIT
# Runs at 12:00 AM every night
# Emails alerts to naga.kvv@gmail.com
#

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "                    DAILY DATA INTEGRITY AUDIT SETUP"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_SCRIPT="$SCRIPT_DIR/data_integrity_audit.py"

echo "📁 Script location: $SCRIPT_DIR"
echo "🔍 Audit script: $AUDIT_SCRIPT"
echo ""

# Make audit script executable
chmod +x "$AUDIT_SCRIPT"
echo "✓ Made audit script executable"

# Create cron job entry
CRON_CMD="0 0 * * * cd $SCRIPT_DIR && /usr/bin/python3 $AUDIT_SCRIPT >> $SCRIPT_DIR/audit_log.txt 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "data_integrity_audit.py"; then
    echo ""
    echo "⚠️  Cron job already exists. Updating..."
    # Remove old entry
    crontab -l 2>/dev/null | grep -v "data_integrity_audit.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✓ Cron job installed"
echo ""
echo "───────────────────────────────────────────────────────────────────────────────"
echo "📅 SCHEDULE CONFIGURED"
echo "───────────────────────────────────────────────────────────────────────────────"
echo ""
echo "  Time: 12:00 AM (Midnight) every day"
echo "  Script: $AUDIT_SCRIPT"
echo "  Logs: $SCRIPT_DIR/audit_log.txt"
echo "  Email: naga.kvv@gmail.com"
echo ""

# Show current crontab
echo "───────────────────────────────────────────────────────────────────────────────"
echo "📋 CURRENT CRON JOBS"
echo "───────────────────────────────────────────────────────────────────────────────"
echo ""
crontab -l | grep "data_integrity_audit.py"
echo ""

echo "───────────────────────────────────────────────────────────────────────────────"
echo "📧 EMAIL SETUP (REQUIRED)"
echo "───────────────────────────────────────────────────────────────────────────────"
echo ""
echo "To enable email alerts, configure SMTP settings in:"
echo "  $AUDIT_SCRIPT"
echo ""
echo "For Gmail (recommended):"
echo "  1. Enable 2-Factor Authentication on your Gmail account"
echo "  2. Generate App Password: https://myaccount.google.com/apppasswords"
echo "  3. Edit $AUDIT_SCRIPT"
echo "  4. Update these lines (around line 305):"
echo ""
echo "     sender_email = 'your_email@gmail.com'"
echo "     sender_password = 'your_16_char_app_password'"
echo ""
echo "  5. Uncomment SMTP lines (lines 319-324)"
echo ""

echo "───────────────────────────────────────────────────────────────────────────────"
echo "🧪 TEST THE AUDIT NOW"
echo "───────────────────────────────────────────────────────────────────────────────"
echo ""
echo "Run manually to test:"
echo "  cd $SCRIPT_DIR"
echo "  python3 data_integrity_audit.py"
echo ""

echo "───────────────────────────────────────────────────────────────────────────────"
echo "✅ SETUP COMPLETE"
echo "───────────────────────────────────────────────────────────────────────────────"
echo ""
echo "The audit will run automatically at midnight every day."
echo "Configure email settings above to receive alerts."
echo ""
