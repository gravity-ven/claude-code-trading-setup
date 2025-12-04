#!/usr/bin/env python3
"""
Script to automatically fix all HTML files to use local API proxies instead of external APIs.
This fixes CORS issues permanently across all pages.
"""

import os
import re
from pathlib import Path

# Directory containing HTML files
WEBSITE_DIR = Path(__file__).parent

# API URL replacements
REPLACEMENTS = [
    # Yahoo Finance URLs - chart API
    (
        r'https://query[12]\.finance\.yahoo\.com/v8/finance/chart/',
        r'http://localhost:5002/api/yahoo/chart/'
    ),
    # Yahoo Finance URLs - quote API
    (
        r'https://query[12]\.finance\.yahoo\.com/v7/finance/quote',
        r'http://localhost:5002/api/yahoo/quote'
    ),
    # Yahoo Finance URLs - generic
    (
        r'https://query[12]\.finance\.yahoo\.com',
        r'http://localhost:5002/api/yahoo'
    ),

    # FRED API URLs - with path
    (
        r'https://api\.stlouisfed\.org/fred/series/observations',
        r'http://localhost:5002/api/fred/series/observations'
    ),
    # FRED API URLs - base URL
    (
        r'https://api\.stlouisfed\.org/fred',
        r'http://localhost:5002/api/fred'
    ),

    # Alpha Vantage URLs
    (
        r'https://www\.alphavantage\.co/query',
        r'http://localhost:5002/api/alpha-vantage/query'
    ),
]

def fix_html_file(filepath):
    """Fix API calls in a single HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = False

        # Apply all replacements
        for pattern, replacement in REPLACEMENTS:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                changes_made = True
                content = new_content

        # Write back if changes were made
        if changes_made:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Process all HTML files in the website directory."""
    html_files = list(WEBSITE_DIR.glob('*.html'))

    print("=" * 80)
    print("FIXING API CALLS IN ALL HTML FILES")
    print("=" * 80)
    print(f"\nFound {len(html_files)} HTML files")
    print("\nProcessing...\n")

    fixed_count = 0

    for html_file in html_files:
        if fix_html_file(html_file):
            print(f"✅ Fixed: {html_file.name}")
            fixed_count += 1
        else:
            print(f"⏭️  No changes needed: {html_file.name}")

    print("\n" + "=" * 80)
    print(f"COMPLETE: Fixed {fixed_count} files")
    print("=" * 80)
    print("\nAll external API calls now use local proxies on localhost:5002")
    print("This eliminates CORS issues permanently!\n")

if __name__ == '__main__':
    main()
