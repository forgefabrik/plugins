# AWP Pixel Plugin and MCP Codex

AWP Pixel Plugin and MCP Codex is a local Codex plugin for producing AWP-style
pixel-art sprites and exposing small sprite-pipeline tools over MCP. It is
inspired by `willibrandon/pixel-plugin`, but rebranded and adapted for the AWP
asset pipeline instead of being tied to a specific external editor workflow.

## What It Does

- Generates each sprite as an individual image from its own prompt.
- Preserves the rule that reference images are style examples, not crop sources.
- Normalizes generated PNGs into 64x64 black-background sprite files.
- Keeps AWP/APW sprite naming and manifest updates consistent.
- Supports the lifecycle-agent prompts in `/home/bkg/workspace/pixel/work.md`.
- Provides a local MCP server with sprite style, prompt catalog, and normalize helpers.

## Layout

- `.codex-plugin/plugin.json` declares the Codex plugin.
- `.mcp.json` declares the local MCP server for Codex.
- `skills/apw-pixel-sprites/SKILL.md` defines the APW sprite workflow.
- `scripts/normalize_sprite.py` converts generated PNGs into 64x64 sprite assets.
- `scripts/mcp_server.py` exposes lightweight MCP sprite helpers.
- `assets/apw-master-style.txt` stores the reusable master style block.

## Example

```bash
python3 scripts/normalize_sprite.py \
  /path/to/generated.png \
  /home/bkg/repo/apw-rs/crates/apw-server/assets/sprites/agents/agent_child_running_se_frame1.png \
  --kind agent
```
