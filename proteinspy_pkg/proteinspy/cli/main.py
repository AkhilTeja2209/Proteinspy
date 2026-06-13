"""
Proteinspy CLI — analyse protein structure files from the terminal.

Supported input formats
-----------------------
.cif / .mmcif / .pdbx     mmCIF (preferred)
.pdb / .ent               legacy PDB format
*.gz                      compressed variants of the above

Output formats (--output / -o)
-------------------------------
table   Rich terminal table (default)
json    Machine-readable JSON
csv     Comma-separated values
tsv     Tab-separated values
"""

from __future__ import annotations

import sys

import click
from rich import box
from rich.console import Console
from rich.table import Table

from proteinspy.analysis.advanced import (
    get_bfactor_stats,
    get_chain_interface,
    get_disulfide_bonds,
)
from proteinspy.analysis.basic import (
    get_chains,
    get_ligands,
    get_missing_residues,
    get_resolution,
)
from proteinspy.core.validator import validate_structure
from proteinspy.exceptions import ProteinsyError
from proteinspy.io.writers import write_output

console = Console()

_OUTPUT_OPTION = click.option(
    "--output",
    "-o",
    "output_fmt",
    type=click.Choice(["table", "json", "csv", "tsv"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)


def _err(msg: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {msg}")
    sys.exit(1)


def _maybe_print(data: dict, fmt: str, display_fn) -> None:
    if fmt == "table":
        display_fn()
    else:
        click.echo(write_output(data, fmt))


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
    console.print(
        f"[bold cyan]Missing Residues[/bold cyan]  ({r['missing_count']} found)\n"
    )
    if r["missing_count"] == 0:
        console.print("  [green]No missing residues.[/green]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain", justify="center")
    t.add_column("Residue", justify="center")
    t.add_column("Seq #", justify="right")
    for mr in r["missing_residues"]:
        t.add_row(
            mr.get("chain", "?"), mr.get("residue", "?"), str(mr.get("seq_num", "?"))
        )
    console.print(t)
    console.print()


def show_bfactor(path: str) -> None:
    r = get_bfactor_stats(path)
    ov = r["overall"]
    console.print("\n[bold cyan]B-Factor Statistics[/bold cyan]\n")
    console.print(
        f"  Overall  — min: [bold]{ov['min']}[/bold]  max: [bold]{ov['max']}[/bold]  "
        f"mean: [bold]{ov['mean']}[/bold]  std: [bold]{ov['std']}[/bold]  atoms: {ov['atom_count']}\n"
    )
    if r["by_chain"]:
        t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
        t.add_column("Chain", justify="center")
        t.add_column("Min", justify="right")
        t.add_column("Max", justify="right")
        t.add_column("Mean", justify="right")
        t.add_column("Std", justify="right")
        t.add_column("Atoms", justify="right")
        for ch in r["by_chain"]:
            t.add_row(
                ch["chain_id"],
                str(ch["min"]),
                str(ch["max"]),
                str(ch["mean"]),
                str(ch["std"]),
                str(ch["atom_count"]),
            )
        console.print(t)
    console.print()


def show_disulfide(path: str) -> None:
    r = get_disulfide_bonds(path)
    console.print(
        f"\n[bold cyan]Disulfide Bonds[/bold cyan]  ({r['bond_count']} found)\n"
    )
    if r["bond_count"] == 0:
        console.print("  [yellow]No disulfide bonds detected.[/yellow]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain A", justify="center")
    t.add_column("Res A", justify="center")
    t.add_column("Seq A", justify="right")
    t.add_column("Chain B", justify="center")
    t.add_column("Res B", justify="center")
    t.add_column("Seq B", justify="right")
    t.add_column("Distance (Å)", justify="right")
    for b in r["bonds"]:
        t.add_row(
            b["chain_a"],
            b["res_a"],
            b["seqid_a"],
            b["chain_b"],
            b["res_b"],
            b["seqid_b"],
            str(b["distance_A"]),
        )
    console.print(t)
    console.print()


def show_interface(path: str) -> None:
    r = get_chain_interface(path)
    console.print(
        f"\n[bold cyan]Chain Interfaces[/bold cyan]  ({r['interface_count']} found)\n"
    )
    if r["interface_count"] == 0:
        console.print("  [yellow]No inter-chain interfaces detected.[/yellow]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain A", justify="center")
    t.add_column("Chain B", justify="center")
    t.add_column("Contact Pairs", justify="right")
    t.add_column("Residues A")
    t.add_column("Residues B")
    for iface in r["interfaces"]:
        ra = ", ".join(iface["residues_a"][:8])
        if len(iface["residues_a"]) > 8:
            ra += f" … (+{len(iface['residues_a']) - 8})"
        rb = ", ".join(iface["residues_b"][:8])
        if len(iface["residues_b"]) > 8:
            rb += f" … (+{len(iface['residues_b']) - 8})"
        t.add_row(
            iface["chain_a"], iface["chain_b"], str(iface["contact_pairs"]), ra, rb
        )
    console.print(t)
    console.print()


def show_validate(path: str) -> None:
    r = validate_structure(path)
    status = (
        "[bold green]PASS[/bold green]" if r["pass"] else "[bold red]FAIL[/bold red]"
    )
    console.print(f"\n[bold cyan]Structure Validation[/bold cyan]  {status}\n")
    if r["info"]:
        console.print("[bold]Info:[/bold]")
        for note in r["info"]:
            console.print(f"  [dim]•[/dim] {note}")
        console.print()
    if r["warnings"]:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warn in r["warnings"]:
            console.print(f"  [yellow]⚠[/yellow]  {warn}")
        console.print()
    else:
        console.print("  [green]No quality warnings.[/green]\n")


def print_help() -> None:
    console.print()
    console.print("[bold green]Proteinspy CLI[/bold green]", justify="center")
    console.print()
    t = Table(
        box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", expand=True
    )
    t.add_column("Command", style="bold yellow", min_width=22)
    t.add_column("Description")
    rows = [
        ("--help", "Show this help message and exit"),
        ("--version", "Show the package version and exit"),
        (
            "analyze",
            "Run all basic analyses (resolution, chains, ligands, missing residues)",
        ),
        ("resolution", "Crystallographic resolution and experimental method"),
        ("chains", "Polymer chains with type and residue count"),
        ("ligands", "Non-solvent ligand molecules"),
        ("missing", "Residues present in sequence but absent from ATOM records"),
        ("bfactor", "B-factor statistics — global and per-chain"),
        ("disulfide", "Disulfide bonds detected by SG-SG distance (<= 2.5 Å)"),
        ("interface", "Inter-chain interface residues by Ca distance"),
        ("validate", "Quick quality check — resolution, completeness, model count"),
        ("export", "Export any analysis result to a JSON / CSV / TSV file"),
    ]
    for cmd, desc in rows:
        t.add_row(cmd, desc)
    console.print(t)
    console.print()
    console.print(
        "Usage: [bold]proteinspy [cyan]<command>[/cyan] "
        "<file.cif|file.pdb> [[dim]--output table|json|csv|tsv[/dim]][/bold]"
    )
    console.print("Example: [bold]proteinspy analyze 10AJ.cif[/bold]")
    console.print("Example: [bold]proteinspy bfactor protein.pdb --output json[/bold]")
    console.print()


CONTEXT_SETTINGS = dict(help_option_names=["--help", "-h"])


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option(version="1.1.4", prog_name="proteinspy")
@click.pass_context
def main(ctx: click.Context) -> None:
    """proteinspy — Analyse a protein structure file (.cif or .pdb)."""
    if ctx.invoked_subcommand is None:
        print_help()


@main.command("analyze")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_analyze(structure_file: str, output_fmt: str) -> None:
    """Run all basic analyses on a structure file."""
    try:
        if output_fmt != "table":
            combined = {
                "resolution": get_resolution(structure_file),
                "chains": get_chains(structure_file),
                "ligands": get_ligands(structure_file),
                "missing_residues": get_missing_residues(structure_file),
            }
            click.echo(write_output(combined, output_fmt))
        else:
            console.rule(f"[bold blue]proteinspy — {structure_file}[/bold blue]")
            show_resolution(structure_file)
            show_chains(structure_file)
            show_ligands(structure_file)
            show_missing(structure_file)
            console.rule()
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("resolution")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_resolution(structure_file: str, output_fmt: str) -> None:
    """Report crystallographic resolution only."""
    try:
        data = get_resolution(structure_file)
        _maybe_print(data, output_fmt, lambda: show_resolution(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("chains")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_chains(structure_file: str, output_fmt: str) -> None:
    """Report all polymer chains."""
    try:
        data = get_chains(structure_file)
        _maybe_print(data, output_fmt, lambda: show_chains(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("ligands")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_ligands(structure_file: str, output_fmt: str) -> None:
    """Report all non-solvent ligands."""
    try:
        data = get_ligands(structure_file)
        _maybe_print(data, output_fmt, lambda: show_ligands(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("missing")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_missing(structure_file: str, output_fmt: str) -> None:
    """Report all missing residues."""
    try:
        data = get_missing_residues(structure_file)
        _maybe_print(data, output_fmt, lambda: show_missing(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("bfactor")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_bfactor(structure_file: str, output_fmt: str) -> None:
    """B-factor statistics — global and per-chain."""
    try:
        data = get_bfactor_stats(structure_file)
        _maybe_print(data, output_fmt, lambda: show_bfactor(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("disulfide")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_disulfide(structure_file: str, output_fmt: str) -> None:
    """Detect disulfide bonds by SG-SG distance."""
    try:
        data = get_disulfide_bonds(structure_file)
        _maybe_print(data, output_fmt, lambda: show_disulfide(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("interface")
@click.argument("structure_file")
@click.option(
    "--cutoff",
    default=5.0,
    show_default=True,
    type=float,
    help="Ca-Ca distance threshold in Angstroms.",
)
@_OUTPUT_OPTION
def cmd_interface(structure_file: str, cutoff: float, output_fmt: str) -> None:
    """Report inter-chain interface residues."""
    try:
        data = get_chain_interface(structure_file, cutoff=cutoff)
        _maybe_print(data, output_fmt, lambda: show_interface(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("validate")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_validate(structure_file: str, output_fmt: str) -> None:
    """Quick quality check (resolution, completeness, model count)."""
    try:
        data = validate_structure(structure_file)
        _maybe_print(data, output_fmt, lambda: show_validate(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("export")
@click.argument("structure_file")
@click.argument("output_file")
@click.option(
    "--analysis",
    "-a",
    type=click.Choice(
        [
            "resolution",
            "chains",
            "ligands",
            "missing",
            "bfactor",
            "disulfide",
            "interface",
            "validate",
            "all",
        ],
        case_sensitive=False,
    ),
    default="all",
    show_default=True,
    help="Which analysis to export.",
)
def cmd_export(structure_file: str, output_file: str, analysis: str) -> None:
    """
    Export analysis results to a file.

    Output format is inferred from the OUTPUT_FILE extension
    (.json -> JSON, .csv -> CSV, .tsv -> TSV).

    \b
    Examples:
      proteinspy export protein.cif report.json
      proteinspy export protein.cif chains.csv --analysis chains
    """
    import os as _os

    ext = _os.path.splitext(output_file.lower())[1].lstrip(".")
    fmt = {"json": "json", "csv": "csv", "tsv": "tsv"}.get(ext, "json")

    _analysis_map = {
        "resolution": get_resolution,
        "chains": get_chains,
        "ligands": get_ligands,
        "missing": get_missing_residues,
        "bfactor": get_bfactor_stats,
        "disulfide": get_disulfide_bonds,
        "interface": get_chain_interface,
        "validate": validate_structure,
    }

    try:
        if analysis == "all":
            data = {k: fn(structure_file) for k, fn in _analysis_map.items()}
        else:
            data = _analysis_map[analysis](structure_file)
        write_output(data, fmt, output_path=output_file)
        console.print(
            f"[green]✓[/green] Exported [bold]{analysis}[/bold] "
            f"analysis to [bold]{output_file}[/bold] ({fmt.upper()})"
        )
    except ProteinsyError as exc:
        _err(str(exc))
