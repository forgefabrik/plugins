#!/usr/bin/env python3
"""Tiny stdio MCP server for AWP pixel sprite helpers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "assets" / "apw-master-style.txt"
NORMALIZER = ROOT / "scripts" / "normalize_sprite.py"


TOOLS = [
    {
        "name": "awp_pixel_master_style",
        "description": "Return the reusable AWP/APW 2.5D pixel-art master style block.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "awp_pixel_agent_filenames",
        "description": "Return the expected lifecycle-agent sprite filename patterns.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "awp_pixel_normalize_sprite",
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
    if name == "awp_pixel_master_style":
        return text_result(STYLE_PATH.read_text())

    if name == "awp_pixel_agent_filenames":
        patterns = [
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

    if name == "awp_pixel_normalize_sprite":
        source = arguments["source"]
        target = arguments["target"]
        kind = arguments.get("kind", "agent")
        subprocess.run(
            ["python3", str(NORMALIZER), source, target, "--kind", kind],
            check=True,
        )
        return text_result(f"normalized {source} -> {target} as {kind}")

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
                    "name": "awp-pixel-plugin-and-mcp-codex",
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
