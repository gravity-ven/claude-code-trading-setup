#!/usr/bin/env python3
"""
Cache Buster - Automatically adds version timestamps to script/style tags
Run this before starting the web server to ensure fresh resources
"""

import os
import re
import time
from datetime import datetime

def add_cache_busting(html_file):
    """Add timestamp query strings to all script and style tags"""

    if not os.path.exists(html_file):
        print(f"❌ File not found: {html_file}")
        return

    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate timestamp
    timestamp = str(int(time.time()))

    # Pattern to match script tags with src
    script_pattern = r'<script\s+src="([^"]+)"(?!\?v=)'
    script_replacement = f'<script src="\\1?v={timestamp}"'

    # Pattern to match link tags (CSS)
    link_pattern = r'<link\s+([^>]*href="[^"]+\.css")(?!\?v=)'
    link_replacement = f'<link \\1?v={timestamp}"'

    # Remove old version parameters first
    content = re.sub(r'\?v=\d+', '', content)

    # Add new version parameters
    content = re.sub(script_pattern, script_replacement, content)
    content = re.sub(link_pattern, link_replacement, content)

    # Write back
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Cache busting applied to {html_file}")
    print(f"   Version timestamp: {timestamp}")
    print(f"   Human readable: {datetime.fromtimestamp(int(timestamp))}")

if __name__ == '__main__':
    # Apply cache busting to main page
    add_cache_busting('index.html')
    print("\n✅ Cache busting complete!")
    print("All script and CSS tags now have version timestamps")
