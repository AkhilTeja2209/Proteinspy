"""
Output formatters for analysis results.

Supported formats: json, csv, tsv.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
from typing import Any, Dict, Literal, Optional

from proteinspy.exceptions import ExportError

logger = logging.getLogger(__name__)

OutputFormat = Literal["json", "csv", "tsv"]


def to_json(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Serialise analysis results to a JSON string.

    Args:
        data: Dictionary returned by any analysis function.
        indent: Pretty-print indentation level (default 2).

    Returns:
        UTF-8 JSON string.
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ExportError(f"JSON serialisation failed: {exc}") from exc


def to_csv(data: Dict[str, Any], delimiter: str = ",") -> str:
    """
    Serialise analysis results to a flat CSV/TSV string.

    List-valued keys are expanded so that each list element becomes one row.
    Scalar keys are repeated on every row.

    Args:
        data: Dictionary returned by any analysis function.
        delimiter: Field separator — "," for CSV, "\\t" for TSV.

    Returns:
        String containing header + data rows.
    """
    try:
        buf = io.StringIO()
        scalars: Dict[str, Any] = {}
        list_val: list = []

        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                list_val = v
            elif not isinstance(v, (list, dict)):
                scalars[k] = v

        if list_val:
            fieldnames = list(scalars.keys()) + list(list_val[0].keys())
            writer = csv.DictWriter(
                buf, fieldnames=fieldnames, delimiter=delimiter, extrasaction="ignore"
            )
            writer.writeheader()
            for row in list_val:
                writer.writerow({**scalars, **row})
        else:
            writer = csv.DictWriter(buf, fieldnames=list(scalars.keys()), delimiter=delimiter)
            writer.writeheader()
            writer.writerow(scalars)

        return buf.getvalue()

    except Exception as exc:
        raise ExportError(f"CSV serialisation failed: {exc}") from exc


def write_output(
    data: Dict[str, Any],
    fmt: OutputFormat,
    output_path: Optional[str] = None,
) -> str:
    """
    Format data and optionally write it to a file.

    Args:
        data: Analysis result dictionary.
        fmt: One of "json", "csv", or "tsv".
        output_path: If given, the formatted string is written to this path.

    Returns:
        Formatted string.

    Raises:
        ExportError: If formatting or file writing fails.
        ValueError: If fmt is not a supported format.
    """
    if fmt == "json":
        content = to_json(data)
    elif fmt == "csv":
        content = to_csv(data, delimiter=",")
    elif fmt == "tsv":
        content = to_csv(data, delimiter="\t")
    else:
        raise ValueError(f"Unsupported output format: '{fmt}'. Choose from json, csv, tsv.")

    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            logger.info("Output written to %s", output_path)
        except OSError as exc:
            raise ExportError(f"Cannot write to '{output_path}': {exc}") from exc

    return content
