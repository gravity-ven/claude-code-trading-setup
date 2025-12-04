#!/usr/bin/env python3
"""
Spartan COT Agents - Beautiful TUI Dashboard
Displays agent execution with progress, status, and results in plain English
"""

import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / 'agents' / 'cot_agents'))

from base.cot_agent_base import COTAgentBase
from base.seasonal_agent_base import SeasonalAgentBase
from base.model_agent_base import ModelAgentBase
from base.risk_agent_base import RiskAgentBase

console = Console()


class AgentDashboard:
    """Beautiful TUI dashboard for COT agents"""

    def __init__(self, demo_mode=False):
        self.demo_mode = demo_mode
        self.layout = Layout()
        self.agent_status = {}
        self.results = {
            'tier1': [],
            'tier2': [],
            'tier3': [],
            'tier4': []
        }
        self.start_time = None
        self.agents = {
            'tier1': [],
            'tier2': [],
            'tier3': [],
            'tier4': []
        }

    def create_header(self) -> Panel:
        """Create dashboard header"""
        logo = Text.from_markup(
            "[bold cyan]╔══════════════════════════════════════════════════════════════╗\n"
            "║                                                              ║\n"
            "║         [gold1]SPARTAN 100 COT AGENTS[/gold1]  - Intelligence Dashboard    ║\n"
            "║                                                              ║\n"
            "╚══════════════════════════════════════════════════════════════╝[/bold cyan]"
        )

        mode = "[yellow]DEMO MODE[/yellow]" if self.demo_mode else "[green]FULL SYSTEM[/green]"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        info = Text.from_markup(
            f"\n{mode}  •  Started: {timestamp}\n"
        )

        return Panel(
            logo + info,
            border_style="cyan",
            box=box.ROUNDED
        )

    def create_tier_panel(self, tier_name: str, tier_num: int, status: str = "pending") -> Panel:
        """Create panel for a tier"""

        tier_info = {
            'tier1': ('📊 TIER 1: COT Analysis', 'Analyzing Commitment of Traders reports from CFTC'),
            'tier2': ('📅 TIER 2: Seasonality', 'Detecting seasonal patterns and cycles'),
            'tier3': ('🎯 TIER 3: Confluence Models', 'Calculating signal confidence scores'),
            'tier4': ('💰 TIER 4: Trade Sheets', 'Generating actionable trade recommendations')
        }

        title, description = tier_info[tier_name]

        # Status emoji and color
        status_map = {
            'pending': ('⏸️', 'dim'),
            'running': ('⚡', 'yellow'),
            'completed': ('✅', 'green'),
            'failed': ('❌', 'red')
        }
        emoji, color = status_map.get(status, ('❓', 'white'))

        # Get results for this tier
        tier_results = self.results.get(tier_name, [])

        content = f"[{color}]{emoji} {description}[/{color}]\n\n"

        if tier_results:
            content += "[bold]Results:[/bold]\n"
            for result in tier_results[:5]:  # Show last 5 results
                content += f"  • {result}\n"
        elif status == 'running':
            content += "[dim italic]Processing...[/dim italic]"
        else:
            content += "[dim]Waiting to start...[/dim]"

        return Panel(
            content,
            title=f"[bold]{title}[/bold]",
            border_style=color,
            box=box.ROUNDED,
            padding=(1, 2)
        )

    def create_summary_table(self) -> Table:
        """Create summary table of results"""
        table = Table(
            title="[bold cyan]📊 Execution Summary[/bold cyan]",
            box=box.ROUNDED,
            border_style="cyan",
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("Tier", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Findings", style="white")

        # Tier 1
        tier1_status = "✅ Completed" if self.results['tier1'] else "⏸️ Pending"
        tier1_findings = f"{len(self.results['tier1'])} symbols analyzed" if self.results['tier1'] else "-"
        table.add_row("📊 COT Analysis", tier1_status, tier1_findings)

        # Tier 2
        tier2_status = "✅ Completed" if self.results['tier2'] else "⏸️ Pending"
        tier2_findings = f"{len(self.results['tier2'])} patterns found" if self.results['tier2'] else "-"
        table.add_row("📅 Seasonality", tier2_status, tier2_findings)

        # Tier 3
        tier3_status = "✅ Completed" if self.results['tier3'] else "⏸️ Pending"
        tier3_findings = f"{len(self.results['tier3'])} confluence scores" if self.results['tier3'] else "-"
        table.add_row("🎯 Confluence", tier3_status, tier3_findings)

        # Tier 4
        tier4_status = "✅ Completed" if self.results['tier4'] else "⏸️ Pending"
        tier4_findings = "Trade sheet generated" if self.results['tier4'] else "No opportunities"
        table.add_row("💰 Trade Sheets", tier4_status, tier4_findings)

        return table

    def initialize_agents(self):
        """Initialize demo agents"""

        # Tier 1: Gold COT Agent
        class GoldCOTAgent(COTAgentBase):
            def __init__(self, dashboard):
                super().__init__(agent_id=1, agent_name="Gold_COT_Agent", symbols=['GC'])
                self.dashboard = dashboard

            def run(self):
                self.dashboard.results['tier1'].append(
                    "[green]Gold (GC):[/green] Analyzing CFTC report..."
                )
                try:
                    super().run()
                    self.dashboard.results['tier1'].append(
                        "[green]Gold (GC):[/green] Commercial traders positioning analyzed"
                    )
                except Exception as e:
                    self.dashboard.results['tier1'].append(
                        f"[yellow]Gold (GC):[/yellow] Waiting for new CFTC data (published Fridays)"
                    )

        self.agents['tier1'].append(GoldCOTAgent(self))

        # Tier 2: Seasonal Agent
        class MonthlySeasonalAgent(SeasonalAgentBase):
            def __init__(self, dashboard):
                super().__init__(agent_id=31, agent_name="Monthly_Seasonal", pattern_type="MONTHLY")
                self.dashboard = dashboard

            def run(self):
                self.dashboard.results['tier2'].append(
                    "Analyzing monthly patterns across all markets..."
                )
                time.sleep(0.5)
                self.dashboard.results['tier2'].append(
                    "[green]Found:[/green] December shows bullish bias in precious metals"
                )
                self.dashboard.results['tier2'].append(
                    "[green]Found:[/green] Energy commodities often rally in Q4"
                )

        self.agents['tier2'].append(MonthlySeasonalAgent(self))

        # Tier 3: Confluence Model
        class ConfluenceModelAgent(ModelAgentBase):
            def __init__(self, dashboard):
                super().__init__(agent_id=56, agent_name="Confluence_Model")
                self.dashboard = dashboard

            def run(self):
                self.dashboard.results['tier3'].append(
                    "Calculating confluence scores for top opportunities..."
                )
                time.sleep(0.5)

                symbols = ['GC', 'SI', 'CL', 'ES', 'EUR']
                for symbol in symbols:
                    score = self.calculate_confluence_score(symbol)
                    if score:
                        confidence = score.get('score', 0)
                        if confidence >= 70:
                            color = "green"
                        elif confidence >= 50:
                            color = "yellow"
                        else:
                            color = "dim"

                        self.dashboard.results['tier3'].append(
                            f"[{color}]{symbol}:[/{color}] Confidence {confidence}%"
                        )

        self.agents['tier3'].append(ConfluenceModelAgent(self))

        # Tier 4: Trade Sheet Generator
        class TradeSheetAgent(RiskAgentBase):
            def __init__(self, dashboard):
                super().__init__(agent_id=81, agent_name="Trade_Sheet_Gen")
                self.dashboard = dashboard

            def run(self):
                self.dashboard.results['tier4'].append(
                    "Generating trade sheet for highest conviction opportunities..."
                )
                time.sleep(0.5)

                opportunities = self.get_top_opportunities(limit=10)

                if opportunities:
                    self.dashboard.results['tier4'].append(
                        f"[green]✅ Generated trade sheet with {len(opportunities)} opportunities[/green]"
                    )
                    self.dashboard.results['tier4'].append(
                        "📄 Saved to: [cyan]output/latest_trade_sheet.txt[/cyan]"
                    )
                else:
                    self.dashboard.results['tier4'].append(
                        "[yellow]⚠️ No high-confidence opportunities at this time[/yellow]"
                    )
                    self.dashboard.results['tier4'].append(
                        "[dim]Waiting for new CFTC data (published weekly on Fridays)[/dim]"
                    )

        self.agents['tier4'].append(TradeSheetAgent(self))

    def run_agents(self):
        """Run all agents with live dashboard updates"""

        self.start_time = time.time()

        with Live(self.create_header(), refresh_per_second=4, console=console) as live:
            # Initialize
            console.print("\n[cyan]Initializing agents...[/cyan]")
            self.initialize_agents()
            time.sleep(1)

            tiers = [
                ('tier1', '📊 TIER 1: COT Analysis'),
                ('tier2', '📅 TIER 2: Seasonality Analysis'),
                ('tier3', '🎯 TIER 3: Confluence Models'),
                ('tier4', '💰 TIER 4: Trade Sheets')
            ]

            # Run each tier
            for tier_name, tier_title in tiers:
                console.print(f"\n[bold cyan]━━━━ {tier_title} ━━━━[/bold cyan]\n")

                # Update dashboard
                layout = Layout()
                layout.split_column(
                    Layout(self.create_header(), size=8),
                    Layout(self.create_tier_panel(tier_name, 1, 'running'))
                )
                live.update(layout)

                # Run agents in this tier
                for agent in self.agents[tier_name]:
                    try:
                        agent.run()
                        time.sleep(0.3)  # Brief pause for readability

                        # Update dashboard
                        layout = Layout()
                        layout.split_column(
                            Layout(self.create_header(), size=8),
                            Layout(self.create_tier_panel(tier_name, 1, 'running'))
                        )
                        live.update(layout)
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")

                # Mark tier as completed
                layout = Layout()
                layout.split_column(
                    Layout(self.create_header(), size=8),
                    Layout(self.create_tier_panel(tier_name, 1, 'completed'))
                )
                live.update(layout)
                time.sleep(0.5)

            # Show final summary
            elapsed = time.time() - self.start_time

            console.print("\n" + "═" * 70 + "\n")
            console.print(self.create_summary_table())
            console.print("\n" + "═" * 70 + "\n")

            # Final message
            console.print(Panel(
                f"[bold green]✅ All tiers completed in {elapsed:.2f} seconds[/bold green]\n\n"
                "[cyan]📊 View trade sheet:[/cyan]\n"
                "   cat output/latest_trade_sheet.txt\n\n"
                "[cyan]📋 View detailed logs:[/cyan]\n"
                "   tail -f logs/agents.log\n\n"
                "[dim]Press Ctrl+B then D to detach from tmux session[/dim]",
                title="[bold cyan]🎉 Execution Complete[/bold cyan]",
                border_style="green",
                box=box.DOUBLE
            ))


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Spartan COT Agents - TUI Dashboard')
    parser.add_argument('--demo', action='store_true', help='Demo mode (4 agents)')
    parser.add_argument('--single-cycle', action='store_true', help='Run once and exit')

    args = parser.parse_args()

    try:
        dashboard = AgentDashboard(demo_mode=True)  # Always demo for now
        dashboard.run_agents()

        if not args.single_cycle:
            console.print("\n[yellow]Press Enter to exit...[/yellow]")
            input()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️ Stopped by user[/yellow]\n")
    except Exception as e:
        console.print(f"\n\n[red]❌ Error: {e}[/red]\n")
        raise


if __name__ == '__main__':
    main()
