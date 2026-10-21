#!/usr/bin/env python3
"""Open the Windows Electron window. The card server can live somewhere else."""

import os
import shutil
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

DESKTOP = Path(__file__).resolve().parent
VERSION = "45.0.0"


def _local_root():
    local = subprocess.check_output(
        ["cmd.exe", "/c", "echo %LOCALAPPDATA%"],
        text=True,
        cwd="/mnt/c",
        stderr=subprocess.DEVNULL,
    ).strip()
    return Path(subprocess.check_output(["wslpath", "-u", local], text=True).strip()) / "card-creator"


def _windows_path(path):
    return subprocess.check_output(["wslpath", "-w", str(path)], text=True).strip()


def _runtime():
    root = _local_root()
    runtime = root / "runtime"
    marker = runtime / "version"
    bundled = DESKTOP / "node_modules" / "electron" / "dist"
    if (bundled / "electron.exe").is_file():
        version = (bundled / "version").read_text().strip()
        ready = (runtime / "electron.exe").is_file() and marker.is_file() and marker.read_text().strip() == version
        if not ready:
            if runtime.exists():
                shutil.rmtree(runtime)
            print("Preparing the window…", flush=True)
            shutil.copytree(bundled, runtime)
        return runtime
    if (runtime / "electron.exe").is_file() and marker.is_file() and marker.read_text().strip() == VERSION:
        return runtime
    print("Downloading the Windows window…", flush=True)
    url = f"https://github.com/electron/electron/releases/download/v{VERSION}/electron-v{VERSION}-win32-x64.zip"
    if runtime.exists():
        shutil.rmtree(runtime)
    runtime.mkdir(parents=True)
    request = Request(url, headers={"User-Agent": "card-creator"})
    with urlopen(request) as response:
        payload = response.read()
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        archive.extractall(runtime)
    marker.write_text(VERSION)
    return runtime


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: open_window.py http://127.0.0.1:PORT")
    url = sys.argv[1]
    runtime = _runtime()
    app_dir = runtime.parent / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    for name in ("main.js", "package.json"):
        shutil.copy2(DESKTOP / name, app_dir / name)
    env = os.environ.copy()
    env["CARD_URL"] = url
    shared = [part for part in env.get("WSLENV", "").split(":") if part and not part.startswith("CARD_URL")]
    shared.append("CARD_URL")
    env["WSLENV"] = ":".join(shared)
    process = subprocess.Popen(
        [str(runtime / "electron.exe"), _windows_path(app_dir), "--", f"--card-url={url}"],
        env=env,
        cwd=str(runtime),
    )
    raise SystemExit(process.wait())


if __name__ == "__main__":
    main()
