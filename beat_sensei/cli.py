#!/usr/bin/env python3
"""Beat-Sensei CLI - Your Sample Library Curator."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.style import Style
from rich import box

from .chatbot.sensei import BeatSensei
from .utils.config import Config

app = typer.Typer(
    name="beat-sensei",
    help="Your Sample Library Curator",
    no_args_is_help=False,
    invoke_without_command=True,
)

console = Console()

# Styles
SENSEI_STYLE = Style(color="cyan", bold=True)
USER_STYLE = Style(color="green")


def get_banner() -> str:
    """Get the Beat-Sensei ASCII banner."""
    return """
[bold cyan]
 ____  _____    _  _____   ____  _____ _   _ ____  _____ ___
| __ )| ____|  / \|_   _| / ___|| ____| \ | / ___|| ____|_ _|
|  _ \|  _|   / _ \ | |   \___ \|  _| |  \| \___ \|  _|  | |
| |_) | |___ / ___ \| |    ___) | |___| |\  |___) | |___ | |
|____/|_____/_/   \_\_|   |____/|_____|_| \_|____/|_____|___|
[/bold cyan]
[dim]Your Sample Library Curator[/dim]
"""


@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    """Run interactive chat if no command is provided."""
    if ctx.invoked_subcommand is None:
        run_chat()


def create_sensei(config: Config) -> BeatSensei:
    """Create and initialize Beat-Sensei."""
    return BeatSensei(
        supabase_url=config.supabase_url,
        supabase_anon_key=config.supabase_anon_key,
        deepseek_api_key=config.deepseek_api_key,
    )


def run_chat():
    """Run the interactive Beat-Sensei chat."""
    config = Config.load()
    sensei = create_sensei(config)
    stats = sensei.get_stats()

    # Display header
    console.print(get_banner())
    
    # Show library status
    if stats['sample_db_available']:
        status_msg = f"[bold]Sample Library:[/bold] [green]Ready ({stats.get('total_samples', 0)} samples)[/green]"
    else:
        status_msg = "[bold]Sample Library:[/bold] [yellow]Not configured[/yellow]"
    
    console.print(Panel(
        status_msg,
        title="[bold cyan]Status[/bold cyan]",
        border_style="cyan",
    ))

    # Show greeting
    greeting = "Yo! I'm your sample library curator. What sound are you looking for?"
    console.print(f"\n[bold cyan]Sensei:[/bold cyan] {greeting}\n")

    # Main chat loop
    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]")

            if not user_input.strip():
                continue

            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                console.print("\n[cyan]Sensei:[/cyan] Keep digging for sounds! Hit me up when you need more.")
                break

            # Check for help
            if user_input.lower() in ['help', '?', '/help']:
                show_help()
                continue

            # Process message
            with console.status("[cyan]Sensei searching library...[/cyan]", spinner="dots"):
                response, action_data = sensei.chat(user_input)

            # Display response
            console.print(f"\n[bold cyan]Sensei:[/bold cyan] {response}")

            # Handle action data
            if action_data:
                if action_data.get('type') == 'play_sample':
                    console.print(f"\n[green]Sample URL:[/green] {action_data['url']}")

            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[cyan]Sensei:[/cyan] Catch you later! The sample vault is always open.")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def chat():
    """Start interactive Beat-Sensei chat."""
    run_chat()


@app.command()
def config():
    """Show configuration and status."""
    cfg = Config.load()

    console.print(get_banner())

    table = Table(title="Beat-Sensei Status", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Supabase Library", "[green]Ready[/green]" if cfg.supabase_url and cfg.supabase_anon_key else "[yellow]Not configured[/yellow]")
    table.add_row("Output Folder", cfg.output_folder)

    console.print(table)

    if not cfg.supabase_url or not cfg.supabase_anon_key:
        console.print("\n[bold]To set up your sample library:[/bold]")
        console.print("1. Create a Supabase project at [cyan]supabase.com[/cyan]")
        console.print("2. Get your URL and anon key from Project Settings > API")
        console.print("3. Run: [green]export SUPABASE_URL=your_url[/green]")
        console.print("4. Run: [green]export SUPABASE_ANON_KEY=your_key[/green]")
        console.print("\n[dim]Or add them to your .env file[/dim]")


@app.command()
def library():
    """Check Supabase sample library status and stats."""
    from .database.supabase_client import SampleDatabase

    config = Config.load()

    if not config.supabase_url or not config.supabase_anon_key:
        console.print("[yellow]Supabase not configured.[/yellow]")
        console.print("\n[bold]To set up your sample library:[/bold]")
        console.print("1. Create a Supabase project at [cyan]supabase.com[/cyan]")
        console.print("2. Get your URL and anon key from Project Settings > API")
        console.print("3. Run: [green]export SUPABASE_URL=your_url[/green]")
        console.print("4. Run: [green]export SUPABASE_ANON_KEY=your_key[/green]")
        console.print("\n[dim]Or add them to your .env file[/dim]")
        return

    console.print("\n[bold cyan]Sample Library Status[/bold cyan]\n")

    db = SampleDatabase(url=config.supabase_url, key=config.supabase_anon_key)

    if not db.is_available():
        console.print("[red]Could not connect to Supabase.[/red]")
        console.print("[dim]Check your URL and API key.[/dim]")
        return

    console.print("[green]✓ Connected to Supabase[/green]")

    # Get library stats
    categories = db.get_categories()

    if not categories:
        console.print("\n[yellow]Library is empty.[/yellow]")
        console.print("\n[bold]To add samples:[/bold]")
        console.print("1. Set SUPABASE_SERVICE_KEY (from Supabase Project Settings > API)")
        console.print("2. Run: [green]python scripts/upload_samples.py /path/to/samples[/green]")
        return

    total_samples = sum(categories.values())

    table = Table(title=f"Sample Library ({total_samples} samples)", box=box.ROUNDED)
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Examples", style="dim")

    # Get example samples for each category
    for category, count in sorted(categories.items(), key=lambda x: -x[1]):
        examples = db.get_by_category(category, limit=2)
        example_names = [s.name[:15] + "..." if len(s.name) > 15 else s.name for s in examples[:2]]
        table.add_row(category, str(count), ", ".join(example_names))

    console.print(table)

    # Show random samples for inspiration
    console.print("\n[bold]Random samples for inspiration:[/bold]")
    random_samples = db.get_random(limit=3)
    for i, sample in enumerate(random_samples, 1):
        tags_str = ', '.join(sample.tags[:2]) if sample.tags else ''
        console.print(f"  {i}. [cyan]{sample.name}[/cyan] ({sample.category}) [dim]{tags_str}[/dim]")


@app.command()
def samples(
    query: str = typer.Argument(None, help="Search query (leave empty for random samples)"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category (kick, snare, hat, 808, loop, etc.)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results to show"),
):
    """Search samples in the library."""
    from .database.supabase_client import SampleDatabase

    config = Config.load()

    if not config.supabase_url or not config.supabase_anon_key:
        console.print("[yellow]Supabase not configured.[/yellow]")
        console.print("\n[bold]To use the sample library:[/bold]")
        console.print("1. Create a Supabase project at [cyan]supabase.com[/cyan]")
        console.print("2. Get your URL and anon key from Project Settings > API")
        console.print("3. Run: [green]export SUPABASE_URL=your_url[/green]")
        console.print("4. Run: [green]export SUPABASE_ANON_KEY=your_key[/green]")
        raise typer.Exit(1)

    db = SampleDatabase(url=config.supabase_url, key=config.supabase_anon_key)

    if not db.is_available():
        console.print("[red]Could not connect to Supabase.[/red]")
        console.print("[dim]Check your URL and API key.[/dim]")
        raise typer.Exit(1)

    if query:
        console.print(f"\n[bold cyan]Searching for:[/bold cyan] {query}")
        if category:
            console.print(f"[dim]Category filter: {category}[/dim]")
        results = db.search(query, category=category, limit=limit)
    elif category:
        console.print(f"\n[bold cyan]Showing {category}s:[/bold cyan]")
        results = db.get_by_category(category, limit=limit)
    else:
        console.print(f"\n[bold cyan]Random samples for inspiration:[/bold cyan]")
        results = db.get_random(limit=limit)

    if not results:
        console.print("\n[yellow]No samples found.[/yellow]")
        console.print("\n[dim]Try a different search, or browse categories: kicks, snares, hats, 808s, loops[/dim]")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Pack", style="dim")
    table.add_column("Tags", style="dim")

    for i, sample in enumerate(results, 1):
        tags_str = ', '.join(sample.tags[:2]) if sample.tags else ''
        if len(tags_str) > 20:
            tags_str = tags_str[:17] + "..."

        table.add_row(
            str(i),
            sample.name[:30] + "..." if len(sample.name) > 30 else sample.name,
            sample.category,
            sample.pack_name[:15] + "..." if len(sample.pack_name) > 15 else sample.pack_name,
            tags_str
        )

    console.print(table)

    # Show URLs for first few samples
    console.print("\n[bold]Preview URLs:[/bold]")
    for i, sample in enumerate(results[:3], 1):
        console.print(f"  {i}. {sample.file_url}")

    console.print(f"\n[dim]Use these in your DAW, or ask Sensei to recommend sounds for your track.[/dim]")


def show_help():
    """Show help information."""
    console.print("\n[bold cyan]Beat-Sensei Commands[/bold cyan]\n")

    help_table = Table(box=box.ROUNDED, show_header=False)
    help_table.add_column("Command", style="cyan", width=25)
    help_table.add_column("Description", style="white")

    commands = [
        ("samples <query>", "Search sample library"),
        ("kicks / snares / 808s", "Browse by category"),
        ("loops", "Browse sample loops"),
        ("random", "Get random samples"),
        ("play <number>", "Preview a sample"),
        ("help", "Show this help"),
        ("quit", "Exit Beat-Sensei"),
    ]

    for cmd, desc in commands:
        help_table.add_row(cmd, desc)

    console.print(help_table)

    console.print("\n[bold]Tips for better results:[/bold]")
    console.print("  - Be specific: 'dark trap kicks', 'jazzy loops', 'aggressive 808s'")
    console.print("  - Use categories: kicks, snares, hats, 808s, loops")
    console.print("  - All samples are production-ready WAV files")
    console.print("\n[bold]Sample library:[/bold]")
    console.print("  - Type 'kicks', 'snares', 'hats', '808s', 'loops' to browse")
    console.print("  - Type 'search dark trap' to find matching samples")
    console.print("  - Type 'random' for inspiration")
    console.print()


def run():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()