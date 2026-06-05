import click
from rich.console import Console
from rich.table import Table
from rich import box

from .analysis import get_resolution, get_chains, get_ligands, get_missing_residues

console = Console()


# ── display helpers ──

def show_resolution(path: str) -> None:
    r = get_resolution(path)
    console.print("\n[bold cyan]Resolution[/bold cyan]")
    if r["resolution"]:
        console.print(f"  Resolution : [bold]{r['resolution']} {r['unit']}[/bold]")
    else:
        console.print("  Resolution : [yellow]Not available[/yellow]")
    console.print(f"  Method     : {r['method']}\n")

def show_chains(path: str) -> None:
    r = get_chains(path)
    console.print(f"[bold cyan]Chains[/bold cyan]  ({r['chain_count']} total)\n")
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain ID", justify="center")
    t.add_column("Type")
    t.add_column("Residues", justify="right")
    for ch in r["chains"]:
        t.add_row(ch["id"], ch["type"], str(ch["residue_count"]))
    console.print(t)
    console.print()

def show_ligands(path: str) -> None:
    r = get_ligands(path)
    console.print(f"[bold cyan]Ligands[/bold cyan]  ({r['ligand_count']} found)\n")
    if not r["has_ligand"]:
        console.print("  [yellow]No ligands detected.[/yellow]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Ligand ID", justify="center")
    t.add_column("Chain", justify="center")
    t.add_column("Seq Num", justify="right")
    for lg in r["ligands"]:
        t.add_row(lg["id"], lg.get("chain", "?"), lg.get("seq_num", "?"))
    console.print(t)
    console.print()

def show_missing(path: str) -> None:
    r = get_missing_residues(path)
    console.print(f"[bold cyan]Missing Residues[/bold cyan]  ({r['missing_count']} found)\n")
    if r["missing_count"] == 0:
        console.print("  [green]No missing residues.[/green]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain", justify="center")
    t.add_column("Residue", justify="center")
    t.add_column("Seq #", justify="right")
    for mr in r["missing_residues"]:
        t.add_row(
            mr.get("chain", "?"),
            mr.get("residue", "?"),
            str(mr.get("seq_num", "?")),
        )
    console.print(t)
    console.print()


#CLI commands

@click.group()
def main():
    """proteinspy — Analyse a .cif protein structure file."""

@main.command("analyze")
@click.argument("cif_file")
def cmd_analyze(cif_file: str):
    """Run all analyses on a .cif file (mode-based)."""
    console.rule(f"[bold blue]proteinspy — {cif_file}[/bold blue]")
    show_resolution(cif_file)
    show_chains(cif_file)
    show_ligands(cif_file)
    show_missing(cif_file)
    console.rule()

@main.command("resolution")
@click.argument("cif_file")
def cmd_resolution(cif_file: str):
    """Report resolution only."""
    show_resolution(cif_file)

@main.command("chains")
@click.argument("cif_file")
def cmd_chains(cif_file: str):
    """Report chains only."""
    show_chains(cif_file)

@main.command("ligands")
@click.argument("cif_file")
def cmd_ligands(cif_file: str):
    """Report ligands only."""
    show_ligands(cif_file)

@main.command("missing")
@click.argument("cif_file")
def cmd_missing(cif_file: str):
    """Report missing residues only."""
    show_missing(cif_file)
