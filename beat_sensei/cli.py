#!/usr/bin/env python3
"""Beat-Sensei CLI - Your AI Sample Master."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.text import Text
from rich.style import Style
from rich import box

from .samples.scanner import SampleScanner
from .samples.search import SampleSearch
from .samples.player import SamplePlayer
from .chatbot.sensei import BeatSensei
from .auth.tiers import TierManager
from .utils.config import Config

app = typer.Typer(
    name="beat-sensei",
    help="Your AI Sample Master - Hip-Hop Edition",
    no_args_is_help=False,
    invoke_without_command=True,
)

console = Console()


@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    """Run interactive chat if no command is provided."""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, run the main chat
        main()

# Styles
SENSEI_STYLE = Style(color="cyan", bold=True)
USER_STYLE = Style(color="green")
RESULT_STYLE = Style(color="yellow")


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
[dim]Your AI Sample Master | Hip-Hop Edition[/dim]
"""


def display_search_results(results: list, console: Console):
    """Display search results in a nice table."""
    if not results:
        return

    table = Table(
        title="[bold yellow]Found Samples[/bold yellow]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Filename", style="cyan")
    table.add_column("BPM", justify="center", width=6)
    table.add_column("Key", justify="center", width=10)
    table.add_column("Category", justify="center", width=10)
    table.add_column("Tags", style="dim")

    for i, result in enumerate(results, 1):
        sample = result.sample
        bpm_str = f"{sample.bpm:.0f}" if sample.bpm else "-"
        key_str = sample.key or "-"
        cat_str = sample.category or "-"
        tags_str = ", ".join(sample.tags[:3]) if sample.tags else "-"

        table.add_row(
            str(i),
            sample.filename[:40],
            bpm_str,
            key_str,
            cat_str,
            tags_str,
        )

    console.print(table)
    console.print("\n[dim]Type a number to play, or describe what else you need.[/dim]\n")


def create_sensei(config: Config) -> BeatSensei:
    """Create and initialize Beat-Sensei."""
    scanner = SampleScanner()
    tier_manager = TierManager()

    # Scan configured folders
    for folder in config.sample_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            scanner.scan_folder(folder_path)

    return BeatSensei(
        scanner=scanner,
        tier_manager=tier_manager,
        api_key=config.replicate_api_token,
    )


@app.command()
def main(
    scan_first: Optional[str] = typer.Option(None, "--scan", "-s", help="Scan a folder before starting"),
):
    """Start interactive Beat-Sensei chat."""
    config = Config.load()

    # Scan additional folder if provided
    if scan_first:
        config.add_sample_folder(scan_first)

    sensei = create_sensei(config)
    stats = sensei.get_stats()

    # Display header
    console.print(get_banner())
    console.print(Panel(
        f"[bold]Sample Library:[/bold] {stats['samples_indexed']} samples indexed\n"
        f"[bold]Tier:[/bold] {sensei.tier_manager.get_tier_display()}",
        title="[bold cyan]Status[/bold cyan]",
        border_style="cyan",
    ))

    # Show greeting
    greeting = sensei.personality.get_greeting()
    console.print(f"\n[bold cyan]Sensei:[/bold cyan] {greeting}\n")

    # Main chat loop
    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]")

            if not user_input.strip():
                continue

            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                console.print("\n[cyan]Sensei:[/cyan] Peace out! Keep making heat. [bold yellow]")
                break

            # Check for help
            if user_input.lower() in ['help', '?', '/help']:
                show_help()
                continue

            # Process message
            with console.status("[cyan]Sensei thinking...[/cyan]", spinner="dots"):
                response, action_data = sensei.chat(user_input)

            # Display response
            console.print(f"\n[bold cyan]Sensei:[/bold cyan] {response}")

            # Handle action data
            if action_data:
                if action_data.get('type') == 'search_results':
                    display_search_results(action_data['results'], console)
                elif action_data.get('type') == 'playing':
                    console.print(f"[dim]Now playing: {action_data['file']}[/dim]")
                elif action_data.get('type') == 'generated':
                    console.print(f"[green]Generated and saved![/green]")
            else:
                console.print()

        except KeyboardInterrupt:
            console.print("\n\n[cyan]Sensei:[/cyan] Catch you later! Keep diggin'. [bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def scan(
    folder: str = typer.Argument(..., help="Folder to scan for samples"),
    analyze: bool = typer.Option(False, "--analyze", "-a", help="Analyze audio for BPM/key (slower)"),
):
    """Scan a folder for audio samples."""
    folder_path = Path(folder).expanduser()

    if not folder_path.exists():
        console.print(f"[red]Folder not found: {folder}[/red]")
        raise typer.Exit(1)

    scanner = SampleScanner()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Scanning {folder_path.name}...", total=None)
        new_samples = scanner.scan_folder(folder_path, analyze_audio=analyze)
        progress.update(task, completed=True)

    console.print(f"\n[green]Found {len(new_samples)} new samples![/green]")
    console.print(f"[dim]Total indexed: {scanner.get_sample_count()} samples[/dim]")

    # Update config
    config = Config.load()
    config.add_sample_folder(str(folder_path))
    config.save()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
):
    """Quick search for samples."""
    config = Config.load()
    scanner = SampleScanner()

    # Load existing index
    search_engine = SampleSearch(scanner)
    results = search_engine.search(query, limit=limit)

    if not results:
        console.print(f"[yellow]No samples found matching '{query}'[/yellow]")
        return

    display_search_results(results, console)


@app.command()
def play(filepath: str = typer.Argument(..., help="File to play")):
    """Play an audio file."""
    player = SamplePlayer()

    filepath_path = Path(filepath).expanduser()
    if not filepath_path.exists():
        console.print(f"[red]File not found: {filepath}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Playing: {filepath_path.name}[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    player.play(str(filepath_path))

    try:
        import time
        while player.is_playing():
            time.sleep(0.5)
    except KeyboardInterrupt:
        player.stop()
        console.print("\n[dim]Stopped.[/dim]")


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Description of the sample to generate"),
    duration: int = typer.Option(8, "--duration", "-d", help="Duration in seconds"),
):
    """Generate a new sample using AI (Pro feature)."""
    from .generator.replicate_client import ReplicateGenerator

    config = Config.load()
    generator = ReplicateGenerator(api_token=config.replicate_api_token)

    if not generator.is_available():
        console.print("[red]Replicate API token not set.[/red]")
        console.print("[dim]Set REPLICATE_API_TOKEN environment variable or add to config.[/dim]")
        raise typer.Exit(1)

    console.print(f"[cyan]Generating: {prompt}[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Cooking up your sample...", total=None)
        result = generator.generate(prompt, duration=float(duration))
        progress.update(task, completed=True)

    if result.success:
        console.print(f"\n[green]Done! Saved to:[/green] {result.filepath}")
    else:
        console.print(f"\n[red]Generation failed: {result.error}[/red]")


@app.command()
def config():
    """Show or edit configuration."""
    cfg = Config.load()

    table = Table(title="Beat-Sensei Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Sample Folders", "\n".join(cfg.sample_folders) or "(none)")
    table.add_row("Output Folder", cfg.output_folder)
    table.add_row("Default BPM", str(cfg.default_bpm))
    table.add_row("Audio Format", cfg.audio_format)
    table.add_row("Tier", cfg.tier)
    table.add_row("Replicate API", "" if cfg.replicate_api_token else "[red]Not set[/red]")
    table.add_row("OpenAI API", "" if cfg.openai_api_key else "[red]Not set[/red]")

    console.print(table)


@app.command()
def auth(license_key: str = typer.Argument(..., help="Your license key")):
    """Activate a Pro license."""
    tier_manager = TierManager()

    if tier_manager.activate_license(license_key):
        console.print(f"[green]License activated! You're now on {tier_manager.tier.value} tier.[/green]")

        # Save to config
        cfg = Config.load()
        cfg.license_key = license_key
        cfg.tier = tier_manager.tier.value
        cfg.save()
    else:
        console.print("[red]Invalid license key.[/red]")


@app.command()
def download(
    pack: str = typer.Argument(None, help="Pack to download: starter, drums, bass (or 'all')"),
    list_packs: bool = typer.Option(False, "--list", "-l", help="List available packs"),
    resources: bool = typer.Option(False, "--resources", "-r", help="Show free sample resources"),
):
    """Download free sample packs to get started."""
    from .samples.downloader import SampleDownloader, FREE_SAMPLE_RESOURCES, SAMPLE_PACKS

    downloader = SampleDownloader()

    # Show resources
    if resources:
        console.print("\n[bold cyan]Free Sample Resources[/bold cyan]\n")
        table = Table(box=box.ROUNDED)
        table.add_column("Site", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("URL", style="dim")

        for resource in FREE_SAMPLE_RESOURCES:
            table.add_row(resource["name"], resource["description"], resource["url"])

        console.print(table)
        console.print("\n[dim]Visit these sites to download more samples![/dim]\n")
        return

    # List available packs
    if list_packs or pack is None:
        console.print("\n[bold cyan]Available Sample Packs[/bold cyan]\n")
        table = Table(box=box.ROUNDED)
        table.add_column("Pack", style="cyan")
        table.add_column("Description", style="white")

        for pack_id, pack_info in SAMPLE_PACKS.items():
            table.add_row(pack_id, pack_info["description"])

        console.print(table)
        console.print("\n[dim]Download with: beat-sensei download <pack-name>[/dim]")
        console.print("[dim]Download all:  beat-sensei download all[/dim]")
        console.print("[dim]Free resources: beat-sensei download --resources[/dim]\n")
        return

    # Download packs with KUNG FU ANIMATION!
    from .utils.animations import KungFuAnimation
    import threading

    console.print(get_banner())

    if pack == "all":
        console.print("[bold cyan]Downloading all sample packs...[/bold cyan]")
        console.print("[dim]Enjoy the show while you wait![/dim]\n")

        # Start kung fu animation
        anim = KungFuAnimation(style="kungfu")
        download_results = []

        def do_downloads():
            for pack_name in SAMPLE_PACKS:
                success, msg, files = downloader.download_pack(pack_name)
                download_results.append((pack_name, success, msg, files))

        # Run downloads in background while animation plays
        download_thread = threading.Thread(target=do_downloads)
        anim.start()
        download_thread.start()
        download_thread.join()
        anim.stop()

        # Show results
        console.print("\n[bold green]Downloads complete![/bold green]")
        for pack_name, success, msg, files in download_results:
            if success:
                console.print(f"  [green]✓[/green] {pack_name}: {len(files)} samples")
            else:
                console.print(f"  [red]✗[/red] {pack_name}: {msg}")

    else:
        if pack not in SAMPLE_PACKS:
            console.print(f"[red]Unknown pack: {pack}[/red]")
            console.print("[dim]Use --list to see available packs[/dim]")
            raise typer.Exit(1)

        console.print(f"[bold cyan]Downloading {pack} pack...[/bold cyan]")
        console.print("[dim]Watch the masters train while you wait![/dim]\n")

        # Start kung fu animation
        anim = KungFuAnimation(style="kungfu")
        result_holder = []

        def do_download():
            result_holder.append(downloader.download_pack(pack))

        download_thread = threading.Thread(target=do_download)
        anim.start()
        download_thread.start()
        download_thread.join()
        anim.stop()

        success, msg, files = result_holder[0]

        if success:
            console.print(f"\n[green]{msg}[/green]")
        else:
            console.print(f"\n[red]{msg}[/red]")

    # Auto-scan downloaded folder
    console.print("\n[cyan]Scanning downloaded samples...[/cyan]")
    scanner = SampleScanner()
    new_samples = scanner.scan_folder(downloader.output_dir)
    console.print(f"[green]Indexed {len(new_samples)} new samples![/green]")

    # Update config
    cfg = Config.load()
    cfg.add_sample_folder(str(downloader.output_dir))
    cfg.save()

    console.print("\n[bold green]Ready to go! Run 'beat-sensei' to start.[/bold green]\n")


def show_help():
    """Show help information."""
    help_table = Table(title="Beat-Sensei Commands", box=box.ROUNDED)
    help_table.add_column("Command", style="cyan")
    help_table.add_column("Description", style="white")

    commands = [
        ("search <query>", "Search for samples by description"),
        ("play <number>", "Play sample from search results"),
        ("play <filepath>", "Play a specific file"),
        ("stop", "Stop current playback"),
        ("generate <desc>", "Generate a new sample (Pro)"),
        ("random", "Get random samples for inspiration"),
        ("help", "Show this help"),
        ("quit", "Exit Beat-Sensei"),
    ]

    for cmd, desc in commands:
        help_table.add_row(cmd, desc)

    console.print(help_table)


def run():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()
