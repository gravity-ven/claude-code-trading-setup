#!/usr/bin/env python3
"""
Spartan COT Agents - Persistent Monitoring TUI
Continuous market analysis with live trade sheet display
REAL DATA ONLY - No fake/simulated data
"""

import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich import box
import argparse

console = Console()


class COTMonitorTUI:
    """Persistent monitoring TUI with trade sheet display"""

    def __init__(self, demo_mode=False, interval_hours=1):
        self.demo_mode = demo_mode
        self.interval_hours = interval_hours
        self.layout = Layout()
        self.start_time = datetime.now()
        self.cycle_count = 0
        self.last_cycle_time = None

        # Tier status tracking
        self.tier_status = {
            'tier1': {'status': 'pending', 'results': [], 'count': 0},
            'tier2': {'status': 'pending', 'results': [], 'count': 0},
            'tier3': {'status': 'pending', 'results': [], 'count': 0},
            'tier4': {'status': 'pending', 'results': [], 'count': 0}
        }

        # Trade sheet tracking
        self.trade_opportunities = []
        self.last_update = None

        # Configure layout - 5 sections
        self.layout.split(
            Layout(name="header", size=5),
            Layout(name="tiers", size=20),
            Layout(name="tradesheet", ratio=1),
            Layout(name="footer", size=5)
        )

        # Tier panels (2x2 grid)
        self.layout["tiers"].split_row(
            Layout(name="left_tiers"),
            Layout(name="right_tiers")
        )

        self.layout["tiers"]["left_tiers"].split_column(
            Layout(name="t1"),
            Layout(name="t2")
        )

        self.layout["tiers"]["right_tiers"].split_column(
            Layout(name="t3"),
            Layout(name="t4")
        )

    def create_header(self) -> Panel:
        """Create header panel with status"""
        mode = "DEMO MODE" if self.demo_mode else "PRODUCTION"
        uptime = (datetime.now() - self.start_time).total_seconds()
        uptime_str = f"{int(uptime//3600)}h {int((uptime%3600)//60)}m"

        next_cycle = ""
        if self.last_cycle_time:
            elapsed = (datetime.now() - self.last_cycle_time).total_seconds()
            remaining = (self.interval_hours * 3600) - elapsed
            if remaining > 0:
                next_cycle = f"Next cycle in: {int(remaining//60)}m {int(remaining%60)}s"
            else:
                next_cycle = "Starting next cycle..."

        header = f"""
SPARTAN COT AGENTS - Continuous Market Monitoring

{mode} | Uptime: {uptime_str} | Cycles: {self.cycle_count} | {next_cycle}
        """

        return Panel(
            Text(header, style="bold cyan", justify="center"),
            style="cyan",
            box=box.ASCII,
            padding=(0, 1)
        )

    def create_tier_panel(self, tier_num: int) -> Panel:
        """Create tier panel with status"""
        tier_key = f'tier{tier_num}'
        tier_data = self.tier_status[tier_key]
        status = tier_data['status']
        results = tier_data['results']

        tier_info = {
            1: ('COT', 'cyan', 'CFTC Data'),
            2: ('Season', 'yellow', 'Patterns'),
            3: ('Signals', 'magenta', 'Confluence'),
            4: ('Trades', 'green', 'Opportunities')
        }

        title, color, description = tier_info[tier_num]

        status_text = {
            'pending': '[WAIT]',
            'running': '[ACTIVE]',
            'completed': '[DONE]',
            'failed': '[ERROR]'
        }[status]

        status_colors = {
            'pending': 'dim',
            'running': 'bold yellow',
            'completed': 'bold green',
            'failed': 'bold red'
        }[status]

        content = Text()
        content.append(f"{status_text} ", style=status_colors)
        content.append(f"{description}\n", style="white")

        if results:
            for result in results[-3:]:  # Last 3 results only
                clean = result.encode('ascii', 'ignore').decode('ascii')[:50]
                content.append(f"* {clean}\n", style="dim")
        elif status == 'completed':
            content.append(f"  {tier_data['count']} items\n", style="dim green")

        return Panel(
            content,
            title=f"[{color}]{title}[/]",
            border_style=color,
            box=box.ASCII,
            padding=(0, 1)
        )

    def create_tradesheet_panel(self) -> Panel:
        """Create trade sheet display panel"""

        if not self.trade_opportunities:
            content = Text()
            content.append("\n  Waiting for trade opportunities...\n\n", style="dim italic")
            content.append("  CFTC data updates weekly (Fridays 3:30 PM ET)\n", style="dim")
            content.append("  System needs 26 weeks of data for extremes\n", style="dim")
            content.append(f"\n  Last check: {datetime.now().strftime('%H:%M:%S')}\n", style="dim cyan")

            return Panel(
                content,
                title="[bold green]Trade Opportunities[/]",
                border_style="green",
                box=box.ASCII,
                padding=(1, 2)
            )

        # Build trade sheet table
        table = Table(
            show_header=True,
            header_style="bold green",
            box=box.ASCII,
            padding=(0, 1),
            expand=True
        )

        table.add_column("Symbol", style="cyan", no_wrap=True)
        table.add_column("Direction", style="white", no_wrap=True)
        table.add_column("Confidence", style="yellow", no_wrap=True)
        table.add_column("Setup", style="white")

        for opp in self.trade_opportunities[:10]:  # Top 10
            symbol = opp.get('symbol', '?')
            direction = opp.get('direction', '?')
            confidence = opp.get('confidence', 0)
            setup = opp.get('setup', 'N/A')[:40]  # Truncate

            direction_color = "green" if direction == "LONG" else "red"

            table.add_row(
                symbol,
                f"[{direction_color}]{direction}[/]",
                f"{confidence}%",
                setup
            )

        footer = Text(f"\nLast updated: {self.last_update}", style="dim")

        from rich.console import Group
        content = Group(table, footer)

        return Panel(
            content,
            title=f"[bold green]Trade Opportunities ({len(self.trade_opportunities)})[/]",
            border_style="green",
            box=box.ASCII,
            padding=(1, 1)
        )

    def create_footer(self) -> Panel:
        """Create footer with controls"""
        footer = Text("", justify="center")
        footer.append("Press Ctrl+C to stop monitoring", style="yellow")
        footer.append(" | ", style="dim")
        footer.append(f"Interval: {self.interval_hours}h", style="cyan")
        footer.append(" | ", style="dim")
        footer.append("Logs: tail -f logs/agents.log", style="dim")

        return Panel(
            footer,
            style="white",
            box=box.ASCII,
            padding=(0, 1)
        )

    def generate_layout(self) -> Layout:
        """Generate the complete layout"""
        self.layout["header"].update(self.create_header())
        self.layout["t1"].update(self.create_tier_panel(1))
        self.layout["t2"].update(self.create_tier_panel(2))
        self.layout["t3"].update(self.create_tier_panel(3))
        self.layout["t4"].update(self.create_tier_panel(4))
        self.layout["tradesheet"].update(self.create_tradesheet_panel())
        self.layout["footer"].update(self.create_footer())

        return self.layout

    def update_tier(self, tier_num: int, status: str = None, results: list = None, count: int = None):
        """Update tier status"""
        tier_key = f'tier{tier_num}'

        if status:
            self.tier_status[tier_key]['status'] = status

        if results is not None:
            self.tier_status[tier_key]['results'] = results

        if count is not None:
            self.tier_status[tier_key]['count'] = count

    def load_trade_sheet(self):
        """Load trade sheet from output file"""
        trade_sheet_path = Path('output/latest_trade_sheet.txt')

        if not trade_sheet_path.exists():
            self.trade_opportunities = []
            return

        try:
            with open(trade_sheet_path, 'r') as f:
                content = f.read()

            # Parse trade sheet (simple parsing)
            opportunities = []

            # Look for sections like "Symbol: GC"
            lines = content.split('\n')
            current_opp = {}

            for line in lines:
                line = line.strip()

                if line.startswith('Symbol:'):
                    if current_opp:
                        opportunities.append(current_opp)
                    current_opp = {'symbol': line.split(':')[1].strip()}

                elif line.startswith('Confidence:'):
                    conf_str = line.split(':')[1].strip().replace('%', '')
                    try:
                        current_opp['confidence'] = int(conf_str)
                    except:
                        current_opp['confidence'] = 0

                elif line.startswith('Setup:'):
                    current_opp['setup'] = line.split(':', 1)[1].strip()

                elif 'LONG' in line.upper():
                    current_opp['direction'] = 'LONG'
                elif 'SHORT' in line.upper():
                    current_opp['direction'] = 'SHORT'

            if current_opp:
                opportunities.append(current_opp)

            self.trade_opportunities = opportunities
            self.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse trade sheet: {e}[/]")
            self.trade_opportunities = []

    def run_agents_continuous(self, live):
        """Run agents continuously - REAL DATA ONLY"""

        args = ['python3', '-u', 'run_100_agents.py']

        if self.demo_mode:
            args.append('--demo')

        args.append('--interval')
        args.append(str(self.interval_hours))

        # NO --single-cycle = runs forever

        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        current_tier = None

        for line in process.stdout:
            line = line.strip()

            # Detect cycle start
            if 'STARTING SINGLE CYCLE' in line or 'STARTING CYCLE' in line:
                self.cycle_count += 1
                self.last_cycle_time = datetime.now()
                # Reset tiers
                for tier in ['tier1', 'tier2', 'tier3', 'tier4']:
                    self.tier_status[tier]['status'] = 'pending'
                    self.tier_status[tier]['results'] = []
                live.update(self.generate_layout())

            # Detect tier transitions
            if 'TIER 1: COT Analysis' in line:
                current_tier = 1
                self.update_tier(1, status='running')
                live.update(self.generate_layout())

            elif 'TIER 2: Seasonality' in line:
                self.update_tier(1, status='completed')
                current_tier = 2
                self.update_tier(2, status='running')
                live.update(self.generate_layout())

            elif 'TIER 3: Confluence' in line:
                self.update_tier(2, status='completed')
                current_tier = 3
                self.update_tier(3, status='running')
                live.update(self.generate_layout())

            elif 'TIER 4:' in line:
                self.update_tier(3, status='completed')
                current_tier = 4
                self.update_tier(4, status='running')
                live.update(self.generate_layout())

            # Detect cycle completion
            elif 'CYCLE COMPLETED' in line:
                if current_tier:
                    self.update_tier(current_tier, status='completed')

                # Load trade sheet
                self.load_trade_sheet()
                live.update(self.generate_layout())

            # Parse results
            if current_tier and ('Fetched' in line or 'Stored' in line or 'Index' in line or 'opportunities' in line.lower()):
                if ' - INFO - ' in line:
                    msg = line.split(' - INFO - ')[-1]
                elif ' - WARNING - ' in line:
                    msg = line.split(' - WARNING - ')[-1]
                else:
                    msg = line

                msg = msg.encode('ascii', 'ignore').decode('ascii')

                tier_key = f'tier{current_tier}'
                results = self.tier_status[tier_key]['results']
                results.append(msg)
                self.tier_status[tier_key]['results'] = results[-6:]
                self.tier_status[tier_key]['count'] += 1

                live.update(self.generate_layout())

        process.wait()

    def run(self):
        """Run the persistent monitoring TUI - REAL DATA ONLY"""
        try:
            with Live(
                self.generate_layout(),
                console=console,
                screen=True,
                refresh_per_second=2
            ) as live:

                # Run continuously - NO FAKE DATA
                self.run_agents_continuous(live)

        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped by user[/]")

        console.print("\n[bold green]" + "=" * 70 + "[/]")
        console.print(f"[bold green]Monitoring Complete - Ran {self.cycle_count} cycles[/]")
        console.print("[bold green]" + "=" * 70 + "[/]")


def main():
    """Main entry point - REAL DATA ONLY"""
    parser = argparse.ArgumentParser(
        description='Spartan COT Agents - Persistent Monitor (REAL DATA ONLY)'
    )
    parser.add_argument('--demo', action='store_true', help='Run 4 agents instead of 100')
    parser.add_argument('--interval', type=int, default=1, help='Hours between cycles (default: 1)')

    args = parser.parse_args()

    console.clear()

    console.print("\n[bold cyan]" + "=" * 70 + "[/]")
    console.print("[bold cyan]SPARTAN COT AGENTS - Persistent Market Monitoring[/]")
    console.print("[bold cyan]" + "=" * 70 + "[/]\n")
    console.print(f"[yellow]Mode:[/] {'Demo (4 agents)' if args.demo else 'Production (100 agents)'}")
    console.print(f"[yellow]Interval:[/] {args.interval} hour(s)")
    console.print(f"[yellow]Started:[/] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print("\n[dim]Press Ctrl+C to stop monitoring[/]\n")

    time.sleep(2)

    tui = COTMonitorTUI(demo_mode=args.demo, interval_hours=args.interval)
    tui.run()


if __name__ == '__main__':
    main()
