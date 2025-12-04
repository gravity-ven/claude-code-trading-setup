#!/usr/bin/env python3
"""
Comprehensive Website Error Checker
Recursively checks all HTML pages for common issues
"""

import re
import os
import glob
from typing import Dict, List, Tuple
from collections import defaultdict

class PageDiagnostics:
    def __init__(self, website_dir: str):
        self.website_dir = website_dir
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)
        self.api_endpoints = defaultdict(set)

    def check_all_pages(self):
        """Check all HTML files in website directory"""
        try:
            all_files = os.listdir(self.website_dir)
            html_files = [os.path.join(self.website_dir, f) for f in all_files if f.endswith('.html') and os.path.isfile(os.path.join(self.website_dir, f))]
        except Exception as e:
            print(f"Error listing files: {e}")
            return

        print(f"🔍 Checking {len(html_files)} HTML files...\n")

        for html_file in sorted(html_files):
            filename = os.path.basename(html_file)
            print(f"Checking: {filename}")
            self.check_page(html_file, filename)

        self.print_report()

    def check_page(self, filepath: str, filename: str):
        """Check individual page for errors"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors[filename].append(f"Failed to read file: {e}")
            return

        # Check for API endpoints
        self.check_api_endpoints(content, filename)

        # Check for FRED series IDs
        self.check_fred_series(content, filename)

        # Check for common JavaScript errors
        self.check_javascript_issues(content, filename)

        # Check for data fetching patterns
        self.check_data_patterns(content, filename)

        # Check for broken normalization formulas (like barometer issues)
        self.check_normalization_formulas(content, filename)

    def check_api_endpoints(self, content: str, filename: str):
        """Find all API endpoints and check for common issues"""
        # Find localhost API calls
        localhost_pattern = r'http://localhost:(\d+)(/[^\s"\'\)]*)'
        matches = re.findall(localhost_pattern, content)

        for port, endpoint in matches:
            self.api_endpoints[filename].add(f"http://localhost:{port}{endpoint}")

            # Check for common port issues
            if port == '8888' and 'api/' in endpoint:
                self.warnings[filename].append(f"Port 8888 used for API endpoint {endpoint} - should be 5002?")

            if port == '5002' and 'fred' in endpoint.lower():
                # This is OK - universal API proxy
                pass

            if port == '5004' and 'correlation' not in endpoint.lower():
                self.warnings[filename].append(f"Port 5004 used for non-correlation endpoint: {endpoint}")

    def check_fred_series(self, content: str, filename: str):
        """Check FRED series IDs for validity"""
        # Common incorrect FRED series
        bad_series = {
            'MANEMP': 'Manufacturing employment (not PMI) - use IPMAN instead',
            'SRVPRD': 'Services production (not PMI) - use PCE instead',
        }

        for series, issue in bad_series.items():
            if series in content:
                self.errors[filename].append(f"Using {series}: {issue}")

    def check_javascript_issues(self, content: str, filename: str):
        """Check for common JavaScript errors"""
        # Check for Math.random() (fake data)
        if 'Math.random()' in content:
            self.errors[filename].append("❌ FAKE DATA: Using Math.random() - FORBIDDEN")

        # Check for undefined variable access
        if re.search(r'barometerData\.lei\s*\?\s*50\s*:', content):
            self.errors[filename].append("Using placeholder value 50 for LEI instead of actual data")

        # Check for division by zero possibilities
        if re.search(r'/\s*\(.*-.*\)', content):
            self.warnings[filename].append("Potential division by zero in formula")

    def check_data_patterns(self, content: str, filename: str):
        """Check data fetching patterns"""
        # Check if using SpartanData preloader
        if 'window.SpartanData' in content:
            self.warnings[filename].append("✅ Using SpartanData preloader (good!)")

        # Check if using fetch without cache check
        if 'fetch(' in content and 'SpartanData' not in content:
            self.warnings[filename].append("Fetching data without checking preloader cache first")

    def check_normalization_formulas(self, content: str, filename: str):
        """Check for broken normalization formulas like barometer issues"""
        # Check for suspicious normalization ranges
        suspicious_patterns = [
            (r'40\s*\+\s*\([^)]+\)\s*\*\s*20', "Normalizing to 40-60 range (too narrow for PMI)"),
            (r'45\s*\+\s*\([^)]+\)\s*\*\s*15', "Normalizing to 45-60 range (too narrow for services)"),
            (r'100\s*-\s*\(\(.*-\s*200000\)\s*/\s*2000\)', "Broken employment formula (can produce negatives)"),
        ]

        for pattern, issue in suspicious_patterns:
            if re.search(pattern, content):
                self.errors[filename].append(f"Broken formula: {issue}")

    def print_report(self):
        """Print comprehensive error report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE ERROR REPORT")
        print("="*80 + "\n")

        # Errors
        if self.errors:
            print("🚨 CRITICAL ERRORS:\n")
            for filename, errors in sorted(self.errors.items()):
                print(f"\n📄 {filename}:")
                for error in errors:
                    print(f"   ❌ {error}")
        else:
            print("✅ No critical errors found!\n")

        # Warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:\n")
            for filename, warnings in sorted(self.warnings.items()):
                print(f"\n📄 {filename}:")
                for warning in warnings:
                    print(f"   ⚠️  {warning}")

        # API Endpoints Summary
        print("\n" + "="*80)
        print("API ENDPOINTS USED")
        print("="*80 + "\n")

        all_endpoints = set()
        for endpoints in self.api_endpoints.values():
            all_endpoints.update(endpoints)

        endpoint_by_port = defaultdict(list)
        for endpoint in sorted(all_endpoints):
            port = endpoint.split(':')[2].split('/')[0]
            endpoint_by_port[port].append(endpoint)

        for port, endpoints in sorted(endpoint_by_port.items()):
            print(f"\nPort {port}:")
            for endpoint in endpoints[:5]:  # Show first 5
                print(f"  • {endpoint}")
            if len(endpoints) > 5:
                print(f"  ... and {len(endpoints) - 5} more")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total pages checked: {len(self.api_endpoints)}")
        print(f"Pages with errors: {len(self.errors)}")
        print(f"Pages with warnings: {len(self.warnings)}")
        print(f"Unique API endpoints: {len(all_endpoints)}")


if __name__ == "__main__":
    website_dir = "/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website"

    checker = PageDiagnostics(website_dir)
    checker.check_all_pages()
