#!/usr/bin/env python3
"""Beat-Sensei CLI - Your AI Music Production Mentor."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.style import Style
from rich import box

from .chatbot.sensei import BeatSensei
from .auth.tiers import TierManager
from .utils.config import Config

app = typer.Typer(
    name="beat-sensei",
    help="Your AI Music Production Mentor",
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
[dim]Your AI Music Production Mentor[/dim]
"""


@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    """Run interactive chat if no command is provided."""
    if ctx.invoked_subcommand is None:
        run_chat()


def create_sensei(config: Config) -> BeatSensei:
    """Create and initialize Beat-Sensei."""
    tier_manager = TierManager()

    return BeatSensei(
        tier_manager=tier_manager,
        api_key=config.soundraw_api_token,
        deepseek_api_key=config.deepseek_api_key,
        supabase_url=config.supabase_url,
        supabase_anon_key=config.supabase_anon_key,
    )


def run_chat():
    """Run the interactive Beat-Sensei chat."""
    config = Config.load()
    sensei = create_sensei(config)
    stats = sensei.get_stats()

    # Display header
    console.print(get_banner())
    console.print(Panel(
        f"[bold]Tier:[/bold] {sensei.tier_manager.get_tier_display()}\n"
        f"[bold]Generation:[/bold] {'Ready' if sensei.generator.is_available() else '[yellow]Set SOUNDRAW_API_TOKEN to enable[/yellow]'}",
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
                console.print("\n[cyan]Sensei:[/cyan] Keep creating! See you next time.")
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
                if action_data.get('type') == 'generated':
                    console.print(f"\n[green]Saved to:[/green] {action_data['file']}")
                    if action_data.get('mood') or action_data.get('genre'):
                        console.print(f"[dim]Style: {action_data.get('mood', '')} {action_data.get('genre', '')}[/dim]")

            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[cyan]Sensei:[/cyan] Catch you later! Keep creating.")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def chat():
    """Start interactive Beat-Sensei chat."""
    run_chat()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Description of the track to generate"),
    duration: int = typer.Option(30, "--duration", "-d", help="Duration in seconds (free: 30s, pro: 300s)"),
):
    """Generate a new track using AI or local beat generator (5 free per day!)."""
    config = Config.load()
    tier_manager = TierManager()
    
    # Try Soundraw first, fall back to local generator
    if config.soundraw_api_token:
        from .generator.soundraw_client import SoundrawGenerator
        generator = SoundrawGenerator(api_token=config.soundraw_api_token)
        generator_type = "AI"
    else:
        # Fall back to local beat generator
        from .generator.local_generator import LocalBeatGenerator, SimpleBeatGenerator
        try:
            generator = LocalBeatGenerator()
            if not generator.is_available():
                generator = SimpleBeatGenerator()
            generator_type = "local"
        except ImportError:
            generator = SimpleBeatGenerator()
            generator_type = "simple"
        
        console.print("[yellow]Note: Using local beat generator (Soundraw API not configured)[/yellow]")
        console.print("[dim]For AI generation, set: export SOUNDRAW_API_TOKEN=your_key[/dim]")
        console.print("")

    if not tier_manager.can_generate():
        console.print("[yellow]You've used all your generations for today![/yellow]")
        console.print("[dim]Come back tomorrow for 5 more, or upgrade to Pro for 50/day.[/dim]")
        raise typer.Exit(0)

    # Limit duration based on tier
    max_duration = tier_manager.get_max_duration()
    if duration > max_duration:
        console.print(f"[yellow]Duration limited to {max_duration}s on free tier.[/yellow]")
        duration = max_duration

    remaining = tier_manager.get_remaining_generations()
    console.print(f"\n[cyan]Creating:[/cyan] {prompt}")
    if generator_type == "AI":
        console.print(f"[dim](AI generation, {remaining} remaining today)[/dim]\n")
    else:
        console.print(f"[dim](Local generation, {remaining} remaining today)[/dim]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating your track...", total=None)
        result = generator.generate(prompt, duration=float(duration))
        progress.update(task, completed=True)

    if result.success:
        tier_manager.use_generation()
        
        if generator_type == "AI":
            console.print(f"\n[green]✓ AI track generated![/green] Saved to: {result.filepath}")
        elif generator_type == "local":
            console.print(f"\n[green]✓ Local beat created![/green] Saved to: {result.filepath}")
        else:
            console.print(f"\n[green]✓ Beat idea created![/green] Saved to: {result.filepath}")
            
        if result.mood or result.genre:
            console.print(f"[dim]Style: {result.mood} - {result.genre}[/dim]")

        remaining_after = tier_manager.get_remaining_generations()
        console.print(f"\n[dim]({remaining_after} generations left today)[/dim]")
        
        # Show helpful next steps
        if generator_type != "AI":
            console.print(f"\n[bold]Next steps:[/bold]")
            console.print(f"1. Load this in your DAW")
            console.print(f"2. Add your own sounds and samples")
            console.print(f"3. For AI generation: export SOUNDRAW_API_TOKEN=your_key")
    else:
        console.print(f"\n[red]Generation failed:[/red] {result.error}")
        if "soundfile" in str(result.error).lower() or "scipy" in str(result.error).lower():
            console.print("\n[dim]Install audio packages: pip install soundfile scipy[/dim]")
        else:
            console.print("\n[dim]Tip: Be specific! Try 'dark trap high energy' or 'chill lo-fi peaceful'[/dim]")


@app.command()
def options():
    """Show available moods, genres, and energy levels for generation."""
    from .generator.soundraw_client import SoundrawGenerator

    console.print("\n[bold cyan]Generation Options[/bold cyan]\n")

    # Moods
    moods = SoundrawGenerator.get_available_moods()
    console.print("[bold]Moods:[/bold]")
    console.print(f"[dim]{', '.join(moods)}[/dim]\n")

    # Genres
    genres = SoundrawGenerator.get_available_genres()
    console.print("[bold]Genres:[/bold]")
    console.print(f"[dim]{', '.join(genres)}[/dim]\n")

    # Energy
    energy = SoundrawGenerator.get_available_energy_levels()
    console.print("[bold]Energy Levels:[/bold]")
    console.print(f"[dim]{', '.join(energy)}[/dim]\n")

    console.print("[bold]Example prompts:[/bold]")
    console.print("  [green]generate dark trap high energy[/green]")
    console.print("  [green]generate chill lo-fi peaceful low energy[/green]")
    console.print("  [green]generate upbeat funk groovy[/green]")


@app.command()
def config():
    """Show configuration and status."""
    cfg = Config.load()
    tier_manager = TierManager()

    console.print(get_banner())

    table = Table(title="Beat-Sensei Status", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Tier", tier_manager.get_tier_display())
    table.add_row("Soundraw API", "[green]Ready[/green]" if cfg.soundraw_api_token else "[yellow]Not configured[/yellow]")
    table.add_row("Supabase Library", "[green]Ready[/green]" if cfg.supabase_url and cfg.supabase_anon_key else "[yellow]Not configured[/yellow]")
    table.add_row("Output Folder", cfg.output_folder)
    table.add_row("Max Duration", f"{tier_manager.get_max_duration()}s")

    console.print(table)

    if not cfg.soundraw_api_token:
        console.print("\n[bold]To enable generation:[/bold]")
        console.print("1. Get your API key at [cyan]soundraw.io[/cyan]")
        console.print("2. Run: [green]export SOUNDRAW_API_TOKEN=your_key[/green]")

    console.print("\n[dim]Free: 5 generations/day, 30s max[/dim]")
    console.print("[dim]Pro: 50 generations/day, 5min max[/dim]")


@app.command()
def auth(license_key: str = typer.Argument(..., help="Your Pro license key")):
    """Activate a Pro license for more generations."""
    tier_manager = TierManager()

    if tier_manager.activate_license(license_key):
        console.print(f"\n[green]License activated![/green]")
        console.print(f"You're now on [bold]{tier_manager.tier.value}[/bold] tier.")
        console.print(f"  - {tier_manager.limits.generations_per_day} generations/day")
        console.print(f"  - {tier_manager.get_max_duration()}s max duration")

        # Save to config
        cfg = Config.load()
        cfg.license_key = license_key
        cfg.tier = tier_manager.tier.value
        cfg.save()
    else:
        console.print("[red]Invalid license key.[/red]")
        console.print("[dim]Pro keys start with BEAT-PRO-[/dim]")


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
    category: str = typer.Option(None, "--category", "-c", help="Filter by category (kick, snare, hat, 808, etc.)"),
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
        console.print("\n[dim]Try a different search, or use 'beat-sensei generate' to create new sounds.[/dim]")
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


@app.command()
def download(
    pack_name: str = typer.Argument(..., help="Pack name to download (use 'all' for all packs, 'list' to see available packs)"),
    output_dir: str = typer.Option(None, "--output", "-o", help="Output directory (default: ~/Music/BeatSensei/Samples)"),
):
    """Download free sample packs."""
    from .samples.downloader import SampleDownloader
    from pathlib import Path
    
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path.home() / "Music" / "BeatSensei" / "Samples"
    
    downloader = SampleDownloader(output_path)
    
    if pack_name.lower() == "list":
        console.print("\n[bold cyan]Available Sample Packs[/bold cyan]\n")
        
        packs = downloader.list_packs()
        for pack in packs:
            console.print(f"[bold]{pack['name']}[/bold]")
            console.print(f"  [dim]{pack['description']}[/dim]")
            console.print(f"  [green]Type: {pack['type']}[/green]")
            console.print(f"  [yellow]Files: {pack['file_count']}[/yellow]")
            console.print()
        
        console.print("[dim]Download with: beat-sensei download <pack_name>[/dim]")
        console.print("[dim]Download all: beat-sensei download all[/dim]")
        return
    
    console.print(f"\n[cyan]Downloading samples to:[/cyan] {output_path}")
    
    if pack_name.lower() == "all":
        console.print("[dim]Downloading all sample packs...[/dim]")
        success, message, files = downloader.download_all_packs(
            progress_callback=lambda msg: console.print(f"[dim]{msg}[/dim]")
        )
    else:
        console.print(f"[dim]Downloading '{pack_name}' pack...[/dim]")
        success, message, files = downloader.download_pack(
            pack_name,
            progress_callback=lambda msg: console.print(f"[dim]{msg}[/dim]")
        )
    
    if success:
        console.print(f"\n[green]✓ {message}[/green]")
        if files:
            console.print(f"\n[dim]Downloaded {len(files)} files:[/dim]")
            for file in files[:5]:  # Show first 5 files
                console.print(f"  [dim]{file.name}[/dim]")
            if len(files) > 5:
                console.print(f"  [dim]... and {len(files) - 5} more[/dim]")
        
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"1. Scan these samples: [green]beat-sensei scan {output_path}[/green]")
        console.print(f"2. Search samples: [green]beat-sensei samples 'kick'[/green]")
        console.print(f"3. Start creating: [green]beat-sensei[/green]")
    else:
        console.print(f"\n[red]✗ {message}[/red]")
        console.print(f"\n[dim]Use 'beat-sensei download list' to see available packs.[/dim]")


@app.command()
def scan(
    directory: str = typer.Argument(..., help="Directory to scan for audio samples"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-R", help="Scan recursively"),
):
    """Scan a directory for audio samples and build local index."""
    from .samples.scanner import SampleScanner
    from pathlib import Path
    
    scan_path = Path(directory)
    
    if not scan_path.exists():
        console.print(f"[red]Directory not found: {scan_path}[/red]")
        raise typer.Exit(1)
    
    if not scan_path.is_dir():
        console.print(f"[red]Not a directory: {scan_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[cyan]Scanning for audio samples in:[/cyan] {scan_path}")
    if recursive:
        console.print("[dim]Recursive scan enabled[/dim]")
    
    scanner = SampleScanner()
    
    with console.status("[cyan]Scanning directory...[/cyan]", spinner="dots"):
        try:
            # For now, just scan the folder (not recursive)
            # TODO: Implement recursive scanning
            samples = scanner.scan_folder(scan_path, analyze_audio=False)
            scanner._save_index()
            new_samples = len(samples)
        except Exception as e:
            console.print(f"[red]Error scanning directory: {e}[/red]")
            raise typer.Exit(1)
    
    console.print(f"\n[green]✓ Scan complete![/green]")
    console.print(f"[dim]Found {new_samples} new samples[/dim]")
    console.print(f"[dim]Total samples in index: {len(scanner.samples)}[/dim]")
    
    # Show some example samples
    if scanner.samples:
        console.print(f"\n[bold]Example samples found:[/bold]")
        sample_list = list(scanner.samples.values())[:5]
        for i, sample in enumerate(sample_list, 1):
            category = f" [{sample.category}]" if sample.category else ""
            console.print(f"  {i}. [cyan]{sample.filename}[/cyan]{category}")
        
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"1. Search samples: [green]beat-sensei samples 'kick'[/green]")
        console.print(f"2. Start chat: [green]beat-sensei[/green]")
        console.print(f"3. Type 'kicks', 'snares', etc. to browse your samples")


def show_help():
    """Show help information."""
    console.print("\n[bold cyan]Beat-Sensei Commands[/bold cyan]\n")

    help_table = Table(box=box.ROUNDED, show_header=False)
    help_table.add_column("Command", style="cyan", width=25)
    help_table.add_column("Description", style="white")

    commands = [
        ("generate <description>", "Create a track with AI (5 free/day)"),
        ("samples <query>", "Search sample library"),
        ("download <pack>", "Download free sample packs"),
        ("scan <directory>", "Scan directory for audio samples"),
        ("kicks / snares / 808s", "Browse by category"),
        ("random", "Get random samples"),
        ("play <number>", "Preview a sample"),
        ("moods / genres / options", "See available styles"),
        ("help", "Show this help"),
        ("quit", "Exit Beat-Sensei"),
    ]

    for cmd, desc in commands:
        help_table.add_row(cmd, desc)

    console.print(help_table)

    console.print("\n[bold]Tips for better results:[/bold]")
    console.print("  - Combine mood + genre + energy")
    console.print("  - Example: [green]'dark trap aggressive high energy'[/green]")
    console.print("  - Example: [green]'chill lo-fi dreamy low energy'[/green]")
    console.print("\n[bold]Sample library:[/bold]")
    console.print("  - Type 'kicks', 'snares', 'hats', '808s' to browse")
    console.print("  - Type 'search dark trap' to find matching samples")
    console.print("  - After generating, I'll suggest related samples")
    console.print()


def run():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()
