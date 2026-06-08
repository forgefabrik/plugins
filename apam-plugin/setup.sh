#!/usr/bin/env bash
set -euo pipefail

# APAM = Aseprite + Pixel + MCP.
# Host adapter installer for Codex, OpenCode, and Claude-style MCP clients.

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_NAME="apam-plugin"
ACTION="${1:-plan}"
TARGET="${2:-all}"
FORCE="${FORCE:-0}"

usage() {
  cat <<'EOF'
APAM Plugin setup

Usage:
  ./setup.sh plan [codex|opencode|claude|aseprite|all]
  ./setup.sh install [codex|opencode|claude|aseprite|all]
  ./setup.sh uninstall [codex|opencode|claude|all]

Environment:
  FORCE=1    replace existing generated command/doc files where supported

Examples:
  ./setup.sh plan all
  ./setup.sh install codex
  ./setup.sh install opencode
  ./setup.sh install claude
  ./setup.sh install all
EOF
}

if [[ "${ACTION}" == "-h" || "${ACTION}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! "${ACTION}" =~ ^(plan|install|uninstall)$ ]]; then
  echo "Unknown action: ${ACTION}" >&2
  usage
  exit 2
fi

if [[ ! "${TARGET}" =~ ^(codex|opencode|claude|aseprite|all)$ ]]; then
  echo "Unknown target: ${TARGET}" >&2
  usage
  exit 2
fi

is_plan() {
  [[ "${ACTION}" == "plan" ]]
}

say_do() {
  if is_plan; then
    printf '[plan]'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

write_file() {
  local path="$1"
  local content="$2"
  if [[ -e "${path}" && "${FORCE}" != "1" && "${ACTION}" == "install" ]]; then
    echo "skip existing ${path} (set FORCE=1 to replace)"
    return
  fi
  if is_plan; then
    echo "[plan] write ${path}"
  else
    mkdir -p "$(dirname "${path}")"
    printf '%s\n' "${content}" > "${path}"
  fi
}

install_codex() {
  local marketplace="${HOME}/.agents/plugins/marketplace.json"
  echo "== Codex ${ACTION} =="

  if [[ "${ACTION}" == "uninstall" ]]; then
    if command -v codex >/dev/null 2>&1; then
      say_do codex plugin remove "${PLUGIN_NAME}@personal"
    else
      echo "codex CLI not found"
    fi
    return
  fi

  if is_plan; then
    echo "[plan] ensure ${marketplace} contains ${PLUGIN_NAME}"
    echo "[plan] codex plugin add ${PLUGIN_NAME}@personal"
    return
  fi

  MARKETPLACE="${marketplace}" PLUGIN_ROOT="${PLUGIN_ROOT}" python3 - <<'PY'
import json
import os
from pathlib import Path

marketplace = Path(os.environ["MARKETPLACE"])
plugin_root = Path(os.environ["PLUGIN_ROOT"])
plugin_name = plugin_root.name
marketplace.parent.mkdir(parents=True, exist_ok=True)

if marketplace.exists():
    data = json.loads(marketplace.read_text())
else:
    data = {"name": "personal", "interface": {"displayName": "Personal"}, "plugins": []}

old_names = {
    "pixel-plugin",
    "apw-pixel-plugin",
    "awp-pixel-plugin-and-mcp-codex",
    "apam-plugin-codex",
    "apam-plugin",
}
plugins = data.setdefault("plugins", [])
plugins[:] = [item for item in plugins if item.get("name") not in old_names]
plugins.append({
    "name": plugin_name,
    "source": {"source": "local", "path": f"./plugins/{plugin_name}"},
    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
    "category": "Design",
})
marketplace.write_text(json.dumps(data, indent=2) + "\n")
PY

  if command -v codex >/dev/null 2>&1; then
    codex plugin remove awp-pixel-plugin-and-mcp-codex@personal >/dev/null 2>&1 || true
    codex plugin remove apam-plugin-codex@personal >/dev/null 2>&1 || true
    codex plugin remove apam-plugin@personal >/dev/null 2>&1 || true
    codex plugin add apam-plugin@personal
  else
    echo "codex CLI not found; marketplace updated only"
  fi
}

install_opencode() {
  local config_dir="${HOME}/.config/opencode"
  local commands_dir="${config_dir}/commands"
  local bin_dir="${config_dir}/bin"
  local jsonc="${config_dir}/opencode.jsonc"
  echo "== OpenCode ${ACTION} =="

  if [[ "${ACTION}" == "uninstall" ]]; then
    say_do rm -f "${bin_dir}/apam-aseprite" "${bin_dir}/apam-setup-aseprite" "${bin_dir}/apam-normalize-sprite" "${bin_dir}/apam-mcp"
    say_do rm -f "${commands_dir}/apam-setup.md" "${commands_dir}/apam-aseprite.md"
    echo "MCP config removal from ${jsonc} is left manual to avoid changing user JSON unexpectedly."
    return
  fi

  say_do mkdir -p "${commands_dir}" "${bin_dir}"
  if is_plan; then
    echo "[plan] link APAM scripts into ${bin_dir}"
  else
    ln -sfn "${PLUGIN_ROOT}/scripts/aseprite_commands.py" "${bin_dir}/apam-aseprite"
    ln -sfn "${PLUGIN_ROOT}/scripts/setup_aseprite_linux.py" "${bin_dir}/apam-setup-aseprite"
    ln -sfn "${PLUGIN_ROOT}/scripts/normalize_sprite.py" "${bin_dir}/apam-normalize-sprite"
    ln -sfn "${PLUGIN_ROOT}/scripts/mcp_server.py" "${bin_dir}/apam-mcp"
  fi

  write_file "${commands_dir}/apam-setup.md" "---
description: Detect, plan, or install APAM Aseprite + Pixel + MCP tooling
---

APAM = Aseprite + Pixel + MCP.

Commands:
- \`${bin_dir}/apam-setup-aseprite detect\`
- \`${bin_dir}/apam-setup-aseprite plan\`
- \`${bin_dir}/apam-setup-aseprite install --yes --dry-run\`
- \`${bin_dir}/apam-setup-aseprite install --yes\`
"

  write_file "${commands_dir}/apam-aseprite.md" "---
description: Use APAM Aseprite commands for professional pixel assets
---

APAM = Aseprite + Pixel + MCP.

Commands:
- \`${bin_dir}/apam-aseprite detect\`
- \`${bin_dir}/apam-aseprite export-sheet --help\`
- \`${bin_dir}/apam-aseprite convert --help\`
"

  if is_plan; then
    echo "[plan] update ${jsonc} mcp.apam"
  else
    JSONC="${jsonc}" BIN_DIR="${bin_dir}" python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["JSONC"])
bin_dir = Path(os.environ["BIN_DIR"])
if path.exists():
    data = json.loads(path.read_text())
else:
    data = {"$schema": "https://opencode.ai/config.json"}
data.setdefault("mcp", {})["apam"] = {
    "type": "local",
    "command": [str(bin_dir / "apam-mcp")],
    "enabled": True,
}
path.write_text(json.dumps(data, indent=2) + "\n")
PY
  fi
}

install_claude() {
  local claude_dir="${HOME}/.claude/apam-plugin"
  echo "== Claude-style ${ACTION} =="

  if [[ "${ACTION}" == "uninstall" ]]; then
    say_do rm -rf "${claude_dir}"
    return
  fi

  say_do mkdir -p "${claude_dir}"
  write_file "${claude_dir}/mcp.json" "{
  \"mcpServers\": {
    \"apam\": {
      \"command\": \"python3\",
      \"args\": [\"${PLUGIN_ROOT}/scripts/mcp_server.py\"]
    }
  }
}"
  write_file "${claude_dir}/APAM.md" "# APAM Plugin

APAM = Aseprite + Pixel + MCP.

Use this MCP server for professional pixel assets, Aseprite export, sprite sheets,
normalization, palette/indexed conversion, and setup detection.

MCP config is in \`${claude_dir}/mcp.json\`.
"
  command -v claude >/dev/null 2>&1 || echo "claude CLI not found; wrote Claude-style MCP config files only."
}

install_aseprite() {
  echo "== Aseprite ${ACTION} =="
  if [[ "${ACTION}" == "uninstall" ]]; then
    echo "Use scripts/setup_aseprite_linux.py uninstall --yes for explicit Aseprite removal."
    return
  fi
  say_do python3 "${PLUGIN_ROOT}/scripts/setup_aseprite_linux.py" detect
  say_do python3 "${PLUGIN_ROOT}/scripts/setup_aseprite_linux.py" plan
}

dispatch_one() {
  case "$1" in
    codex) install_codex ;;
    opencode) install_opencode ;;
    claude) install_claude ;;
    aseprite) install_aseprite ;;
  esac
}

if [[ "${TARGET}" == "all" ]]; then
  dispatch_one aseprite
  dispatch_one codex
  dispatch_one opencode
  dispatch_one claude
else
  dispatch_one "${TARGET}"
fi

echo "APAM setup complete: action=${ACTION} target=${TARGET}"
