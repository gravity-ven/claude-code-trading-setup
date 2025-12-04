#!/usr/bin/env python3
"""
Advanced Validation Tests for Spartan Research Station
Checks CSS, accessibility, performance, and advanced HTML issues
"""

import re
import os
from pathlib import Path
from collections import Counter

class AdvancedValidator:
    def __init__(self, index_html_path):
        self.index_path = Path(index_html_path)
        self.errors = []
        self.warnings = []
        self.info = []

        with open(self.index_path, 'r', encoding='utf-8') as f:
            self.html = f.read()

    def run_all_tests(self):
        """Run all advanced validation tests"""
        print("=" * 80)
        print("🔬 ADVANCED VALIDATION TEST SUITE")
        print("=" * 80)
        print()

        self.test_css_references()
        self.test_javascript_includes()
        self.test_accessibility()
        self.test_performance_hints()
        self.test_responsive_design()
        self.test_seo_meta_tags()
        self.test_navigation_structure()

        self.generate_report()

    def test_css_references(self):
        """Check CSS file references"""
        print("🎨 TEST 1: CSS References")
        print("-" * 80)

        css_refs = re.findall(r'<link[^>]*href="([^"]+\.css)"', self.html)
        print(f"  Found {len(css_refs)} CSS references:")

        for css_file in css_refs:
            if css_file.startswith('http'):
                print(f"    🌐 {css_file} (external)")
                self.info.append(f"External CSS: {css_file}")
            else:
                full_path = self.index_path.parent / css_file
                if full_path.exists():
                    print(f"    ✅ {css_file} (exists)")
                else:
                    print(f"    ❌ {css_file} (MISSING)")
                    self.errors.append(f"Missing CSS file: {css_file}")

        print()

    def test_javascript_includes(self):
        """Check JavaScript file includes"""
        print("⚙️  TEST 2: JavaScript Includes")
        print("-" * 80)

        js_refs = re.findall(r'<script[^>]*src="([^"]+)"', self.html)
        print(f"  Found {len(js_refs)} JavaScript includes:")

        for js_file in js_refs:
            if js_file.startswith('http'):
                print(f"    🌐 {js_file} (external)")
                self.info.append(f"External JS: {js_file}")
            else:
                full_path = self.index_path.parent / js_file
                if full_path.exists():
                    print(f"    ✅ {js_file} (exists)")
                else:
                    print(f"    ⚠️  {js_file} (missing - may be commented out)")
                    self.warnings.append(f"JavaScript file not found: {js_file}")

        print()

    def test_accessibility(self):
        """Check accessibility features"""
        print("♿ TEST 3: Accessibility Validation")
        print("-" * 80)

        issues = []

        # Check for alt text on images
        img_tags = re.findall(r'<img[^>]*>', self.html)
        imgs_without_alt = [img for img in img_tags if 'alt=' not in img]

        if imgs_without_alt:
            issues.append(f"Found {len(imgs_without_alt)} images without alt text")
            print(f"  ⚠️  {len(imgs_without_alt)} images missing alt text")

        # Check for ARIA labels on clickable divs
        clickable_divs = re.findall(r'<div[^>]*onclick=[^>]*>', self.html)
        divs_without_role = [div for div in clickable_divs if 'role=' not in div]

        if divs_without_role:
            issues.append(f"Found {len(divs_without_role)} clickable divs without role attribute")
            print(f"  ⚠️  {len(divs_without_role)} clickable elements missing role attribute")

        # Check for lang attribute
        if 'lang="en"' in self.html or '<html lang="en">' in self.html:
            print("  ✅ Language attribute set (en)")
        else:
            issues.append("Missing lang attribute on <html> tag")
            print("  ⚠️  Missing lang attribute")

        if not issues:
            print("  ✅ No major accessibility issues detected")

        print()

    def test_performance_hints(self):
        """Check performance optimization hints"""
        print("⚡ TEST 4: Performance Optimization")
        print("-" * 80)

        # Check for preconnect hints
        preconnects = re.findall(r'rel="preconnect"', self.html)
        print(f"  ✅ Found {len(preconnects)} preconnect hints")

        # Check for dns-prefetch
        dns_prefetch = re.findall(r'rel="dns-prefetch"', self.html)
        print(f"  ✅ Found {len(dns_prefetch)} dns-prefetch hints")

        # Check for defer/async on scripts
        script_tags = re.findall(r'<script[^>]*src=[^>]*>', self.html)
        deferred = [s for s in script_tags if 'defer' in s or 'async' in s]
        print(f"  ✅ {len(deferred)}/{len(script_tags)} scripts use defer/async")

        # Check cache control meta tags
        if 'Cache-Control' in self.html:
            print("  ✅ Cache control meta tags present")
        else:
            print("  ⚠️  No cache control meta tags found")

        print()

    def test_responsive_design(self):
        """Check responsive design elements"""
        print("📱 TEST 5: Responsive Design")
        print("-" * 80)

        # Check viewport meta tag
        if 'name="viewport"' in self.html:
            print("  ✅ Viewport meta tag present")
        else:
            self.errors.append("Missing viewport meta tag")
            print("  ❌ Missing viewport meta tag")

        # Check for media queries in CSS
        media_queries = re.findall(r'@media[^{]+{', self.html)
        if media_queries:
            print(f"  ✅ Found {len(media_queries)} media queries")
        else:
            print("  ⚠️  No media queries found in inline styles")

        # Check for flexbox/grid usage
        if 'display: flex' in self.html or 'display: grid' in self.html:
            print("  ✅ Modern layout (flexbox/grid) detected")
        else:
            print("  ⚠️  No flexbox/grid detected")

        print()

    def test_seo_meta_tags(self):
        """Check SEO meta tags"""
        print("🔍 TEST 6: SEO Meta Tags")
        print("-" * 80)

        # Check title tag
        title_match = re.search(r'<title>([^<]+)</title>', self.html)
        if title_match:
            title = title_match.group(1)
            print(f"  ✅ Title: {title[:60]}...")
        else:
            self.errors.append("Missing <title> tag")
            print("  ❌ Missing title tag")

        # Check meta description
        if 'name="description"' in self.html:
            print("  ✅ Meta description present")
        else:
            self.warnings.append("Missing meta description")
            print("  ⚠️  Missing meta description")

        # Check charset
        if 'charset=' in self.html:
            print("  ✅ Character encoding specified")
        else:
            print("  ⚠️  No character encoding specified")

        print()

    def test_navigation_structure(self):
        """Analyze navigation structure and complexity"""
        print("🧭 TEST 7: Navigation Structure Analysis")
        print("-" * 80)

        # Count navigation tabs
        nav_tabs = re.findall(r'<button class="nav-tab"[^>]*data-tab="([^"]+)"', self.html)
        print(f"  📊 Navigation tabs: {len(nav_tabs)}")
        for tab in nav_tabs:
            print(f"     • {tab}")

        print()

        # Count flashcard categories
        categories = re.findall(r'data-category="([^"]+)"', self.html)
        category_counts = Counter(categories)
        print(f"  📊 Flashcard categories:")
        for cat, count in category_counts.items():
            print(f"     • {cat}: {count} flashcards")

        print()

        # Analyze connection density
        all_connections = re.findall(r'data-connections="([^"]+)"', self.html)
        total_connections = sum(len(c.split(',')) for c in all_connections)
        avg_connections = total_connections / len(all_connections) if all_connections else 0
        print(f"  🔗 Connection statistics:")
        print(f"     • Total connections: {total_connections}")
        print(f"     • Average per flashcard: {avg_connections:.1f}")

        print()

    def generate_report(self):
        """Generate final report"""
        print("=" * 80)
        print("📋 ADVANCED VALIDATION REPORT")
        print("=" * 80)
        print()

        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"ℹ️  Info: {len(self.info)}")
        print()

        if self.errors:
            print("❌ ERRORS:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
            print()

        if not self.errors:
            print("✅ PASS - No critical errors!")
        else:
            print("❌ FAIL - Please fix errors above")

        print()
        print("=" * 80)

if __name__ == '__main__':
    import sys

    index_path = '/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/index.html'

    if not os.path.exists(index_path):
        print(f"❌ Error: {index_path} not found")
        sys.exit(1)

    validator = AdvancedValidator(index_path)
    validator.run_all_tests()
