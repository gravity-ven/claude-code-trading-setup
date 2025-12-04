#!/usr/bin/env python3
"""
Claude Computer Use Visual Monitor
Uses Claude's computer use API to visually inspect and fix the website
"""

import anthropic
import os
import time
import subprocess
import base64
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/claude_computer_use_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ClaudeComputerUseMonitor:
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.website_url = os.environ.get('WEBSITE_URL', 'http://spartan_web:8888')
        self.check_interval = int(os.environ.get('CHECK_INTERVAL', '300'))  # 5 minutes
        self.screenshot_dir = Path('/app/screenshots')
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Claude Computer Use Monitor initialized")
        logger.info(f"Monitoring URL: {self.website_url}")
        logger.info(f"Check interval: {self.check_interval}s")

    def take_screenshot(self, page, name="screenshot"):
        """Take a screenshot of the current page"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.screenshot_dir / f"{name}_{timestamp}.png"
        page.screenshot(path=str(filepath), full_page=True)
        logger.info(f"📸 Screenshot saved: {filepath}")
        return filepath

    def screenshot_to_base64(self, filepath):
        """Convert screenshot to base64 for Claude API"""
        with open(filepath, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def analyze_with_claude(self, screenshot_base64, html_content):
        """Send screenshot and HTML to Claude for analysis"""
        logger.info("🤖 Analyzing with Claude...")

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""Analyze this Spartan Research Station trading dashboard screenshot.

HTML Content (first 5000 chars):
{html_content[:5000]}

**Your Task:**
1. Identify ALL visual errors, broken elements, or "Error" text
2. Check if data is displaying correctly (prices, charts, indicators)
3. Look for layout issues, missing images, or broken UI components
4. Verify all sections are loading properly

**Output Format (JSON):**
{{
  "status": "healthy" | "warning" | "critical",
  "issues_found": [
    {{
      "severity": "critical" | "warning" | "info",
      "component": "name of component with issue",
      "description": "what's wrong",
      "suggested_fix": "how to fix it"
    }}
  ],
  "overall_assessment": "brief summary"
}}

Be thorough - scan the entire page for ANY issues."""
                        }
                    ]
                }]
            )

            analysis = message.content[0].text
            logger.info(f"Claude analysis complete: {len(analysis)} chars")
            return analysis

        except Exception as e:
            logger.error(f"❌ Claude API error: {e}")
            return None

    def execute_fix(self, fix_description):
        """Execute autonomous fix based on Claude's suggestion"""
        logger.warning(f"🔧 AUTONOMOUS FIX: {fix_description}")

        # Map fix descriptions to actions
        fix_actions = {
            "restart web server": lambda: subprocess.run(['docker', 'restart', 'spartan_web']),
            "clear redis cache": lambda: subprocess.run(['docker', 'exec', 'spartan_redis', 'redis-cli', 'FLUSHDB']),
            "reset database": lambda: self.reset_database_connections(),
            "rebuild frontend": lambda: subprocess.run(['docker', 'restart', 'spartan_web']),
        }

        # Try to match fix description to action
        for keyword, action in fix_actions.items():
            if keyword.lower() in fix_description.lower():
                logger.info(f"Executing fix action: {keyword}")
                try:
                    action()
                    logger.info(f"✅ Fix executed successfully: {keyword}")
                    return True
                except Exception as e:
                    logger.error(f"❌ Fix failed: {e}")
                    return False

        logger.warning(f"⚠️  No automated fix available for: {fix_description}")
        return False

    def reset_database_connections(self):
        """Reset PostgreSQL database connections"""
        try:
            subprocess.run([
                'docker', 'exec', 'spartan_postgres', 'psql',
                '-U', 'spartan_user', '-d', 'spartan_research',
                '-c', "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'spartan_research' AND pid <> pg_backend_pid();"
            ], capture_output=True, timeout=10)
            logger.info("✅ Database connections reset")
            return True
        except Exception as e:
            logger.error(f"❌ Database reset failed: {e}")
            return False

    def visual_health_check(self):
        """Perform visual health check using Playwright and Claude"""
        logger.info("="*70)
        logger.info(f"VISUAL HEALTH CHECK - {datetime.now().strftime('%H:%M:%S')}")
        logger.info("="*70)

        try:
            with sync_playwright() as p:
                # Launch browser
                logger.info("🌐 Launching browser...")
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = context.new_page()

                # Navigate to website
                logger.info(f"📡 Loading {self.website_url}...")
                page.goto(self.website_url, wait_until='networkidle', timeout=30000)

                # Wait for key elements
                logger.info("⏳ Waiting for content to load...")
                page.wait_for_timeout(5000)  # Give dynamic content time to load

                # Take screenshot
                screenshot_path = self.take_screenshot(page, "health_check")

                # Get HTML content
                html_content = page.content()

                # Get console errors
                console_errors = []
                page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)

                browser.close()

                # Convert screenshot to base64
                screenshot_base64 = self.screenshot_to_base64(screenshot_path)

                # Analyze with Claude
                analysis = self.analyze_with_claude(screenshot_base64, html_content)

                if analysis:
                    logger.info("📊 ANALYSIS RESULTS:")
                    logger.info(analysis)

                    # Parse analysis and execute fixes (simplified - would parse JSON in production)
                    if "critical" in analysis.lower() or "error" in analysis.lower():
                        logger.warning("🚨 CRITICAL ISSUES DETECTED - Triggering auto-fix...")

                        # Example auto-fix logic
                        if "database" in analysis.lower() or "transaction" in analysis.lower():
                            self.execute_fix("restart web server")
                            time.sleep(10)  # Wait for restart
                            # Re-check
                            self.visual_health_check()
                        elif "cache" in analysis.lower() or "stale" in analysis.lower():
                            self.execute_fix("clear redis cache")
                    else:
                        logger.info("✅ WEBSITE HEALTH: GOOD")
                else:
                    logger.error("❌ Claude analysis failed")

        except Exception as e:
            logger.error(f"❌ Visual health check failed: {e}")
            # Auto-fix: Restart web server on check failure
            logger.warning("🔧 AUTO-FIX: Health check failed, restarting web server...")
            self.execute_fix("restart web server")

    def monitor_loop(self):
        """Continuous monitoring loop"""
        logger.info("="*70)
        logger.info("CLAUDE COMPUTER USE MONITOR - STARTED")
        logger.info("="*70)

        check_count = 0

        while True:
            check_count += 1
            logger.info(f"\n{'='*70}")
            logger.info(f"Visual Check #{check_count} at {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"{'='*70}\n")

            try:
                self.visual_health_check()
            except Exception as e:
                logger.error(f"❌ Monitor loop error: {e}")

            logger.info(f"\n💤 Sleeping for {self.check_interval} seconds...\n")
            time.sleep(self.check_interval)


if __name__ == "__main__":
    monitor = ClaudeComputerUseMonitor()
    monitor.monitor_loop()
