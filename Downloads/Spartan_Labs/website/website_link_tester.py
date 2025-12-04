#!/usr/bin/env python3
"""
Spartan Labs Website Link Tester
Systematically checks all webpages for broken internal links and data availability
Uses computer use to visually verify functionality
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import time
from urllib.parse import urljoin, urlparse
import os

class SpartanWebsiteTester:
    def __init__(self):
        self.base_url = "http://localhost:8888"
        self.session = requests.Session()
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'total_pages': 0,
            'start_time': datetime.now()
        }
        
        # Get all HTML files
        self.html_files = [f for f in os.listdir('/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website') 
                        if f.endswith('.html')]
        
        # Define critical pages to check
        self.critical_pages = [
            'index.html',
            'bitcoin_intelligence.html',
            'gold_intelligence.html', 
            'oil_intelligence.html',
            'global_capital_flow_swing_trading.html',
            'fred_global_complete.html',
            'correlation_matrix.html',
            'market_cycles.html',
            'daily_planet.html',
            'garp.html'
        ]
        
        # Define all intelligence pages
        self.intelligence_pages = [
            'bitcoin_intelligence.html',
            'gold_intelligence.html',
            'oil_intelligence.html', 
            'copper_intelligence.html',
            'bond_intelligence.html'
        ]
        
        # Define analysis pages
        self.analysis_pages = [
            'correlation_matrix.html',
            'seasonality_research.html', 
            'pattern_discovery_terminal.html',
            'pattern_finder_hub.html'
        ]
        
        # Define dashboard pages
        self.dashboard_pages = [
            'unified_market_dashboard.html',
            'flashcard_dashboard.html'
        ]

    def test_all_pages(self):
        """Test all webpages systematically"""
        print("🧪 Spartan Website Link Tester Starting...")
        print(f"📊 Found {len(self.html_files)} HTML pages to test")
        print("=" * 60)
        
        self.results['total_pages'] = len(self.html_files)
        
        # Test each page
        for html_file in sorted(self.html_files):
            self.test_single_page(html_file)
        
        self.generate_report()
        
    def test_single_page(self, html_file):
        """Test a single webpage for broken links and data issues"""
        page_url = f"{self.base_url}/{html_file}"
        
        try:
            print(f"🔍 Testing: {html_file}...")
            
            # Test main page load
            response = self.session.get(page_url, timeout=10)
            
            if response.status_code != 200:
                self.results['failed'].append({
                    'file': html_file,
                    'url': page_url,
                    'error': f"HTTP {response.status_code}",
                    'type': 'page_load_error'
                })
                return False
            
            # Parse HTML and check for broken links
            soup = BeautifulSoup(response.text, 'html.parser')
            
            issues_found = []
            
            # Check for broken internal links
            broken_links = self.check_internal_links(soup, page_url, html_file)
            issues_found.extend(broken_links)
            
            # Check for N/A fields
            na_issues = self.check_na_fields(soup, html_file)
            issues_found.extend(na_issues)
            
            # Check for JavaScript errors
            js_issues = self.check_javascript_errors(soup, html_file)
            issues_found.extend(js_issues)
            
            # Check for data loading issues
            data_issues = self.check_data_loading(soup, html_file)
            issues_found.extend(data_issues)
            
            # Check CSS and styling issues
            css_issues = self.check_css_issues(soup, html_file)
            issues_found.extend(css_issues)
            
            if issues_found:
                self.results['warnings'].extend(issues_found)
                print(f"⚠️ {len(issues_found)} issues found")
                for issue in issues_found[:3]:  # Show first 3 issues
                    print(f"   - {issue['type']}: {issue['description']}")
            else:
                self.results['passed'].append({
                    'file': html_file,
                    'url': page_url,
                    'status': 'ok'
                })
                print(f"✅ {html_file}: PASSED")
            
            return True
            
        except Exception as e:
            self.results['failed'].append({
                'file': html_file,
                'url': page_url,
                'error': str(e),
                'type': 'test_exception'
            })
            print(f"❌ {html_file}: ERROR - {str(e)}")
            return False

    def check_internal_links(self, soup, base_url, page_file):
        """Check for broken internal links"""
        broken = []
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            
            # Skip external links
            if href.startswith('http') and not href.startswith(base_url):
                continue
            # Skip anchor links
            if href.startswith('#'):
                continue
            # Skip mailto links
            if href.startswith('mailto:'):
                continue
            # Skip javascript void
            if href.startswith('javascript:'):
                continue
                continue
            # Skip javascript void
            href.startswith('javascript:'):
                continue
                
            # Convert relative links to absolute
            if not href.startswith('http'):
                full_url = urljoin(base_url, href)
            else:
                full_url = href
            
            # Only test internal links pointing to HTML pages
            if full_url.endswith('.html'):
                try:
                    test_response = self.session.get(full_url, timeout=5)
                    if test_response.status_code != 200:
                        broken.append({
                            'type': 'internal_link_error',
                            'description': f"Broken link to {href} (HTTP {test_response.status_code})",
                            'link': href,
                            'target_url': full_url,
                            'source_page': page_file
                        })
                except Exception as e:
                    broken.append({
                        'type': 'internal_link_error', 
                        'description': f"Failed to test link {href}: {str(e)}",
                        'link': href, 
                        'source_page': page_file
                    })
        
        return broken

    def check_na_fields(self, soup, page_file):
        """Check for N/A fields that indicate data unavailability"""
        na_issues = []
        
        # Check for N/A text content
        text_content = soup.get_text()
        
        na_patterns = [
            r'\bN/A\b',
            r'\bnot available\b',
            r'\bdata unavail',
            r'\bError\b',
            r'\bnull\b',
            r'\bundefined\b'
        ]
        
        for pattern in na_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                na_issues.append({
                    'type': 'na_field_error',
                    'description': f"Found N/A or unavailable data ({len(matches)} occurrences)",
                    'pattern': pattern
                })
        
        # Check for hidden N/A in attributes
        all_elements = soup.find_all(True)
        for element in all_elements:
            for attr_name, attr_value in element.attrs.items():
                if attr_value and re.search(r'\bN/A\b', attr_value):
                    na_issues.append({
                        'type': 'na_attribute_error',
                        'description': f"N/A found in {attr_name} attribute",
                        'element': element.name,
                        'attribute': attr_name,
                        'value': attr_value,
                        'tagged_content': element.get_text()[:100]
                    })
        
        return na_issues

    def check_javascript_errors(self, soup, page_file):
        """Check for common JavaScript error patterns"""
        js_issues = []
        
        script_tags = soup.find_all(['script'])
        
        for script in script_tags:
            script_content = script.get_text() or script.get('src', '')
            
            if script_content:
                # Check for error patterns
                error_patterns = [
                    r'console\.error',
                    r'console\.warn',
                    r'error.*:',
                    r'undefined.*error',
                    r'null.*error'
                ]
                
                for pattern in error_patterns:
                    matches = re.findall(pattern, script_content, re.IGNORECASE)
                    if matches:
                        js_issues.append({
                            'type': 'javascript_error',
                            'description': f"JavaScript error pattern found ({len(matches)} occurrences)",
                            'pattern': pattern,
                            'script_src': script.get('src', 'inline_script')
                        })
        
        return js_issues

    def check_data_loading(self, soup, page_file):
        """Check for data loading issues and broken data endpoints"""
        data_issues = []
        
        # Check for broken API calls
        script_tags = soup.find_all(['script'])
        
        for script in script_tags:
            script_content = script.get_text() or ''
            
            # Look for common data loading patterns
            loading_patterns = [
                r'fetch\(',
                r'\.get\(',
                r'ajax\(',
                r'api/',
                r'/api/'
            ]
            
            for pattern in loading_patterns:
                matches = re.findall(pattern, script_content)
                
                for match in matches:
                    # Try to identify specific API endpoints
                    if 'api/' in match:
                        endpoint = match.split('api/')[1].split("'")[0].split('"')[0]
                        data_issues.append({
                            'type': 'api_usage_warning',
                            'description': f"API endpoint referenced: {endpoint}",
                            'context': match[:100],
                            ' recommendation': "Verify this API endpoint exists and returns data"
                        })
        
        # Check for placeholder or demo data indicators
        placeholder_patterns = [
            r'demo.*data',
            r'placeholder.*text',
            r'lorem.*ipsum',
            r'example.*only'
        ]
        
        page_text = soup.get_text()
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                data_issues.append({
                    'type': 'placeholder_data_warning',
                    'description': f"Potential demo/placeholder data found ({len(matches)} occurrences)",
                    'pattern': pattern
                })
        
        return data_issues

    def check_css_issues(self, soup, page_file):
        """Check for CSS and styling issues"""
        css_issues = []
        
        # Check for inline styles that might indicate errors
        style_tags = soup.find_all(style)
        
        for style in style_tags:
            style_content = style.get_text() or ''
            
            # Look for color or size errors
            error_patterns = [
                r'color:\s*#ff0000',
                r'font-size:\s*0',
                r'display:\s*none',
                r'visibility:\s*hidden'
            ]
            
            for pattern in error_patterns:
                matches = re.findall(pattern, style_content, re.IGNORECASE)
                if matches:
                    css_issues.append({
                        'type': 'css_styling_issue',
                        'description': f"CSS issue found: {pattern} ({len(matches)} occurrences)",
                        'pattern': pattern
                    })
        
        return css_issues

    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = end_time - self.results['start_time']
        
        print("\n" + "=" * 60)
        print("📊 SPARTAN WEBSITE TEST REPORT")
        print("=" * 60)
        
        print(f"⏱️  Total Pages Tested: {self.results['total_pages']}")
        print(f"✅  Passed: {len(self.results['passed'])}")
        print(f"❌  Failed: {len(self.results['failed'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print(f"⏱️  Duration: {duration.total_seconds()}s")
        
        print(f"\n📊 PASSED PAGES:")
        for page in self.results['passed']:
            print(f"  ✅ {page['file']}")
        
        print(f"\n❌ FAILED PAGES:")
        for page in self.results['failed']:
            print(f"  ❌ {page['file']}")
            print(f"     Error: {page['error']}")
        
        print(f"\n⚠️ WARNINGS ({len(self.results['warnings'])}):")
        issue_types = {}
        for warning in self.results['warnings']:
            issue_type = warning['type']
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(warning)
        
        for issue_type, issues_list in issue_types.items():
            print(f"  ⚠️ {issue_type}: {len(issues_list)} occurrences")
            if issues_list:
                print(f"     Example: {issues_list[0]['description']}")
        
        # Summary statistics
        pages_with_issues = len(self.results['failed']) + len(self.results['warnings'])
        issue_rate = (pages_with_issues / self.results['total_pages']) * 100 if self.results['total_pages'] > 0 else 0
        
        print(f"\n📈 SUMMARY:")
        print(f"  Health Score: {100 - issue_rate:.1f}%")
        print(f"  Critical Pages Status: {self.check_critical_pages()}")
        print(f"  Overall Status: {'GOOD' if issue_rate < 20 else 'NEEDS ATTENTION' if issue_rate < 50 else 'CRITICAL'})}")
        
        # Save detailed report
        report_data = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'total_pages': self.results['total_pages'],
            'passed': self.results['passed'],
            'failed': self.results['failed'], 
            'warnings': self.results['warnings'],
            'critical_pages_status': self.check_critical_pages(),
            'health_score': round(100 - issue_rate, 1),
            'overall_status': 'GOOD' if issue_rate < 20 else 'NEEDS ATTENTION' if issue_rate < 50 else 'CRITICAL',
            'pages_with_issues': pages_with_issues
        }
        
        # Save to file
        with open('/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/website_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: website_test_report.json")
        
        return report_data

    def check_critical_pages(self):
        """Check the most critical pages for issues"""
        critical_status = "🔴 ALL CRITICAL PAGES OK"
        
        failed_critical = [p['file'] for p in self.results['failed'] 
                       if p['file'] in self.critical_pages]
        
        if failed_critical:
            critical_status = f"⚠️ CRITICAL ISSUES: {len(failed_critical)} pages failed: {', '.join(failed_critical)}"
        
        return critical_status

def main():
    """Main test runner"""
    tester = SpartanWebsiteTester()
    tester.test_all_pages()
    
    return tester.results

if __name__ == "__main__":
    main()
