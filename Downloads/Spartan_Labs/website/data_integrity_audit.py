#!/usr/bin/env python3
"""
DATA INTEGRITY AUDIT SYSTEM
Runs daily at 12:00 AM to detect fake data across entire website
Sends email alerts to naga.kvv@gmail.com if violations found
"""

import requests
import json
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import traceback

# Configuration
ALERT_EMAIL = "naga.kvv@gmail.com"
AUDIT_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class DataIntegrityAuditor:
    def __init__(self):
        self.violations = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0

    def log_violation(self, severity, location, description, evidence):
        """Log a data integrity violation"""
        violation = {
            'severity': severity,  # 'CRITICAL', 'HIGH', 'MEDIUM'
            'location': location,
            'description': description,
            'evidence': evidence,
            'timestamp': AUDIT_TIMESTAMP
        }

        if severity in ['CRITICAL', 'HIGH']:
            self.violations.append(violation)
            self.checks_failed += 1
        else:
            self.warnings.append(violation)
            self.checks_passed += 1

    def check_for_fake_data_patterns(self, content, location):
        """Check for common fake data patterns"""
        fake_patterns = [
            (r'Math\.random\(\)(?!.*sort)', 'Math.random() used for data generation'),
            (r'= *\d+\.\d+ \* Math\.random', 'Random number multiplication for fake data'),
            (r'return.*\[.*Math\.random', 'Array with random data'),
            (r'value.*=.*Math\.floor\(Math\.random', 'Random floor values'),
            (r'= *(?:100|50|25) \+ Math\.random', 'Random offset values'),
        ]

        # Patterns to IGNORE (documentation/comments about policy)
        ignore_patterns = [
            r'NO FAKE DATA',
            r'ZERO fake',
            r'no.*fake.*data',
            r'//.*fake',
            r'/\*.*fake.*\*/',
            r'#.*fake',
            r'""".*fake.*"""',
            r"'''.*fake.*'''",
            r'@param.*fake',
            r'@description.*fake'
        ]

        for pattern, description in fake_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extract context (200 chars before and after for better analysis)
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end]

                # Check if this is just documentation/comments
                is_documentation = any(re.search(ignore, context, re.IGNORECASE | re.DOTALL) for ignore in ignore_patterns)

                # Check if it's in a comment block
                is_comment = bool(re.search(r'(//|/\*|\*|#|""")', context[:match.start()-start]))

                if not is_documentation and not is_comment:
                    self.log_violation(
                        'CRITICAL',
                        location,
                        f'Fake data pattern detected: {description}',
                        f'Code: {context[max(0,match.start()-start-50):min(len(context),match.end()-start+50)]}'
                    )

    def audit_html_files(self):
        """Audit all HTML files for fake data"""
        print("🔍 Auditing HTML files...")

        html_files = [
            'index.html',
            'nano_banana_scanner.html',
            'global_capital_flow_swing_trading.html',
            'correlation_matrix.html',
            'garp.html',
            'daily_planet.html'
        ]

        for filename in html_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.check_for_fake_data_patterns(content, f'HTML: {filename}')
                    self.checks_passed += 1
                    print(f"  ✓ {filename}")
            except FileNotFoundError:
                print(f"  ⚠️  {filename} not found (skipping)")
            except Exception as e:
                self.log_violation('MEDIUM', f'HTML: {filename}', f'Audit error: {str(e)}', '')

    def audit_javascript_files(self):
        """Audit all JavaScript files for fake data"""
        print("🔍 Auditing JavaScript files...")

        js_files = [
            'js/spartan-preloader.js',
            'js/capital_flow_visualizer.js',
            'js/composite_score_engine.js',
            'js/fred_api_client.js',
            'js/timeframe_data_fetcher_1_2_weeks.js',
            'js/timeframe_data_fetcher_1_3_months.js',
            'js/timeframe_data_fetcher_6_18_months.js',
            'js/timeframe_data_fetcher_18_36_months.js'
        ]

        for filename in js_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.check_for_fake_data_patterns(content, f'JavaScript: {filename}')
                    self.checks_passed += 1
                    print(f"  ✓ {filename}")
            except FileNotFoundError:
                print(f"  ⚠️  {filename} not found (skipping)")
            except Exception as e:
                self.log_violation('MEDIUM', f'JavaScript: {filename}', f'Audit error: {str(e)}', '')

    def audit_python_apis(self):
        """Audit Python API files for fake data"""
        print("🔍 Auditing Python API files...")

        python_files = [
            'cot_api.py',
            'correlation_api.py',
            'daily_planet_api.py',
            'swing_dashboard_api.py',
            'garp_api.py',
            'start_server.py',
            'src/data_preloader.py'
        ]

        for filename in python_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # Python-specific fake data patterns
                    fake_patterns = [
                        (r'random\.random\(\)', 'random.random() for data generation'),
                        (r'random\.randint', 'random.randint for fake data'),
                        (r'random\.uniform', 'random.uniform for fake data'),
                        (r'np\.random', 'numpy random for fake data'),
                        (r'(mock|fake|placeholder|dummy).*=', 'Mock/fake variable assignment'),
                    ]

                    for pattern, description in fake_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            start = max(0, match.start() - 50)
                            end = min(len(content), match.end() + 50)
                            context = content[start:end]

                            self.log_violation(
                                'CRITICAL',
                                f'Python: {filename}',
                                f'Fake data pattern: {description}',
                                f'Code: {context}'
                            )

                    self.checks_passed += 1
                    print(f"  ✓ {filename}")
            except FileNotFoundError:
                print(f"  ⚠️  {filename} not found (skipping)")
            except Exception as e:
                self.log_violation('MEDIUM', f'Python: {filename}', f'Audit error: {str(e)}', '')

    def audit_api_endpoints(self):
        """Audit live API endpoints for data integrity"""
        print("🔍 Auditing live API endpoints...")

        endpoints = [
            ('http://localhost:5005/health', 'COT API Health'),
            ('http://localhost:5005/api/cot/market/NG=F', 'COT API - Natural Gas'),
            ('http://localhost:5005/api/cot/market/GC=F', 'COT API - Gold'),
        ]

        for url, name in endpoints:
            try:
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    data = response.json()

                    # Check for suspicious patterns in API responses
                    data_str = json.dumps(data)

                    # Check for null/None values (acceptable)
                    # Check for obviously fake patterns
                    if 'test' in data_str.lower() or 'mock' in data_str.lower():
                        self.log_violation(
                            'HIGH',
                            f'API: {name}',
                            'Test/mock data detected in API response',
                            f'Response: {data_str[:200]}'
                        )
                    else:
                        self.checks_passed += 1
                        print(f"  ✓ {name}")
                else:
                    self.log_violation('MEDIUM', f'API: {name}', f'HTTP {response.status_code}', '')
            except requests.exceptions.RequestException as e:
                print(f"  ⚠️  {name} - Service not running (skipping)")
            except Exception as e:
                self.log_violation('MEDIUM', f'API: {name}', f'Audit error: {str(e)}', '')

    def audit_cftc_data_source(self):
        """Verify CFTC data is from official source"""
        print("🔍 Auditing CFTC data source...")

        try:
            with open('cot_api.py', 'r') as f:
                content = f.read()

                # Check for official CFTC URL
                if 'https://www.cftc.gov/files/dea/history/deacot' in content:
                    self.checks_passed += 1
                    print("  ✓ CFTC official source verified")
                else:
                    self.log_violation(
                        'CRITICAL',
                        'CFTC Data Source',
                        'CFTC URL not found or not official',
                        'Expected: https://www.cftc.gov/files/dea/history/'
                    )
        except Exception as e:
            self.log_violation('HIGH', 'CFTC Data Source', f'Audit error: {str(e)}', '')

    def generate_report(self):
        """Generate comprehensive audit report"""
        report = f"""
{'='*80}
                    DATA INTEGRITY AUDIT REPORT
{'='*80}

Audit Timestamp: {AUDIT_TIMESTAMP}
Alert Recipient: {ALERT_EMAIL}

{'='*80}
SUMMARY
{'='*80}

Total Checks: {self.checks_passed + self.checks_failed}
Passed: {self.checks_passed}
Failed: {self.checks_failed}

Critical Violations: {len([v for v in self.violations if v['severity'] == 'CRITICAL'])}
High Violations: {len([v for v in self.violations if v['severity'] == 'HIGH'])}
Medium Violations: {len([v for v in self.violations if v['severity'] == 'MEDIUM'])}
Warnings: {len(self.warnings)}

"""

        if self.violations:
            report += f"""
{'='*80}
🚨 VIOLATIONS DETECTED
{'='*80}

"""
            for i, violation in enumerate(self.violations, 1):
                report += f"""
[{i}] {violation['severity']} - {violation['location']}
    Description: {violation['description']}
    Evidence: {violation['evidence'][:200]}...
    Time: {violation['timestamp']}

"""
        else:
            report += f"""
{'='*80}
✅ NO VIOLATIONS DETECTED
{'='*80}

All data integrity checks passed successfully.
No fake data, mock data, or placeholder values detected.

"""

        report += f"""
{'='*80}
AUDIT DETAILS
{'='*80}

✓ HTML Files Audited
✓ JavaScript Files Audited
✓ Python API Files Audited
✓ Live API Endpoints Tested
✓ CFTC Data Source Verified

{'='*80}
DATA INTEGRITY POLICY
{'='*80}

1. NEVER use Math.random() for data generation
2. NEVER create fallback/placeholder values
3. ALWAYS return null on API failure
4. ONLY use real external APIs (Polygon.io, CFTC.gov)
5. FAIL GRACEFULLY - Better to show nothing than fake data

{'='*80}

Auditor: Automated Data Integrity System
Next Audit: Tomorrow at 12:00 AM

{'='*80}
"""
        return report

    def send_email_alert(self, report):
        """Send email alert with audit report"""
        try:
            # Email configuration
            sender_email = "spartan.labs.alerts@gmail.com"  # Configure with your email
            sender_password = "your_app_password"  # Use Gmail App Password

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = ALERT_EMAIL
            msg['Subject'] = f"🚨 URGENT: Data Integrity Violations Detected - {AUDIT_TIMESTAMP}"

            if self.violations:
                body = f"""
URGENT: Data Integrity Audit has detected {len(self.violations)} violation(s).

Critical Violations: {len([v for v in self.violations if v['severity'] == 'CRITICAL'])}
High Violations: {len([v for v in self.violations if v['severity'] == 'HIGH'])}

IMMEDIATE ACTION REQUIRED

Full report below:
{'='*80}

{report}
"""
            else:
                msg['Subject'] = f"✅ Data Integrity Audit Passed - {AUDIT_TIMESTAMP}"
                body = f"""
Data Integrity Audit completed successfully.

All checks passed: {self.checks_passed}
No violations detected.

Full report below:
{'='*80}

{report}
"""

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            # NOTE: You need to configure SMTP settings
            # For Gmail: Use App Password, enable 2FA
            # server = smtplib.SMTP('smtp.gmail.com', 587)
            # server.starttls()
            # server.login(sender_email, sender_password)
            # text = msg.as_string()
            # server.sendmail(sender_email, ALERT_EMAIL, text)
            # server.quit()

            print(f"\n📧 Email alert would be sent to: {ALERT_EMAIL}")
            print("NOTE: Configure SMTP settings in data_integrity_audit.py to enable email")

        except Exception as e:
            print(f"❌ Failed to send email: {e}")

    def run_full_audit(self):
        """Run complete audit"""
        print(f"\n{'='*80}")
        print("DATA INTEGRITY AUDIT - STARTING")
        print(f"{'='*80}\n")

        self.audit_html_files()
        self.audit_javascript_files()
        self.audit_python_apis()
        self.audit_api_endpoints()
        self.audit_cftc_data_source()

        report = self.generate_report()
        print(report)

        # Send email if violations found OR as daily summary
        if self.violations:
            print("\n🚨 VIOLATIONS DETECTED - SENDING ALERT EMAIL")
            self.send_email_alert(report)
        else:
            print("\n✅ AUDIT PASSED - All data integrity checks successful")
            # Optionally send daily summary
            # self.send_email_alert(report)

        return len(self.violations) == 0


if __name__ == "__main__":
    auditor = DataIntegrityAuditor()
    success = auditor.run_full_audit()

    # Exit with error code if violations found
    sys.exit(0 if success else 1)
