# APAM Plugin

APAM Plugin is a local Codex plugin for professional pixel assets,
Aseprite automation, and MCP-backed asset workflows. It is inspired by
`willibrandon/pixel-plugin`, but rebranded as a general-purpose Codex plugin
instead of being tied to one project or one sprite catalog.

APAM means Aseprite + Pixel + MCP.

The Linux Aseprite setup flow is an APAM-native refactor inspired by
`mak448a/compile-aseprite-linux`. APAM keeps the useful compile/install idea,
adds non-interactive planning, dry-run safety, an APAM install signature, MCP
exposure, and explicit commands.

## What It Does

- Generates each asset as an individual image from its own prompt.
- Preserves the rule that reference images are style examples, not crop sources.
- Uses Aseprite batch mode for professional sheet export, metadata, conversion,
  palette/indexed workflows, scaling, trimming, and production handoff.
- Normalizes generated PNGs into consistent sprite/asset files when needed.
- Keeps asset naming, manifest updates, and project integration consistent.
- Can support lifecycle sprites, game sprites, tiles, props, icons, UI assets,
  facilities, environments, and any future pixel pipeline.
- Provides a local MCP server with style, prompt, normalize, and Aseprite helpers.

## Layout

- `.codex-plugin/plugin.json` declares the Codex plugin.
- `.mcp.json` declares the local MCP server for Codex.
- `skills/apam-pixel-assets/SKILL.md` defines the general asset workflow.
- `scripts/aseprite_commands.py` wraps Aseprite CLI commands for Codex/MCP.
- `scripts/normalize_sprite.py` converts generated PNGs into consistent sprite assets.
- `scripts/mcp_server.py` exposes lightweight MCP asset helpers.
- `assets/pixel-master-style.txt` stores the reusable pixel-art style block.

## Aseprite Commands

Detect Aseprite:

```bash
python3 scripts/aseprite_commands.py detect
```

Plan or run the APAM Linux setup command:

```bash
python3 scripts/setup_aseprite_linux.py detect
python3 scripts/setup_aseprite_linux.py plan
python3 scripts/setup_aseprite_linux.py install --yes --dry-run
python3 scripts/setup_aseprite_linux.py install --yes
```

## Host Setup

APAM ships one host adapter for Codex, OpenCode, and Claude-style MCP config.
The setup script is dry-run by default:

```bash
./setup.sh plan all
./setup.sh install codex
./setup.sh install opencode
./setup.sh install claude
./setup.sh install all
```

Host differences:

- Codex uses `.codex-plugin/plugin.json`, `.mcp.json`, skills, and a marketplace entry.
- OpenCode uses command markdown files, `~/.config/opencode/bin`, and `opencode.jsonc` MCP config.
- Claude-style setup writes MCP config/docs under `~/.claude/apam-plugin`.

Export a professional sheet plus JSON metadata:

```bash
python3 scripts/aseprite_commands.py export-sheet \
  --sheet /tmp/agents_sheet.png \
  --data /tmp/agents_sheet.json \
  --sheet-type rows \
  --columns 4 \
  frame0.png frame1.png frame2.png frame3.png
```

Convert through Aseprite, optionally using indexed mode and dithering:

```bash
python3 scripts/aseprite_commands.py convert \
  input.png output.png \
  --color-mode indexed \
  --dithering-algorithm ordered
```

Normalize a generated image before Aseprite export:

```bash
python3 scripts/normalize_sprite.py \
  /path/to/generated.png \
  /path/to/project/assets/agent_child_running_se_frame1.png \
  --kind agent
```

## MCP Tools

The plugin exposes local MCP tools for Codex:

- `apam_pixel_master_style`
- `apam_pixel_asset_patterns`
- `apam_pixel_normalize_sprite`
- `apam_aseprite_detect`
- `apam_aseprite_setup_detect`
- `apam_aseprite_setup_plan`
- `apam_aseprite_setup_install`
- `apam_aseprite_export_sheet`
- `apam_aseprite_convert`
