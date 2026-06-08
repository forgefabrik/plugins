---
name: apw-pixel-sprites
description: Generate and maintain AWP Pixel Plugin and MCP Codex sprite assets from prompt catalogs. Use when creating individual 2.5D isometric 16-bit sprites, animation frames, directions, rooms, facilities, props, or manifests for the AWP/APW project.
---

# AWP Pixel Sprites

Use this skill when the user asks for pixel-art sprites, APW lifecycle agents, 64x64 sprite assets, animation frames, or assets from `/home/bkg/workspace/pixel/work.md`.

## Core Rule

Generate every sprite as its own image from its own prompt. Do not crop a preview sheet, do not slice a reference image, and do not treat a mood/reference image as source art. A reference image may guide style only.

## Style Block

Append this style block to every sprite prompt:

`2.5D isometric pixel art sprite, classic 16-bit video game asset style, isolated on a solid absolute black background, dimetric projection (2:1 pixel ratio), clean sharp pixel outlines, no anti-aliasing, no floor shadows, orthographic perspective, flat colors, retro arcade aesthetic.`

Also include:

`Generate a single standalone sprite only, centered, no sprite sheet, no labels, no extra characters.`

## APW Agent Naming

Write files under:

`/home/bkg/repo/apw-rs/crates/apw-server/assets/sprites/agents/`

Use the prompt catalog filenames exactly:

- `agent_infant_crawling_frame0.png` through `agent_infant_crawling_frame3.png`
- `agent_child_running_<direction>_frame<frame>.png`
- `agent_student_tablet_<direction>_frame<frame>.png`
- `agent_junior_dev_typing_<direction>_frame<frame>.png`
- `agent_senior_arch_focus_<direction>_frame<frame>.png`
- `agent_mentor_lecturing_<direction>_frame<frame>.png`
- `agent_retired_walking_<direction>_frame<frame>.png`
- `agent_archived_sphere_frame0.png` through `agent_archived_sphere_frame3.png`

Directions are `se`, `sw`, `ne`, and `nw`. Frames are `0`, `1`, `2`, and `3`.

## Workflow

1. Read the requested prompt catalog or `/home/bkg/workspace/pixel/work.md`.
2. Generate one image per requested sprite/frame.
3. Leave generated originals in `/home/bkg/.codex/generated_images/...`.
4. Copy and normalize each generated image into the APW asset tree.
5. Update `crates/apw-server/assets/sprites/manifest.json`.
6. If the server should show the new assets, ensure `/assets/sprites/*path` serves the file and the office HTML references the new file paths.
7. Run `cargo check -p apw-server` after server changes.

## Normalization

Use `scripts/normalize_sprite.py` from AWP Pixel Plugin and MCP Codex for generated PNGs:

```bash
python3 /home/bkg/plugins/awp-pixel-plugin-and-mcp-codex/scripts/normalize_sprite.py \
  /path/to/generated.png \
  /home/bkg/repo/apw-rs/crates/apw-server/assets/sprites/agents/agent_child_running_se_frame1.png \
  --kind agent
```

The normalizer keeps a solid black background, crops non-black content, nearest-neighbor scales it, and places standing agent feet at `y=48`.

## Verification

After writing assets, list the files and inspect representative images. For server integration, check:

```bash
cargo check -p apw-server
```
