#!/usr/bin/env python3
"""APAM stdio MCP server.

APAM means Aseprite + Pixel + MCP.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "assets" / "pixel-master-style.txt"
NORMALIZER = ROOT / "scripts" / "normalize_sprite.py"
ASEPRITE_COMMANDS = ROOT / "scripts" / "aseprite_commands.py"
ASEPRITE_SETUP = ROOT / "scripts" / "setup_aseprite_linux.py"


TOOLS = [
    {
        "name": "apam_pixel_master_style",
        "description": "Return the reusable 2.5D pixel-art master style block.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "apam_pixel_asset_patterns",
        "description": "Return reusable pixel asset naming patterns and lifecycle sprite examples.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "apam_pixel_normalize_sprite",
        "description": "Normalize a generated PNG into a 64x64 black-background sprite.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "target": {"type": "string"},
                "kind": {
                    "type": "string",
                    "enum": ["agent", "infant", "sphere", "tile"],
                    "default": "agent",
                },
            },
            "required": ["source", "target"],
            "additionalProperties": False,
        },
    },
    {
        "name": "apam_aseprite_detect",
        "description": "Detect the local Aseprite binary and return its version.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "apam_aseprite_setup_detect",
        "description": "Detect APAM Aseprite install paths and current Aseprite status.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "apam_aseprite_setup_plan",
        "description": "Plan the Linux Aseprite compile/install steps without changing the system.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "apam_aseprite_setup_install",
        "description": "Run the APAM Linux Aseprite compile/install command. Requires yes=true.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "yes": {"type": "boolean"},
                "dry_run": {"type": "boolean", "default": True},
                "force": {"type": "boolean", "default": False},
                "work_dir": {"type": "string"},
                "source_url": {"type": "string"},
            },
            "required": ["yes"],
            "additionalProperties": False,
        },
    },
    {
        "name": "apam_aseprite_export_sheet",
        "description": "Export individual PNG frames into a professional Aseprite sprite sheet plus JSON metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "inputs": {"type": "array", "items": {"type": "string"}},
                "sheet": {"type": "string"},
                "data": {"type": "string"},
                "sheet_type": {
                    "type": "string",
                    "enum": ["horizontal", "vertical", "rows", "columns", "packed"],
                    "default": "horizontal",
                },
                "columns": {"type": "integer"},
                "rows": {"type": "integer"},
                "scale": {"type": "integer", "default": 1},
                "trim": {"type": "boolean", "default": False},
            },
            "required": ["inputs", "sheet", "data"],
            "additionalProperties": False,
        },
    },
    {
        "name": "apam_aseprite_convert",
        "description": "Use Aseprite batch mode to convert a sprite to another file/color mode/palette.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "output": {"type": "string"},
                "color_mode": {
                    "type": "string",
                    "enum": ["rgb", "grayscale", "indexed"],
                    "default": "rgb",
                },
                "palette": {"type": "string"},
                "dithering_algorithm": {
                    "type": "string",
                    "enum": ["none", "ordered", "old"],
                    "default": "none",
                },
            },
            "required": ["input", "output"],
            "additionalProperties": False,
        },
    },
]


def respond(message_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": message_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    print(json.dumps(payload), flush=True)


def text_result(text: str):
    return {"content": [{"type": "text", "text": text}]}


def call_tool(name: str, arguments: dict):
    if name == "apam_pixel_master_style":
        return text_result(STYLE_PATH.read_text())

    if name == "apam_pixel_asset_patterns":
        patterns = [
            "General: <asset_family>_<action_or_state>_<direction?>_frame<0..n>.png",
            "Tiles: tile_<environment>_<variant>_frame<0..n>.png",
            "Props: prop_<object>_<direction?>_<variant?>.png",
            "UI: ui_<component>_<state>_<size>.png",
            "agent_infant_crawling_frame0.png ... agent_infant_crawling_frame3.png",
            "agent_child_running_<se|sw|ne|nw>_frame<0|1|2|3>.png",
            "agent_student_tablet_<se|sw|ne|nw>_frame<0|1|2|3>.png",
            "agent_junior_dev_typing_<se|sw|ne|nw>_frame<0|1|2|3>.png",
            "agent_senior_arch_focus_<se|sw|ne|nw>_frame<0|1|2|3>.png",
            "agent_mentor_lecturing_<se|sw|ne|nw>_frame<0|1|2|3>.png",
            "agent_retired_walking_<se|sw|ne|nw>_frame<0|1|2|3>.png",
            "agent_archived_sphere_frame0.png ... agent_archived_sphere_frame3.png",
        ]
        return text_result("\n".join(patterns))

    if name == "apam_pixel_normalize_sprite":
        source = arguments["source"]
        target = arguments["target"]
        kind = arguments.get("kind", "agent")
        subprocess.run(
            ["python3", str(NORMALIZER), source, target, "--kind", kind],
            check=True,
        )
        return text_result(f"normalized {source} -> {target} as {kind}")

    if name == "apam_aseprite_detect":
        result = subprocess.run(
            ["python3", str(ASEPRITE_COMMANDS), "detect"],
            check=True,
            capture_output=True,
            text=True,
        )
        return text_result(result.stdout.strip())

    if name == "apam_aseprite_setup_detect":
        result = subprocess.run(
            ["python3", str(ASEPRITE_SETUP), "detect"],
            check=True,
            capture_output=True,
            text=True,
        )
        return text_result(result.stdout.strip())

    if name == "apam_aseprite_setup_plan":
        result = subprocess.run(
            ["python3", str(ASEPRITE_SETUP), "plan"],
            check=True,
            capture_output=True,
            text=True,
        )
        return text_result(result.stdout.strip())

    if name == "apam_aseprite_setup_install":
        if arguments.get("yes") is not True:
            raise ValueError("apam_aseprite_setup_install requires yes=true")
        command = ["python3", str(ASEPRITE_SETUP), "install", "--yes"]
        if arguments.get("dry_run", True):
            command.append("--dry-run")
        if arguments.get("force"):
            command.append("--force")
        if arguments.get("work_dir"):
            command.extend(["--work-dir", arguments["work_dir"]])
        if arguments.get("source_url"):
            command.extend(["--source-url", arguments["source_url"]])
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return text_result(result.stdout.strip())

    if name == "apam_aseprite_export_sheet":
        command = [
            "python3",
            str(ASEPRITE_COMMANDS),
            "export-sheet",
            "--sheet",
            arguments["sheet"],
            "--data",
            arguments["data"],
            "--sheet-type",
            arguments.get("sheet_type", "horizontal"),
            "--scale",
            str(arguments.get("scale", 1)),
        ]
        if arguments.get("columns") is not None:
            command.extend(["--columns", str(arguments["columns"])])
        if arguments.get("rows") is not None:
            command.extend(["--rows", str(arguments["rows"])])
        if arguments.get("trim"):
            command.append("--trim")
        command.extend(arguments["inputs"])
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return text_result(result.stdout.strip())

    if name == "apam_aseprite_convert":
        command = [
            "python3",
            str(ASEPRITE_COMMANDS),
            "convert",
            arguments["input"],
            arguments["output"],
            "--color-mode",
            arguments.get("color_mode", "rgb"),
            "--dithering-algorithm",
            arguments.get("dithering_algorithm", "none"),
        ]
        if arguments.get("palette"):
            command.extend(["--palette", arguments["palette"]])
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return text_result(result.stdout.strip())

    raise ValueError(f"unknown tool: {name}")


def handle(message: dict):
    method = message.get("method")
    message_id = message.get("id")

    if method == "initialize":
        return respond(
            message_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "apam-plugin",
                    "version": "0.1.0",
                },
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return respond(message_id, {"tools": TOOLS})

    if method == "tools/call":
        params = message.get("params", {})
        try:
            result = call_tool(params.get("name"), params.get("arguments") or {})
            return respond(message_id, result)
        except Exception as exc:
            return respond(message_id, error={"code": -32000, "message": str(exc)})

    return respond(message_id, error={"code": -32601, "message": f"unknown method {method}"})


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            handle(json.loads(line))
        except Exception as exc:
            respond(None, error={"code": -32700, "message": str(exc)})


if __name__ == "__main__":
    main()
