#!/usr/bin/env python3
"""
Spartan Research Station - Page Inspector
Systematically checks all HTML pages for data loading issues
Waits at least 1 minute per page as requested
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

BASE_URL = "http://localhost:8888"
WAIT_TIME = 60  # seconds - wait at least 1 minute per page
SCREENSHOT_DIR = Path("screenshots_inspection")
SCREENSHOT_DIR.mkdir(exist_ok=True)

async def inspect_page(page, html_file, page_num, total_pages):
    """Inspect a single page for data loading"""
    url = f"{BASE_URL}/{html_file}"
    result = {
        "file": html_file,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "errors": [],
        "warnings": [],
        "data_loaded": False,
        "api_calls": [],
        "console_errors": [],
    }

    try:
        print(f"\n{'='*80}")
        print(f"[{page_num}/{total_pages}] Inspecting: {html_file}")
        print(f"URL: {url}")
        print(f"{'='*80}")

        # Track console errors
        page.on("console", lambda msg:
            result["console_errors"].append({
                "type": msg.type,
                "text": msg.text
            }) if msg.type in ["error", "warning"] else None
        )

        # Track network requests (API calls)
        def handle_response(response):
            if "/api/" in response.url:
                result["api_calls"].append({
                    "url": response.url,
                    "status": response.status,
                    "ok": response.ok
                })

        page.on("response", handle_response)

        # Navigate to page
        print(f"Loading page...")
        response = await page.goto(url, wait_until="networkidle", timeout=30000)

        if response.status != 200:
            result["status"] = f"HTTP {response.status}"
            result["errors"].append(f"Page returned status {response.status}")
            print(f"❌ ERROR: HTTP {response.status}")
            return result

        print(f"✅ Page loaded (HTTP {response.status})")

        # Wait for initial page load
        await asyncio.sleep(5)

        # Check for loading indicators
        loading_selectors = [
            '.loading',
            '.spinner',
            '[data-loading="true"]',
            '.data-loading',
            '.skeleton'
        ]

        print(f"Checking for loading indicators...")
        for selector in loading_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"  Found {len(elements)} loading indicators: {selector}")

        # Wait for the requested 1 minute
        print(f"Waiting {WAIT_TIME} seconds for data to load (as requested)...")
        for i in range(WAIT_TIME // 10):
            await asyncio.sleep(10)
            elapsed = (i + 1) * 10
            print(f"  {elapsed}/{WAIT_TIME} seconds elapsed...")

        # Check for error messages
        error_selectors = [
            '.error',
            '.error-message',
            '[data-error]',
            '.alert-danger'
        ]

        print(f"Checking for error messages...")
        for selector in error_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                for elem in elements:
                    error_text = await elem.inner_text()
                    if error_text.strip():
                        result["errors"].append(f"Error message found: {error_text[:100]}")
                        print(f"  ❌ Error: {error_text[:100]}")

        # Check for data tables/charts
        data_selectors = [
            'table',
            '.chart',
            'canvas',
            '[data-symbol]',
            '.data-value',
            '.market-data'
        ]

        print(f"Checking for data elements...")
        data_element_count = 0
        for selector in data_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                data_element_count += len(elements)
                print(f"  Found {len(elements)} elements: {selector}")

        result["data_loaded"] = data_element_count > 0

        # Take screenshot
        screenshot_path = SCREENSHOT_DIR / f"{html_file.replace('.html', '')}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"📸 Screenshot saved: {screenshot_path}")

        # Analyze API calls
        api_success = sum(1 for call in result["api_calls"] if call["ok"])
        api_failed = len(result["api_calls"]) - api_success

        print(f"\nAPI Calls Summary:")
        print(f"  Total: {len(result['api_calls'])}")
        print(f"  Success: {api_success}")
        print(f"  Failed: {api_failed}")

        if result["api_calls"]:
            print(f"\nAPI Endpoints Called:")
            for call in result["api_calls"]:
                status_icon = "✅" if call["ok"] else "❌"
                print(f"  {status_icon} {call['status']} - {call['url']}")

        # Determine overall status
        if result["errors"]:
            result["status"] = "has_errors"
            print(f"\n❌ STATUS: Page has {len(result['errors'])} errors")
        elif not result["data_loaded"]:
            result["status"] = "no_data"
            print(f"\n⚠️  STATUS: No data elements detected")
        elif api_failed > 0:
            result["status"] = "api_failures"
            print(f"\n⚠️  STATUS: {api_failed} API calls failed")
        else:
            result["status"] = "ok"
            print(f"\n✅ STATUS: Page appears to be working correctly")

        # Console errors summary
        if result["console_errors"]:
            print(f"\nConsole Errors/Warnings: {len(result['console_errors'])}")
            for err in result["console_errors"][:5]:  # Show first 5
                print(f"  {err['type']}: {err['text'][:100]}")

        return result

    except Exception as e:
        result["status"] = "exception"
        result["errors"].append(str(e))
        print(f"❌ EXCEPTION: {e}")
        logger.error("page_inspection_failed", file=html_file, error=str(e))
        return result


async def main():
    """Main inspection loop"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           SPARTAN RESEARCH STATION                           ║
║           Visual Page Inspector                              ║
║                                                               ║
║  Systematic inspection of all HTML pages                     ║
║  Waiting 1 minute per page for data loading                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # Get list of HTML files
    html_files = sorted([f.name for f in Path(".").glob("*.html")
                         if not f.name.startswith("test_")
                         and f.name not in ["COMPREHENSIVE_TRADING_JOURNAL.html",
                                           "SPARTAN_COLOR_PREVIEW.html"]])

    total_pages = len(html_files)
    print(f"Found {total_pages} HTML pages to inspect\n")

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        for idx, html_file in enumerate(html_files, 1):
            result = await inspect_page(page, html_file, idx, total_pages)
            results.append(result)

            # Save incremental results
            with open("page_inspection_results.json", "w") as f:
                json.dump(results, f, indent=2)

        await browser.close()

    # Generate summary report
    print("\n" + "="*80)
    print("INSPECTION COMPLETE - SUMMARY")
    print("="*80 + "\n")

    status_counts = {}
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print("Status Distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count} pages")

    # Pages with errors
    error_pages = [r for r in results if r["errors"]]
    if error_pages:
        print(f"\n⚠️  Pages with Errors ({len(error_pages)}):")
        for result in error_pages:
            print(f"  - {result['file']}: {len(result['errors'])} errors")
            for error in result["errors"][:2]:
                print(f"      {error[:80]}")

    # Pages without data
    no_data_pages = [r for r in results if not r["data_loaded"]]
    if no_data_pages:
        print(f"\n⚠️  Pages Without Data ({len(no_data_pages)}):")
        for result in no_data_pages:
            print(f"  - {result['file']}")

    # API failures
    api_failure_pages = [r for r in results
                         if any(not call["ok"] for call in r["api_calls"])]
    if api_failure_pages:
        print(f"\n⚠️  Pages with API Failures ({len(api_failure_pages)}):")
        for result in api_failure_pages:
            failed_calls = [c for c in result["api_calls"] if not c["ok"]]
            print(f"  - {result['file']}: {len(failed_calls)} failed API calls")

    # Working pages
    working_pages = [r for r in results if r["status"] == "ok"]
    if working_pages:
        print(f"\n✅ Working Pages ({len(working_pages)}):")
        for result in working_pages:
            print(f"  - {result['file']}")

    print(f"\nFull results saved to: page_inspection_results.json")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}/")

    return len(error_pages) + len(no_data_pages) + len(api_failure_pages)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInspection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        logger.error("inspection_failed", error=str(e), exc_info=True)
        sys.exit(1)
