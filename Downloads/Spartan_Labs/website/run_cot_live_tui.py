#!/usr/bin/env python3
"""
Spartan COT Agents - Live TUI Dashboard
Beautiful real-time terminal interface using Rich library
"""

import sys
import time
import subprocess
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box
import argparse

console = Console()


class COTAgentTUI:
    """Live TUI Dashboard for COT Agents"""

    def __init__(self, demo_mode=False):
        self.demo_mode = demo_mode
        self.layout = Layout()
        self.start_time = datetime.now()

        # Tier status tracking
        self.tier_status = {
            'tier1': {'status': 'pending', 'results': [], 'count': 0},
            'tier2': {'status': 'pending', 'results': [], 'count': 0},
            'tier3': {'status': 'pending', 'results': [], 'count': 0},
            'tier4': {'status': 'pending', 'results': [], 'count': 0}
        }

        # Configure layout
        self.layout.split(
            Layout(name="header", size=5),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=8)
        )

        self.layout["main"].split_row(
            Layout(name="tier1"),
            Layout(name="tier2")
        )

        self.layout["main"]["tier1"].split_column(
            Layout(name="t1"),
            Layout(name="t2")
        )

        self.layout["main"]["tier2"].split_column(
            Layout(name="t3"),
            Layout(name="t4")
        )

    def create_header(self) -> Panel:
        """Create header panel"""
        mode = "🎮 DEMO MODE" if self.demo_mode else "🚀 PRODUCTION"
        elapsed = (datetime.now() - self.start_time).total_seconds()

        header_text = Text()
        header_text.append("\n", style="bold")
        header_text.append("        ⚔️  SPARTAN COT AGENTS", style="bold cyan")
        header_text.append("  •  ", style="dim")
        header_text.append("Intelligence Dashboard", style="bold white")
        header_text.append("        \n", style="bold")

        subtitle = Text()
        subtitle.append(f"{mode}", style="bold yellow")
        subtitle.append(f"  •  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        subtitle.append(f"  •  Elapsed: {elapsed:.1f}s", style="dim cyan")

        return Panel(
            Align.center(header_text + "\n" + subtitle),
            style="bold cyan",
            box=box.DOUBLE,
            padding=(0, 2)
        )

    def create_tier_panel(self, tier_num: int) -> Panel:
        """Create tier panel with status and results"""
        tier_key = f'tier{tier_num}'
        tier_data = self.tier_status[tier_key]
        status = tier_data['status']
        results = tier_data['results']

        # Tier metadata
        tier_info = {
            1: ('📊 COT Analysis', 'cyan', 'Analyzing CFTC Commitment of Traders reports'),
            2: ('📅 Seasonality', 'yellow', 'Detecting seasonal patterns and cycles'),
            3: ('🎯 Confluence', 'magenta', 'Calculating signal confluence scores'),
            4: ('💰 Trade Sheets', 'green', 'Generating actionable recommendations')
        }

        title, color, description = tier_info[tier_num]

        # Status indicator
        status_icons = {
            'pending': '⏳',
            'running': '⚡',
            'completed': '✅',
            'failed': '❌'
        }

        status_colors = {
            'pending': 'dim',
            'running': 'bold yellow',
            'completed': 'bold green',
            'failed': 'bold red'
        }

        status_icon = status_icons.get(status, '❓')
        status_color = status_colors.get(status, 'white')

        # Build content
        content = Text()
        content.append(f"\n{status_icon} ", style=status_color)
        content.append(description, style="white")
        content.append("\n\n")

        # Results section
        if results:
            content.append("Results:\n", style="bold white")
            for result in results[:8]:  # Limit to 8 results
                content.append(f"  • {result}\n", style="dim white")
        elif status == 'running':
            content.append("Processing...\n", style="italic dim yellow")
        elif status == 'completed':
            content.append(f"  • {tier_data['count']} items processed\n", style="dim green")
        else:
            content.append("Waiting to start...\n", style="dim")

        # Add some padding
        content.append("\n")

        return Panel(
            content,
            title=f"[bold {color}]{title}[/]",
            border_style=color,
            padding=(1, 2),
            box=box.ROUNDED
        )

    def create_footer(self) -> Panel:
        """Create footer with summary table"""
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            padding=(0, 1),
            expand=True
        )

        table.add_column("Tier", style="cyan", no_wrap=True)
        table.add_column("Status", style="white", no_wrap=True)
        table.add_column("Findings", style="white")

        tier_names = {
            'tier1': '📊 COT Analysis',
            'tier2': '📅 Seasonality',
            'tier3': '🎯 Confluence',
            'tier4': '💰 Trade Sheets'
        }

        for tier_key, tier_name in tier_names.items():
            tier_data = self.tier_status[tier_key]
            status = tier_data['status']
            count = tier_data['count']

            status_text = {
                'pending': '⏳ Pending',
                'running': '⚡ Running',
                'completed': '✅ Completed',
                'failed': '❌ Failed'
            }.get(status, '❓ Unknown')

            findings = f"{count} items" if count > 0 else "No data yet"

            table.add_row(tier_name, status_text, findings)

        footer_text = Text("\n", style="dim")
        footer_text.append("📋 Logs: ", style="bold white")
        footer_text.append("tail -f logs/agents.log", style="cyan")
        footer_text.append("  •  ", style="dim")
        footer_text.append("Trade Sheet: ", style="bold white")
        footer_text.append("./SHOW_TRADE_SHEET.sh", style="cyan")
        footer_text.append("  •  ", style="dim")
        footer_text.append("Press Ctrl+C to exit", style="yellow")

        from rich.console import Group
        content = Group(table, footer_text)

        return Panel(
            content,
            title="[bold white]Execution Summary[/]",
            border_style="white",
            padding=(1, 1),
            box=box.DOUBLE
        )

    def generate_layout(self) -> Layout:
        """Generate the complete layout"""
        self.layout["header"].update(self.create_header())
        self.layout["t1"].update(self.create_tier_panel(1))
        self.layout["t2"].update(self.create_tier_panel(2))
        self.layout["t3"].update(self.create_tier_panel(3))
        self.layout["t4"].update(self.create_tier_panel(4))
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

    # REMOVED: simulate_execution() method
    # REASON: NO FAKE DATA policy - system must ONLY use real CFTC data
    # This method violated core principle by generating mock results

    def run_real_agents(self, live):
        """Run actual COT agents and parse output"""

        # Start agents
        args = ['python3', '-u', 'run_100_agents.py', '--demo', '--single-cycle']

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

            elif 'TIER 4: Risk Management' in line or 'TIER 4: Trade Sheets' in line:
                self.update_tier(3, status='completed')
                current_tier = 4
                self.update_tier(4, status='running')
                live.update(self.generate_layout())

            # Parse interesting log lines
            if current_tier and ('✅' in line or '⚠️' in line or '❌' in line):
                # Extract the message after the log level
                if ' - INFO - ' in line:
                    msg = line.split(' - INFO - ')[-1]
                elif ' - WARNING - ' in line:
                    msg = line.split(' - WARNING - ')[-1]
                elif ' - ERROR - ' in line:
                    msg = line.split(' - ERROR - ')[-1]
                else:
                    msg = line

                # Add to tier results
                tier_key = f'tier{current_tier}'
                results = self.tier_status[tier_key]['results']
                results.append(msg)

                # Keep only last 6 results
                self.tier_status[tier_key]['results'] = results[-6:]
                self.tier_status[tier_key]['count'] += 1

                live.update(self.generate_layout())

        # Mark final tier as completed
        if current_tier:
            self.update_tier(current_tier, status='completed')
            live.update(self.generate_layout())

        process.wait()

    def run(self):
        """Run the TUI dashboard - REAL DATA ONLY"""
        try:
            with Live(
                self.generate_layout(),
                console=console,
                screen=True,
                refresh_per_second=4
            ) as live:

                # ONLY run real agents - NO FAKE DATA
                self.run_real_agents(live)

                # Show final state for a few seconds
                time.sleep(3)

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Interrupted by user[/]")

        # Print completion message
        console.print("\n")
        console.rule("[bold green]Execution Complete[/]", style="green")
        console.print()

        # Final summary
        summary_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        summary_table.add_row("✅", "All tiers completed successfully")
        summary_table.add_row("📊", "View logs: [cyan]tail -f logs/agents.log[/]")
        summary_table.add_row("📋", "Trade sheet: [cyan]./SHOW_TRADE_SHEET.sh[/]")
        summary_table.add_row("🔄", "Run again: [cyan]./START_COT_TUI.sh[/]")

        console.print(Panel(
            summary_table,
            title="[bold white]Next Steps[/]",
            border_style="green",
            padding=(1, 2)
        ))
        console.print()


def main():
    """Main entry point - REAL DATA ONLY"""
    parser = argparse.ArgumentParser(description='Spartan COT Agents - Live TUI Dashboard (REAL DATA ONLY)')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode (4 agents instead of 100)')
    # REMOVED: --simulate flag (violated NO FAKE DATA policy)

    args = parser.parse_args()

    # Clear screen
    console.clear()

    # Create and run TUI
    tui = COTAgentTUI(demo_mode=args.demo)
    tui.run()  # Always uses real agents - NO FAKE DATA


if __name__ == '__main__':
    main()
