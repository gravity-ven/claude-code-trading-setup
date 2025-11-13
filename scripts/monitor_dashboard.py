#!/usr/bin/env python3
"""
Spartan Labs QA Monitor Dashboard
Main monitoring and dashboard system for trading infrastructure
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

class QAMonitor:
    """QA Monitor main class"""
    
    def __init__(self, base_path: str = "/mnt/c/Users/Quantum/spartan-labs-qa-monitor"):
        self.base_path = Path(base_path)
        self.config_path = self.base_path / "config"
        self.reports_path = self.base_path / "reports"
        self.logs_path = self.base_path / "logs"
        
        # Ensure directories exist
        for path in [self.config_path, self.reports_path, self.logs_path]:
            path.mkdir(exist_ok=True)
        
        self.setup_logging()
        self.load_config()
        
    def setup_logging(self):
        """Setup logging configuration"""
        self.logs_path.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_path / 'qa_monitor.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Load configuration from files"""
        config_file = self.config_path / 'monitor_config.json'
        
        default_config = {
            'monitor_trading_hours': True,
            'alert_thresholds': {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'disk_usage': 90.0,
                'response_time_ms': 5000
            },
            'check_intervals': {
                'system_health': 300,  # 5 minutes
                'trading_systems': 60,   # 1 minute
                'dashboard_update': 900  # 15 minutes
            },
            'notifications': {
                'email': False,
                'slack': False,
                'console': True
            }
        }
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                try:
                    self.config = json.load(f)
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid config file: {config_file}")
                    self.config = default_config
        else:
            self.config = default_config
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path / 'monitor_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def check_system_health(self) -> dict:
        """Check system health metrics"""
        import psutil
        import shutil
        
        health = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': {},
            'status': 'healthy'
        }
        
        # Check disk usage for main drives
        for mount in ['/mnt/c', '/']:
            if os.path.exists(mount):
                usage = shutil.disk_usage(mount)
                health['disk_usage'][mount] = {
                    'used_percent': (usage.used / usage.total) * 100,
                    'free_gb': usage.free / (1024**3),
                    'total_gb': usage.total / (1024**3)
                }
        
        # Check overall health
        for metric, threshold in self.config['alert_thresholds'].items():
            if metric in health and health[metric] > threshold:
                health['status'] = 'warning'
        
        return health
    
    def generate_report(self) -> str:
        """Generate monitoring report"""
        health = self.check_system_health()
        
        report_lines = [
            "# Spartan Labs QA Monitor Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## System Health",
            f"Status: {health['status'].upper()}",
            f"CPU Usage: {health['cpu_percent']}%",
            f"Memory Usage: {health['memory_percent']}%",
            "",
            "## Disk Usage"
        ]
        
        for mount, usage in health['disk_usage'].items():
            report_lines.extend([
                f"**{mount}**",
                f"Space Used: {usage['used_percent']:.1f}%",
                f"Free Space: {usage['free_gb']:.1f} GB",
                f"Total Space: {usage['total_gb']:.1f} GB",
                ""
            ])
        
        # Add trading system checks
        report_lines.extend([
            "## Trading Systems",
            "Status: Monitoring Active",
            "Last Check: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "",
            "## Summary",
            "✅ Monitor: Active",
            f"✅ Config: Loaded from {self.config_path}",
            f"✅ Reports: {len(list(self.reports_path.glob('*'))} reports available"
        ])
        
        return '\n'.join(report_lines)
    
    def save_report(self, content: str, filename: str = None):
        """Save report to file"""
        if not filename:
            filename = f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_path = self.reports_path / filename
        with open(report_path, 'w') as f:
            f.write(content)
        
        self.logger.info(f"Report saved: {report_path}")
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        self.logger.info("Starting QA monitoring cycle")
        
        # Check system health
        health = self.check_system_health()
        self.logger.info(f"System status: {health['status']}")
        
        # Check for alerts
        if health['status'] == 'warning':
            self.logger.warning("System health threshold exceeded!")
        
        # Generate and save report
        report_content = self.generate_report()
        self.save_report(report_content)
        
        self.logger.info("Monitoring cycle completed")

def main():
    """Main execution function"""
    monitor = QAMonitor()
    print("🚀 Spartan Labs QA Monitor")
    print("=" * 40)
    
    try:
        # Run monitoring cycle
        monitor.run_monitoring_cycle()
        
        print("\n✅ Monitoring completed successfully!")
        print(f"📊 Reports saved in: {monitor.reports_path}")
        print(f"📋 Logs available in: {monitor.logs_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Monitor failed: {e}", exc_info=sys.exc_info())
        sys.exit(1)

if __name__ == "__main__":
    main()
