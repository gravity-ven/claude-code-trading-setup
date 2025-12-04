#!/usr/bin/env python3
"""
Batch remove Math.random() from all pages per NO FAKE DATA policy
"""

import re

# Files to fix
files_to_fix = [
    'roce_research.html',
    'symbol_search_connections.html',
    'test_page_validation.html',
    'flashcard_dashboard.html'
]

website_dir = '/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/'

for filename in files_to_fix:
    filepath = website_dir + filename

    print(f"Processing {filename}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find and replace Math.random() in data generation contexts

        # Pattern 1: Math.random() in expressions
        # Replace with deterministic comment
        count = content.count('Math.random()')

        if count > 0:
            print(f"  Found {count} instances of Math.random()")

            # Strategy: Comment out functions that generate fake data
            # Look for common patterns like generateMockData, generateSample, etc.

            # Find function declarations that use Math.random
            pattern = r'(function\s+\w+[^{]*\{[^}]*Math\.random\(\)[^}]*\})'
            matches = re.finditer(pattern, content, re.DOTALL)

            for match in matches:
                func_text = match.group(1)
                # Check if this is a data generation function
                if any(keyword in func_text for keyword in ['generate', 'mock', 'sample', 'fake', 'random']):
                    print(f"    Found data generation function")
                    # Replace the entire function with NO FAKE DATA version
                    # Extract function name
                    func_name_match = re.search(r'function\s+(\w+)', func_text)
                    if func_name_match:
                        func_name = func_name_match.group(1)
                        # Create replacement function
                        replacement = f'''function {func_name}() {{
            // NO FAKE DATA POLICY: Return null/empty instead of synthetic data
            console.error('❌ FAKE DATA REMOVED: {func_name}() disabled per NO FAKE DATA policy');
            console.error('Please use real API data instead.');
            return null;
        }}'''
                        content = content.replace(func_text, replacement)
                        print(f"    Replaced {func_name}()")

            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"  ✅ Fixed {filename}")
        else:
            print(f"  ✅ No Math.random() found in {filename}")

    except Exception as e:
        print(f"  ❌ Error processing {filename}: {e}")

print("\n✅ All files processed!")
