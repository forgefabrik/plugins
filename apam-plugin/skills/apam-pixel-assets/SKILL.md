---
name: apam-pixel-assets
description: Create and maintain professional pixel assets using Codex, image generation, Aseprite CLI automation, and MCP tools. Use for sprites, animation frames, sprite sheets, tiles, props, UI icons, facilities, environments, prompt catalogs, manifests, and production asset pipelines.
---

# APAM Pixel Assets

APAM means Aseprite + Pixel + MCP.

Use this skill when the user asks for pixel-art assets, sprite sheets, animation frames, Aseprite workflows, tiles, props, game UI assets, environments, facilities, icons, prompt catalogs, or project asset integration.

## Core Rule

Generate every final asset as its own image from its own prompt unless the user explicitly asks to edit an existing source file. Do not crop a preview sheet, do not slice a reference image, and do not treat a mood/reference image as source art. A reference image may guide style only.

## Pixel Style Block

For 2.5D pixel-art sprites, append this style block to every generation prompt:

`2.5D isometric pixel art sprite, classic 16-bit video game asset style, isolated on a solid absolute black background, dimetric projection (2:1 pixel ratio), clean sharp pixel outlines, no anti-aliasing, no floor shadows, orthographic perspective, flat colors, retro arcade aesthetic.`

Also include:

`Generate a single standalone sprite only, centered, no sprite sheet, no labels, no extra characters.`

For non-sprite pixel assets, preserve the same professional constraints: crisp pixels, no unwanted blur, deterministic asset naming, and project-ready dimensions.

## Aseprite Is The Production Pass

Aseprite is the final professional production tool. Use it after generation or normalization when the user needs:

- sprite sheets
- frame metadata JSON
- palette/indexed conversion
- dithering
- trimming and padding
- scaling
- animation-frame handoff
- batch conversion
- project-ready export

Available commands:

```bash
python3 /home/bkg/plugins/apam-plugin/scripts/aseprite_commands.py detect
python3 /home/bkg/plugins/apam-plugin/scripts/aseprite_commands.py export-sheet --help
python3 /home/bkg/plugins/apam-plugin/scripts/aseprite_commands.py convert --help
```

Prefer Aseprite exports over ad hoc image stitching when producing sheets or metadata.

## Aseprite Setup

APAM includes an Aseprite Linux setup command refactored from the idea of
`mak448a/compile-aseprite-linux`. Use APAM's command, not the upstream script
directly, because APAM adds dry-run planning, non-interactive flags, an APAM
install signature, and MCP exposure.

```bash
python3 /home/bkg/plugins/apam-plugin/scripts/setup_aseprite_linux.py detect
python3 /home/bkg/plugins/apam-plugin/scripts/setup_aseprite_linux.py plan
python3 /home/bkg/plugins/apam-plugin/scripts/setup_aseprite_linux.py install --yes --dry-run
python3 /home/bkg/plugins/apam-plugin/scripts/setup_aseprite_linux.py install --yes
```

Do not run a real install or uninstall without explicit user approval.

## Host Setup

Use `setup.sh` to install APAM adapters for Codex, OpenCode, and Claude-style MCP hosts:

```bash
/home/bkg/plugins/apam-plugin/setup.sh install all
```

Default mode is dry-run:

```bash
/home/bkg/plugins/apam-plugin/setup.sh plan all
```

Host behavior differs:

- Codex installs through the personal plugin marketplace and `codex plugin add`.
- OpenCode receives command markdown files, bin symlinks, and an `opencode.jsonc` MCP entry.
- Claude-style setup receives MCP config/docs under `~/.claude/apam-plugin`.

## Workflow

1. Read the requested prompt catalog, project spec, or user asset list.
2. Generate one image per requested asset/frame when using image generation.
3. Leave generated originals in `/home/bkg/.codex/generated_images/...`.
4. Copy and normalize generated images into the project asset tree.
5. Use Aseprite to export sprite sheets, metadata, indexed versions, previews, or production variants.
6. Update the project manifest/registry that consumes those assets.
7. Run the project’s relevant validation/build commands after code or manifest changes.

## Normalization

Use `scripts/normalize_sprite.py` from APAM Plugin for generated PNGs:

```bash
python3 /home/bkg/plugins/apam-plugin/scripts/normalize_sprite.py \
  /path/to/generated.png \
  /path/to/project/assets/agent_child_running_se_frame1.png \
  --kind agent
```

The normalizer keeps a solid black background, crops non-black content, nearest-neighbor scales it, and can place standing agent feet at `y=48`.

## Project-Specific Catalogs

Project-specific naming rules are allowed, but they must be treated as project overlays, not global plugin limits. For example, a lifecycle sprite catalog can use:

- `agent_infant_crawling_frame0.png` through `agent_infant_crawling_frame3.png`
- `agent_child_running_<se|sw|ne|nw>_frame<0|1|2|3>.png`
- `agent_student_tablet_<se|sw|ne|nw>_frame<0|1|2|3>.png`
- rooms, facilities, props, and other assets from the project catalog

## Verification

After writing assets:

- list output files
- inspect representative images
- run Aseprite export/metadata checks when a sheet is expected
- run project tests/builds when code or manifests changed
