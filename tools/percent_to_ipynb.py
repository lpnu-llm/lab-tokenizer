"""Convert a Python percent-format notebook to a Jupyter notebook.

Uses only the Python standard library so `make notebook` works without
installing Jupytext or nbformat.
"""

import argparse
import json
from pathlib import Path


CELL_MARKER = "# %%"


def markdown_source(lines):
    """Remove the leading comment marker from a markdown cell."""
    source = []
    for line in lines:
        if line.startswith("# "):
            source.append(line[2:])
        elif line.startswith("#"):
            source.append(line[1:])
        else:
            source.append(line)
    return source


def split_cells(text):
    """Parse `# %%` cell markers and return notebook cell dictionaries."""
    cells = []
    cell_type = None
    lines = []

    def append_cell():
        if cell_type is None:
            return
        source = markdown_source(lines) if cell_type == "markdown" else lines[:]
        cell = {
            "cell_type": cell_type,
            "metadata": {},
            "source": source,
        }
        if cell_type == "code":
            cell.update({"execution_count": None, "outputs": []})
        cells.append(cell)

    for line in text.splitlines(keepends=True):
        if line.startswith(CELL_MARKER):
            append_cell()
            cell_type = "markdown" if "[markdown]" in line else "code"
            lines = []
        elif cell_type is not None:
            lines.append(line)

    append_cell()
    return cells


def convert(source_path, output_path):
    source = source_path.read_text(encoding="utf-8")
    notebook = {
        "cells": split_cells(source),
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    output_path.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    convert(args.source, args.output)


if __name__ == "__main__":
    main()
