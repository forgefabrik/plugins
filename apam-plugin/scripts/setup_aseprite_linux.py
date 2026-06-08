#!/usr/bin/env python3
"""APAM Aseprite setup command for Linux.

Refactored from the idea of mak448a/compile-aseprite-linux, but implemented as
an APAM-native, non-interactive setup tool with dry-run planning by default.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


SIGNATURE_NAME = "apam-plugin"
ASEPRITE_RELEASE_API = "https://api.github.com/repos/aseprite/aseprite/releases/latest"


def paths() -> dict[str, Path]:
    home = Path.home()
    data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    install_dir = data_home / "aseprite"
    binary_dir = home / ".local" / "bin"
    launcher_dir = data_home / "applications"
    return {
        "install_dir": install_dir,
        "binary_dir": binary_dir,
        "launcher_dir": launcher_dir,
        "signature": install_dir / SIGNATURE_NAME,
        "binary": binary_dir / "aseprite",
        "launcher": launcher_dir / "aseprite.desktop",
        "icon": install_dir / "data" / "icons" / "ase256.png",
    }


def run(command: list[str], *, cwd: Path | None = None, dry_run: bool = False) -> None:
    printable = " ".join(command)
    print(printable)
    if not dry_run:
        subprocess.run(command, cwd=cwd, check=True)


def detect(_args: argparse.Namespace) -> None:
    binary = shutil.which("aseprite") or str(paths()["binary"])
    exists = Path(binary).exists()
    version = None
    if exists:
        try:
            version = subprocess.run(
                [binary, "--version"], check=True, capture_output=True, text=True
            ).stdout.strip()
        except Exception:
            version = None
    payload = {
        "platform": platform.platform(),
        "binary": binary,
        "exists": exists,
        "version": version,
        "paths": {key: str(value) for key, value in paths().items()},
    }
    print(json.dumps(payload, indent=2))


def distro_package_manager() -> str:
    os_release = Path("/etc/os-release")
    text = os_release.read_text(errors="ignore") if os_release.exists() else ""
    lowered = text.lower()
    if any(name in lowered for name in ("ubuntu", "debian", "mint")):
        return "apt"
    if "fedora" in lowered:
        return "dnf"
    if any(name in lowered for name in ("arch", "manjaro")):
        return "pacman"
    return "unsupported"


def dependency_command(package_manager: str) -> list[str]:
    if package_manager == "apt":
        return [
            "sudo",
            "apt-get",
            "install",
            "-y",
            "g++",
            "cmake",
            "ninja-build",
            "libx11-dev",
            "libxcursor-dev",
            "libxi-dev",
            "libgl1-mesa-dev",
            "libfontconfig1-dev",
        ]
    if package_manager == "dnf":
        return [
            "sudo",
            "dnf",
            "install",
            "-y",
            "gcc-c++",
            "cmake",
            "ninja-build",
            "libX11-devel",
            "libXcursor-devel",
            "libXi-devel",
            "mesa-libGL-devel",
            "fontconfig-devel",
        ]
    if package_manager == "pacman":
        return [
            "sudo",
            "pacman",
            "-S",
            "--needed",
            "--noconfirm",
            "gcc",
            "cmake",
            "ninja",
            "libx11",
            "libxcursor",
            "libxi",
            "mesa",
            "fontconfig",
        ]
    raise SystemExit("Unsupported Linux distro. APAM supports apt, dnf, and pacman.")


def latest_source_url() -> str:
    with urllib.request.urlopen(ASEPRITE_RELEASE_API, timeout=30) as response:
        release = json.loads(response.read().decode("utf-8"))
    for asset in release.get("assets", []):
        url = asset.get("browser_download_url", "")
        if url.endswith("-Source.zip"):
            return url
    raise SystemExit("Could not find Aseprite Source.zip in latest release assets.")


def plan(args: argparse.Namespace) -> None:
    package_manager = distro_package_manager()
    payload = {
        "package_manager": package_manager,
        "dependency_command": dependency_command(package_manager),
        "install_paths": {key: str(value) for key, value in paths().items()},
        "source": "latest Aseprite release Source.zip",
        "dry_run": args.dry_run,
        "signature": SIGNATURE_NAME,
        "upstream_inspiration": "https://github.com/mak448a/compile-aseprite-linux",
    }
    print(json.dumps(payload, indent=2))


def install(args: argparse.Namespace) -> None:
    if not args.yes:
        raise SystemExit("Refusing install without --yes. Run plan first.")

    p = paths()
    if p["install_dir"].exists() and not p["signature"].exists() and not args.force:
        raise SystemExit(
            f"{p['install_dir']} exists but was not created by APAM. Use --force to replace."
        )
    if p["binary"].exists() and not p["signature"].exists() and not args.force:
        raise SystemExit(f"{p['binary']} exists. Use --force to replace.")

    dry_run = args.dry_run
    package_manager = distro_package_manager()
    run(dependency_command(package_manager), dry_run=dry_run)

    work_dir = Path(args.work_dir) if args.work_dir else Path(tempfile.mkdtemp(prefix="apam-aseprite-"))
    work_dir.mkdir(parents=True, exist_ok=True)
    source_url = args.source_url or latest_source_url()
    archive = work_dir / Path(source_url).name

    if dry_run:
        print(f"download {source_url} -> {archive}")
    else:
        urllib.request.urlretrieve(source_url, archive)

    source_dir = work_dir / "aseprite"
    if dry_run:
        print(f"unzip {archive} -> {source_dir}")
    else:
        if source_dir.exists():
            shutil.rmtree(source_dir)
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(source_dir)

    run(["./build.sh", "--auto", "--norun"], cwd=source_dir, dry_run=dry_run)

    if dry_run:
        print(f"install build/bin/* -> {p['install_dir']}")
        return

    if p["install_dir"].exists():
        shutil.rmtree(p["install_dir"])
    p["install_dir"].mkdir(parents=True, exist_ok=True)
    p["binary_dir"].mkdir(parents=True, exist_ok=True)
    p["launcher_dir"].mkdir(parents=True, exist_ok=True)

    build_bin = source_dir / "build" / "bin"
    for item in build_bin.iterdir():
        target = p["install_dir"] / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    p["signature"].write_text("installed by APAM Plugin\n")

    if p["binary"].exists() or p["binary"].is_symlink():
        p["binary"].unlink()
    p["binary"].symlink_to(p["install_dir"] / "aseprite")

    desktop_source = source_dir / "src" / "desktop" / "linux" / "aseprite.desktop"
    desktop = desktop_source.read_text()
    lines = []
    for line in desktop.splitlines():
        if line.startswith("TryExec="):
            lines.append(f"TryExec={p['binary']}")
        elif line.startswith("Exec="):
            lines.append(f"Exec={p['binary']} %U")
        elif line.startswith("Icon="):
            lines.append(f"Icon={p['icon']}")
        else:
            lines.append(line)
    p["launcher"].write_text("\n".join(lines) + "\n")
    print(f"Aseprite installed to {p['install_dir']}")


def uninstall(args: argparse.Namespace) -> None:
    if not args.yes:
        raise SystemExit("Refusing uninstall without --yes.")
    p = paths()
    if not p["signature"].exists() and not args.force:
        raise SystemExit("APAM signature not found. Use --force to remove anyway.")

    for key in ("binary", "launcher"):
        target = p[key]
        if target.exists() or target.is_symlink():
            print(f"remove {target}")
            if not args.dry_run:
                target.unlink()
    if p["install_dir"].exists():
        print(f"remove {p['install_dir']}")
        if not args.dry_run:
            shutil.rmtree(p["install_dir"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    detect_parser = subcommands.add_parser("detect")
    detect_parser.set_defaults(func=detect)

    plan_parser = subcommands.add_parser("plan")
    plan_parser.add_argument("--dry-run", action="store_true", default=True)
    plan_parser.set_defaults(func=plan)

    install_parser = subcommands.add_parser("install")
    install_parser.add_argument("--yes", action="store_true")
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.add_argument("--force", action="store_true")
    install_parser.add_argument("--work-dir")
    install_parser.add_argument("--source-url")
    install_parser.set_defaults(func=install)

    uninstall_parser = subcommands.add_parser("uninstall")
    uninstall_parser.add_argument("--yes", action="store_true")
    uninstall_parser.add_argument("--dry-run", action="store_true")
    uninstall_parser.add_argument("--force", action="store_true")
    uninstall_parser.set_defaults(func=uninstall)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
