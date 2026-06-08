#!/usr/bin/env python3
"""Aseprite command wrappers for professional sprite production."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def aseprite_binary() -> str:
    configured = os.environ.get("ASEPRITE_BIN")
    candidates = [
        configured,
        shutil.which("aseprite"),
        "/home/bkg/.local/bin/aseprite",
        "/usr/bin/aseprite",
        "/usr/local/bin/aseprite",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise SystemExit("Aseprite binary not found. Set ASEPRITE_BIN or install aseprite.")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def detect(_args: argparse.Namespace) -> None:
    binary = aseprite_binary()
    version = run([binary, "--version"]).stdout.strip()
    print(json.dumps({"binary": binary, "version": version}, indent=2))


def export_sheet(args: argparse.Namespace) -> None:
    binary = aseprite_binary()
    inputs = [str(Path(item).resolve()) for item in args.inputs]
    for item in inputs:
        if not Path(item).exists():
            raise SystemExit(f"input does not exist: {item}")

    sheet = Path(args.sheet).resolve()
    data = Path(args.data).resolve()
    sheet.parent.mkdir(parents=True, exist_ok=True)
    data.parent.mkdir(parents=True, exist_ok=True)

    command = [
        binary,
        "--batch",
        *inputs,
        "--data",
        str(data),
        "--format",
        "json-array",
        "--sheet",
        str(sheet),
        "--sheet-type",
        args.sheet_type,
        "--border-padding",
        str(args.border_padding),
        "--shape-padding",
        str(args.shape_padding),
        "--inner-padding",
        str(args.inner_padding),
    ]
    if args.columns:
        command.extend(["--sheet-columns", str(args.columns)])
    if args.rows:
        command.extend(["--sheet-rows", str(args.rows)])
    if args.scale != 1:
        command.extend(["--scale", str(args.scale)])
    if args.trim:
        command.append("--trim")
    if args.merge_duplicates:
        command.append("--merge-duplicates")
    if args.filename_format:
        command.extend(["--filename-format", args.filename_format])

    result = run(command)
    print(
        json.dumps(
            {
                "sheet": str(sheet),
                "data": str(data),
                "inputs": inputs,
                "aseprite": binary,
                "stdout": result.stdout.strip(),
            },
            indent=2,
        )
    )


def convert(args: argparse.Namespace) -> None:
    binary = aseprite_binary()
    source = Path(args.input).resolve()
    target = Path(args.output).resolve()
    if not source.exists():
        raise SystemExit(f"input does not exist: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)

    command = [
        binary,
        "--batch",
        str(source),
        "--color-mode",
        args.color_mode,
        "--dithering-algorithm",
        args.dithering_algorithm,
    ]
    if args.palette:
        command.extend(["--palette", str(Path(args.palette).resolve())])
    if args.scale != 1:
        command.extend(["--scale", str(args.scale)])
    command.extend(["--save-as", str(target)])

    result = run(command)
    print(
        json.dumps(
            {
                "input": str(source),
                "output": str(target),
                "color_mode": args.color_mode,
                "aseprite": binary,
                "stdout": result.stdout.strip(),
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    detect_parser = subcommands.add_parser("detect")
    detect_parser.set_defaults(func=detect)

    sheet_parser = subcommands.add_parser("export-sheet")
    sheet_parser.add_argument("inputs", nargs="+")
    sheet_parser.add_argument("--sheet", required=True)
    sheet_parser.add_argument("--data", required=True)
    sheet_parser.add_argument(
        "--sheet-type",
        choices=["horizontal", "vertical", "rows", "columns", "packed"],
        default="horizontal",
    )
    sheet_parser.add_argument("--columns", type=int)
    sheet_parser.add_argument("--rows", type=int)
    sheet_parser.add_argument("--scale", type=int, default=1)
    sheet_parser.add_argument("--border-padding", type=int, default=0)
    sheet_parser.add_argument("--shape-padding", type=int, default=0)
    sheet_parser.add_argument("--inner-padding", type=int, default=0)
    sheet_parser.add_argument("--trim", action="store_true")
    sheet_parser.add_argument("--merge-duplicates", action="store_true")
    sheet_parser.add_argument("--filename-format")
    sheet_parser.set_defaults(func=export_sheet)

    convert_parser = subcommands.add_parser("convert")
    convert_parser.add_argument("input")
    convert_parser.add_argument("output")
    convert_parser.add_argument(
        "--color-mode", choices=["rgb", "grayscale", "indexed"], default="rgb"
    )
    convert_parser.add_argument(
        "--dithering-algorithm", choices=["none", "ordered", "old"], default="none"
    )
    convert_parser.add_argument("--palette")
    convert_parser.add_argument("--scale", type=int, default=1)
    convert_parser.set_defaults(func=convert)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
