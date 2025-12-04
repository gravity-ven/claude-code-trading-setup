#!/usr/bin/env python3
"""
Deep Integration Test for Spartan Research Station Flashcard System
Tests navigation, file existence, connections, and identifies errors
"""

import re
import os
from pathlib import Path
from collections import defaultdict

class FlashcardIntegrityTester:
    def __init__(self, index_html_path):
        self.index_path = Path(index_html_path)
        self.base_dir = self.index_path.parent
        self.errors = []
        self.warnings = []
        self.info = []
        self.flashcards = {}

    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 80)
        print("🔍 SPARTAN RESEARCH STATION - DEEP INTEGRATION TEST")
        print("=" * 80)
        print()

        # Read HTML content
        with open(self.index_path, 'r', encoding='utf-8') as f:
            self.html_content = f.read()

        # Run tests
        self.test_flashcard_extraction()
        self.test_navigation_links()
        self.test_duplicate_ids()
        self.test_data_connections()
        self.test_html_structure()
        self.test_javascript_references()

        # Generate report
        self.generate_report()

    def test_flashcard_extraction(self):
        """Extract all flashcards and their metadata"""
        print("📊 TEST 1: Flashcard Extraction")
        print("-" * 80)

        # Find all flashcard divs
        pattern = r'<div class="flashcard"[^>]*data-id="([^"]+)"[^>]*>'
        matches = re.finditer(pattern, self.html_content)

        for match in matches:
            flashcard_id = match.group(1)

            # Extract flashcard block
            start_pos = match.start()
            # Find the closing div (simplified - counts div depth)
            depth = 1
            pos = start_pos + len(match.group(0))
            while depth > 0 and pos < len(self.html_content):
                if self.html_content[pos:pos+5] == '<div ':
                    depth += 1
                elif self.html_content[pos:pos+6] == '</div>':
                    depth -= 1
                pos += 1

            flashcard_html = self.html_content[start_pos:pos]

            # Extract metadata
            category_match = re.search(r'data-category="([^"]+)"', flashcard_html)
            connections_match = re.search(r'data-connections="([^"]+)"', flashcard_html)
            onclick_match = re.search(r'onclick="window\.location\.href=\'([^\']+)\'', flashcard_html)
            title_match = re.search(r'<h3[^>]*>([^<]+)</h3>', flashcard_html)

            self.flashcards[flashcard_id] = {
                'category': category_match.group(1) if category_match else None,
                'connections': connections_match.group(1).split(',') if connections_match else [],
                'target_file': onclick_match.group(1) if onclick_match else None,
                'title': title_match.group(1).strip() if title_match else 'UNKNOWN',
                'html': flashcard_html
            }

        total = len(self.flashcards)
        print(f"✅ Found {total} flashcards")

        # List all flashcards
        for fid, data in sorted(self.flashcards.items()):
            status = "🔗" if data['target_file'] else "⚠️"
            print(f"  {status} {fid:30s} → {data['title']}")

        print()
        self.info.append(f"Total flashcards: {total}")

    def test_navigation_links(self):
        """Test that all navigation links point to existing files"""
        print("🔗 TEST 2: Navigation Link Validation")
        print("-" * 80)

        files_checked = 0
        files_ok = 0
        files_missing = 0

        for fid, data in self.flashcards.items():
            target = data['target_file']
            if not target:
                self.warnings.append(f"Flashcard '{fid}' has no navigation link (might be intentional)")
                continue

            files_checked += 1
            file_path = self.base_dir / target

            if file_path.exists():
                files_ok += 1
                print(f"  ✅ {fid:30s} → {target} (EXISTS)")
            else:
                files_missing += 1
                self.errors.append(f"Missing file: {target} (referenced by flashcard '{fid}')")
                print(f"  ❌ {fid:30s} → {target} (MISSING)")

        print()
        print(f"📈 Results: {files_ok}/{files_checked} files exist, {files_missing} missing")
        print()

    def test_duplicate_ids(self):
        """Check for duplicate data-id values"""
        print("🔍 TEST 3: Duplicate ID Detection")
        print("-" * 80)

        id_counts = defaultdict(int)
        for fid in self.flashcards.keys():
            id_counts[fid] += 1

        duplicates = {k: v for k, v in id_counts.items() if v > 1}

        if duplicates:
            print("  ❌ DUPLICATE IDs FOUND:")
            for fid, count in duplicates.items():
                self.errors.append(f"Duplicate data-id: '{fid}' appears {count} times")
                print(f"     • {fid} (appears {count} times)")
        else:
            print("  ✅ No duplicate IDs found - all flashcards have unique identifiers")

        print()

    def test_data_connections(self):
        """Validate all data-connections point to valid flashcards"""
        print("🔗 TEST 4: Data Connections Validation")
        print("-" * 80)

        all_ids = set(self.flashcards.keys())
        total_connections = 0
        broken_connections = 0

        for fid, data in self.flashcards.items():
            connections = data['connections']
            total_connections += len(connections)

            for conn in connections:
                if conn not in all_ids:
                    broken_connections += 1
                    self.warnings.append(f"Broken connection: '{fid}' → '{conn}' (target doesn't exist)")
                    print(f"  ⚠️  {fid:30s} → {conn} (BROKEN)")

        valid_connections = total_connections - broken_connections
        print()
        print(f"📊 Results: {valid_connections}/{total_connections} connections valid, {broken_connections} broken")
        print()

    def test_html_structure(self):
        """Check HTML structure for common issues"""
        print("🏗️  TEST 5: HTML Structure Validation")
        print("-" * 80)

        issues = []

        # Check for unclosed divs in flashcard sections
        flashcard_section = re.search(
            r'<div class="flashcard-network".*?</div>\s*</div>\s*<!--.*Legend',
            self.html_content,
            re.DOTALL
        )

        if flashcard_section:
            content = flashcard_section.group(0)
            div_opens = content.count('<div')
            div_closes = content.count('</div>')

            if div_opens != div_closes:
                issues.append(f"Unbalanced divs in flashcard section: {div_opens} opens, {div_closes} closes")
                print(f"  ⚠️  Unbalanced divs: {div_opens} <div> vs {div_closes} </div>")
            else:
                print(f"  ✅ Balanced divs: {div_opens} opening tags = {div_closes} closing tags")

        # Check for onclick syntax
        onclick_errors = re.findall(r'onclick="window\.location\.href=\'([^\']*)"', self.html_content)
        if onclick_errors:
            issues.append(f"Found {len(onclick_errors)} onclick attributes with potential syntax errors")
            print(f"  ⚠️  Found {len(onclick_errors)} onclick statements (verify quotes)")

        # Check for missing quotes in attributes
        bad_attrs = re.findall(r'data-\w+=[^"\s>]+\s', self.html_content)
        if bad_attrs:
            issues.append(f"Found {len(bad_attrs)} attributes without quotes")
            print(f"  ⚠️  Found {len(bad_attrs)} unquoted attributes")

        if not issues:
            print("  ✅ HTML structure appears valid")

        print()

    def test_javascript_references(self):
        """Check JavaScript function references"""
        print("⚙️  TEST 6: JavaScript Reference Validation")
        print("-" * 80)

        # Find all onclick handlers
        onclick_patterns = re.findall(r'onclick="([^"]+)"', self.html_content)

        valid_patterns = [
            r'window\.location\.href=',
            r'toggleEditMode\(',
            r'window\.open\(',
        ]

        invalid_count = 0
        for pattern in onclick_patterns:
            is_valid = any(re.search(vp, pattern) for vp in valid_patterns)
            if not is_valid:
                invalid_count += 1
                self.warnings.append(f"Unusual onclick pattern: {pattern[:50]}...")

        print(f"  📊 Found {len(onclick_patterns)} onclick handlers")
        print(f"  ✅ {len(onclick_patterns) - invalid_count} standard patterns")
        if invalid_count > 0:
            print(f"  ⚠️  {invalid_count} non-standard patterns (review recommended)")

        print()

    def generate_report(self):
        """Generate final test report"""
        print("=" * 80)
        print("📋 FINAL TEST REPORT")
        print("=" * 80)
        print()

        print(f"🎯 Total Flashcards: {len(self.flashcards)}")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"ℹ️  Info: {len(self.info)}")
        print()

        if self.errors:
            print("❌ ERRORS (MUST FIX):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS (REVIEW RECOMMENDED):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
            print()

        if self.info:
            print("ℹ️  INFORMATION:")
            for i, info_item in enumerate(self.info, 1):
                print(f"   {i}. {info_item}")
            print()

        # Overall status
        if not self.errors:
            print("✅ PASS - No critical errors found!")
            if self.warnings:
                print("⚠️  Some warnings detected - review recommended but not critical")
        else:
            print("❌ FAIL - Critical errors detected that need fixing")

        print()
        print("=" * 80)
        print("🏁 TEST COMPLETE")
        print("=" * 80)

        return len(self.errors) == 0

if __name__ == '__main__':
    import sys

    # Path to index.html
    index_path = '/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/index.html'

    if not os.path.exists(index_path):
        print(f"❌ Error: {index_path} not found")
        sys.exit(1)

    # Run tests
    tester = FlashcardIntegrityTester(index_path)
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
