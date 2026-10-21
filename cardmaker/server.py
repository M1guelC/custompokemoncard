"""Desktop card creator. A local server draws the cards; a window shows the editor."""

import json
import mimetypes
import os
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import cgi

from cardmaker.assets import CACHE, ensure_cache, type_slug
from cardmaker.layout import CARDS, RARITIES, TYPES, type_label
from cardmaker.render import open_photo, render_png

WEB = Path(__file__).resolve().parent / "web"
HOST = "127.0.0.1"
PORT = 8765


def schema():
    cards = []
    for card_id, spec in CARDS.items():
        cards.append(
            {
                "id": card_id,
                "label": spec["label"],
                "description": spec["description"],
                "flip": spec.get("flip", False),
                "defaults": spec["defaults"],
                "sections": spec["sections"],
            }
        )
    return {
        "types": [{"id": key, "label": type_label(key)} for key in TYPES],
        "rarities": RARITIES,
        "cards": cards,
    }


def merged(card_id, incoming):
    data = dict(CARDS[card_id]["defaults"])
    for key, value in incoming.items():
        if isinstance(value, str):
            data[key] = value[:800]
    return data


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/schema":
            self._bytes(json.dumps(schema()).encode(), "application/json")
            return
        if path.startswith("/icons/"):
            slug = path.split("/", 2)[-1]
            file_path = CACHE / "icons" / Path(slug).name
            if file_path.is_file():
                self._bytes(file_path.read_bytes(), "image/png")
                return
            self.send_error(404)
            return
        if path == "/":
            self._file(WEB / "index.html")
            return
        relative = unquote(path.lstrip("/"))
        file_path = (WEB / relative).resolve()
        if WEB.resolve() in file_path.parents and file_path.is_file():
            self._file(file_path)
            return
        self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/preview":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 25_000_000:
            self._bytes(b'{"error":"That picture is too large."}', "application/json", 413)
            return
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )
        incoming = {}
        photo = None
        if form.list:
            for item in form.list:
                if getattr(item, "filename", None):
                    raw = item.file.read()
                    if raw:
                        try:
                            photo = open_photo(raw)
                        except Exception:
                            self._bytes(b'{"error":"That picture could not be opened."}', "application/json", 400)
                            return
                elif item.name:
                    incoming[item.name] = item.value
        card_id = incoming.get("card") or "character"
        if card_id not in CARDS:
            self._bytes(b'{"error":"Unknown card."}', "application/json", 400)
            return
        side = incoming.get("side") or "front"
        preview = incoming.get("purpose") != "download"
        try:
            payload, mime = render_png(card_id, merged(card_id, incoming), photo, side, preview)
        except Exception as error:
            message = json.dumps({"error": f"Could not draw the card. {error}"})
            self._bytes(message.encode(), "application/json", 500)
            return
        self._bytes(payload, mime)

    def _file(self, path):
        mime, _ = mimetypes.guess_type(str(path))
        self._bytes(path.read_bytes(), mime or "application/octet-stream")

    def _bytes(self, payload, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        if args and str(args[1]) != "200":
            super().log_message(fmt, *args)


def _server_only():
    return os.environ.get("CARD_SERVER_ONLY") == "1" or os.environ.get("CARD_CONTAINER") == "1"


def start_server():
    ensure_cache()
    if _server_only():
        host = "0.0.0.0"
        port = int(os.environ.get("PORT", "8765"))
    else:
        host = HOST
        port = 0
    server = ThreadingHTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _wsl():
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def _windows_path(path):
    return subprocess.check_output(["wslpath", "-w", str(path)], text=True).strip()


def _windows_app():
    """Copy Electron onto the Windows drive. A copy that stays on the WSL
    drive cannot start its own graphics process."""
    local = subprocess.check_output(
        ["cmd.exe", "/c", "echo %LOCALAPPDATA%"],
        text=True,
        cwd="/mnt/c",
        stderr=subprocess.DEVNULL,
    ).strip()
    root = Path(subprocess.check_output(["wslpath", "-u", local], text=True).strip()) / "card-creator"
    desktop = Path(__file__).resolve().parent.parent / "desktop"
    dist = desktop / "node_modules" / "electron" / "dist"
    version = (dist / "version").read_text().strip()
    runtime = root / "runtime"
    marker = runtime / "version"
    if not marker.is_file() or marker.read_text().strip() != version:
        if runtime.exists():
            shutil.rmtree(runtime)
        print("Preparing the window…", flush=True)
        shutil.copytree(dist, runtime)
    app_dir = root / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    for name in ("main.js", "package.json"):
        shutil.copy2(desktop / name, app_dir / name)
    return runtime / "electron.exe", _windows_path(app_dir)


def electron_command(url):
    desktop = Path(__file__).resolve().parent.parent / "desktop"
    dist = desktop / "node_modules" / "electron" / "dist"
    windows = dist / "electron.exe"
    linux = dist / "electron"
    flag = f"--card-url={url}"
    if _wsl() and windows.is_file():
        executable, app_dir = _windows_app()
        return [str(executable), app_dir, "--", flag]
    if linux.is_file():
        return [str(linux), str(desktop), "--", flag]
    if windows.is_file():
        return [str(windows), str(desktop), "--", flag]
    raise SystemExit("Install the window with:\n  cd desktop && npm install")


def serve():
    server = start_server()
    _host, port = server.server_address
    if _server_only():
        print(f"Card creator server is running on port {port}", flush=True)
        try:
            threading.Event().wait()
        finally:
            server.shutdown()
            server.server_close()
        return
    url = f"http://{HOST}:{port}"
    print(f"Card creator is running at {url}", flush=True)
    env = os.environ.copy()
    env["CARD_URL"] = url
    shared = [part for part in env.get("WSLENV", "").split(":") if part and not part.startswith("CARD_URL")]
    shared.append("CARD_URL")
    env["WSLENV"] = ":".join(shared)
    try:
        command = electron_command(url)
    except SystemExit:
        server.shutdown()
        server.server_close()
        raise
    executable = Path(command[0])
    # Windows exits immediately when the working directory is a WSL path.
    cwd = str(executable.parent) if executable.suffix.lower() == ".exe" else None
    process = subprocess.Popen(command, env=env, cwd=cwd)
    try:
        process.wait()
    finally:
        server.shutdown()
        server.server_close()
