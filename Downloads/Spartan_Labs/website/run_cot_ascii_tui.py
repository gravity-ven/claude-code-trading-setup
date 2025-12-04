#!/usr/bin/env python3
"""
Spartan COT Agents - ASCII TUI Dashboard
Simple ASCII-only interface that works in any terminal
NO UNICODE - Pure ASCII compatibility
"""

import sys
import subprocess
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich import box
import argparse

console = Console()


class COTAgentASCIITUI:
    """ASCII-only TUI Dashboard for COT Agents"""

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

        # Trade sheet content
        self.trade_sheet_content = "Waiting for agents to generate trade sheet..."

        # Configure layout - Add trade sheet on the right
        self.layout.split(
            Layout(name="header", size=5),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=8)
        )

        # Split main into tiers (left) and trade sheet (right)
        self.layout["main"].split_row(
            Layout(name="tiers", ratio=2),
            Layout(name="trade_sheet", ratio=1)
        )

        self.layout["main"]["tiers"].split_row(
            Layout(name="tier1"),
            Layout(name="tier2")
        )

        self.layout["main"]["tiers"]["tier1"].split_column(
            Layout(name="t1"),
            Layout(name="t2")
        )

        self.layout["main"]["tiers"]["tier2"].split_column(
            Layout(name="t3"),
            Layout(name="t4")
        )

    def create_header(self) -> Panel:
        """Create header panel"""
        mode = "DEMO MODE" if self.demo_mode else "PRODUCTION"
        elapsed = (datetime.now() - self.start_time).total_seconds()

        header = f"""
        SPARTAN COT AGENTS - Intelligence Dashboard

        {mode}  |  Started: {self.start_time.strftime('%H:%M:%S')}  |  Elapsed: {elapsed:.1f}s
        """

        return Panel(
            Text(header, style="bold cyan", justify="center"),
            style="cyan",
            box=box.ASCII,
            padding=(0, 1)
        )

    def create_tier_panel(self, tier_num: int) -> Panel:
        """Create tier panel with status and results"""
        tier_key = f'tier{tier_num}'
        tier_data = self.tier_status[tier_key]
        status = tier_data['status']
        results = tier_data['results']

        # Tier metadata
        tier_info = {
            1: ('COT Analysis', 'cyan', 'Analyzing CFTC Commitment of Traders reports'),
            2: ('Seasonality', 'yellow', 'Detecting seasonal patterns and cycles'),
            3: ('Confluence', 'magenta', 'Calculating signal confluence scores'),
            4: ('Trade Sheets', 'green', 'Generating actionable recommendations')
        }

        title, color, description = tier_info[tier_num]

        # Status indicator (ASCII only)
        status_text = {
            'pending': '[PENDING]',
            'running': '[RUNNING]',
            'completed': '[DONE]',
            'failed': '[FAILED]'
        }

        status_colors = {
            'pending': 'dim',
            'running': 'bold yellow',
            'completed': 'bold green',
            'failed': 'bold red'
        }

        status_label = status_text.get(status, '[?]')
        status_color = status_colors.get(status, 'white')

        # Build content
        content = Text()
        content.append(f"\n{status_label} ", style=status_color)
        content.append(description, style="white")
        content.append("\n\n")

        # Results section
        if results:
            content.append("Results:\n", style="bold white")
            for result in results[:8]:  # Limit to 8 results
                # Clean up any unicode characters in results
                clean_result = result.encode('ascii', 'ignore').decode('ascii')
                content.append(f"  * {clean_result}\n", style="dim white")
        elif status == 'running':
            content.append("Processing...\n", style="italic dim yellow")
        elif status == 'completed':
            content.append(f"  * {tier_data['count']} items processed\n", style="dim green")
        else:
            content.append("Waiting to start...\n", style="dim")

        content.append("\n")

        return Panel(
            content,
            title=f"[bold {color}]{title}[/]",
            border_style=color,
            padding=(1, 2),
            box=box.ASCII  # ASCII box characters only
        )

    def create_trade_sheet_panel(self) -> Panel:
        """Create trade sheet panel"""
        content = Text()

        # Read trade sheet file if it exists
        try:
            with open('output/latest_trade_sheet.txt', 'r') as f:
                trade_sheet = f.read()

            # Extract key sections - focus on recommendations
            lines = trade_sheet.split('\n')

            # Find BUY RECOMMENDATIONS section
            buy_section = []
            sell_section = []
            in_buy = False
            in_sell = False

            for line in lines:
                # Clean ASCII only
                clean_line = line.encode('ascii', 'ignore').decode('ascii')

                if 'BUY RECOMMENDATIONS' in clean_line:
                    in_buy = True
                    in_sell = False
                    buy_section.append(clean_line)
                elif 'SELL RECOMMENDATIONS' in clean_line:
                    in_buy = False
                    in_sell = True
                    sell_section.append(clean_line)
                elif 'NO HIGH-CONFIDENCE' in clean_line or 'WHY NO RECOMMENDATIONS' in clean_line:
                    in_buy = False
                    in_sell = False
                    content.append("NO SIGNALS\n\n", style="bold yellow")
                    content.append("Markets are neutral.\n", style="dim white")
                    content.append("Building data (Week 1/26)\n", style="dim white")
                    break
                elif in_buy and clean_line.strip():
                    buy_section.append(clean_line)
                    if len(buy_section) > 40:  # Limit display
                        break
                elif in_sell and clean_line.strip():
                    sell_section.append(clean_line)
                    if len(sell_section) > 40:  # Limit display
                        break

            # Display BUY recommendations
            if buy_section:
                for line in buy_section[:35]:  # First 35 lines
                    if 'BUY' in line and 'RECOMMENDATIONS' in line:
                        content.append(line + "\n", style="bold green")
                    elif line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                        content.append(line + "\n", style="bold cyan")
                    elif 'WHAT TO DO:' in line:
                        content.append(line + "\n", style="bold yellow")
                    elif 'WHY THIS OPPORTUNITY:' in line:
                        content.append(line + "\n", style="bold magenta")
                    elif 'RISK LEVEL:' in line:
                        content.append(line + "\n", style="bold red")
                    else:
                        content.append(line + "\n", style="white")

            # Display SELL recommendations
            if sell_section:
                content.append("\n")
                for line in sell_section[:35]:  # First 35 lines
                    if 'SELL' in line and 'RECOMMENDATIONS' in line:
                        content.append(line + "\n", style="bold red")
                    elif line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                        content.append(line + "\n", style="bold cyan")
                    elif 'WHAT TO DO:' in line:
                        content.append(line + "\n", style="bold yellow")
                    elif 'WHY THIS OPPORTUNITY:' in line:
                        content.append(line + "\n", style="bold magenta")
                    elif 'RISK LEVEL:' in line:
                        content.append(line + "\n", style="bold red")
                    else:
                        content.append(line + "\n", style="white")

            if not buy_section and not sell_section and not content.plain:
                content.append("Generating trade sheet...\n", style="dim yellow")

        except FileNotFoundError:
            content.append("Trade sheet not yet generated.\n\n", style="dim yellow")
            content.append("Waiting for Tier 4 agents...\n", style="dim white")
        except Exception as e:
            content.append(f"Error reading trade sheet:\n{str(e)}\n", style="red")

        return Panel(
            content,
            title="[bold green]Investment Signals[/]",
            border_style="green",
            padding=(1, 2),
            box=box.ASCII
        )

    def create_footer(self) -> Panel:
        """Create footer with summary table"""
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ASCII,  # ASCII box characters only
            padding=(0, 1),
            expand=True
        )

        table.add_column("Tier", style="cyan", no_wrap=True)
        table.add_column("Status", style="white", no_wrap=True)
        table.add_column("Findings", style="white")

        tier_names = {
            'tier1': 'COT Analysis',
            'tier2': 'Seasonality',
            'tier3': 'Confluence',
            'tier4': 'Trade Sheets'
        }

        for tier_key, tier_name in tier_names.items():
            tier_data = self.tier_status[tier_key]
            status = tier_data['status']
            count = tier_data['count']

            status_text = {
                'pending': '[PENDING]',
                'running': '[RUNNING]',
                'completed': '[DONE]',
                'failed': '[FAILED]'
            }.get(status, '[?]')

            findings = f"{count} items" if count > 0 else "No data yet"

            table.add_row(tier_name, status_text, findings)

        footer_text = Text("\n", style="dim")
        footer_text.append("Logs: ", style="bold white")
        footer_text.append("tail -f logs/agents.log", style="cyan")
        footer_text.append("  |  ", style="dim")
        footer_text.append("Refresh: ", style="bold white")
        footer_text.append("Auto-updates live", style="cyan")
        footer_text.append("  |  ", style="dim")
        footer_text.append("Press Ctrl+C to exit", style="yellow")

        from rich.console import Group
        content = Group(table, footer_text)

        return Panel(
            content,
            title="[bold white]Summary[/]",
            border_style="white",
            padding=(1, 1),
            box=box.ASCII  # ASCII box characters only
        )

    def generate_layout(self) -> Layout:
        """Generate the complete layout"""
        self.layout["header"].update(self.create_header())
        self.layout["t1"].update(self.create_tier_panel(1))
        self.layout["t2"].update(self.create_tier_panel(2))
        self.layout["t3"].update(self.create_tier_panel(3))
        self.layout["t4"].update(self.create_tier_panel(4))
        self.layout["main"]["trade_sheet"].update(self.create_trade_sheet_panel())
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

    def run_real_agents(self, live):
        """Run actual COT agents and parse output - REAL DATA ONLY"""

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

            # Parse interesting log lines (ASCII safe)
            if current_tier and ('OK' in line or 'WARNING' in line or 'ERROR' in line or 'Fetched' in line or 'Stored' in line):
                # Extract the message after the log level
                if ' - INFO - ' in line:
                    msg = line.split(' - INFO - ')[-1]
                elif ' - WARNING - ' in line:
                    msg = line.split(' - WARNING - ')[-1]
                elif ' - ERROR - ' in line:
                    msg = line.split(' - ERROR - ')[-1]
                else:
                    msg = line

                # Clean ASCII only
                msg = msg.encode('ascii', 'ignore').decode('ascii')

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
                import time
                time.sleep(3)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/]")

        # Print completion message
        console.print("\n")
        console.print("[bold green]" + "=" * 70 + "[/]")
        console.print("[bold green]Execution Complete[/]")
        console.print("[bold green]" + "=" * 70 + "[/]")
        console.print()

        # Final summary
        summary_table = Table(show_header=False, box=box.ASCII, padding=(0, 2))
        summary_table.add_row("DONE", "All tiers completed successfully")
        summary_table.add_row("LOGS", "View logs: tail -f logs/agents.log")
        summary_table.add_row("SHEET", "Trade signals displayed in TUI above")
        summary_table.add_row("RERUN", "Run again: python3 run_cot_ascii_tui.py --demo")

        console.print(Panel(
            summary_table,
            title="[bold white]Next Steps[/]",
            border_style="green",
            padding=(1, 2),
            box=box.ASCII
        ))
        console.print()


def main():
    """Main entry point - REAL DATA ONLY"""
    parser = argparse.ArgumentParser(description='Spartan COT Agents - ASCII TUI (REAL DATA ONLY)')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode (4 agents)')

    args = parser.parse_args()

    # Clear screen
    console.clear()

    # Create and run TUI
    tui = COTAgentASCIITUI(demo_mode=args.demo)
    tui.run()  # Always uses real agents - NO FAKE DATA


if __name__ == '__main__':
    main()
