#!/usr/bin/env python3
"""Make the Chrome Web Store screenshots: 1280x800, 24-bit PNG, no alpha.

Usage (from chrome-extension/):
    python store-screenshots/capture.py [output folder]

Builds the screenshot page (real extension components with sample data),
serves it locally, photographs each screen with headless Chrome, and saves
RGB PNGs. Needs Chrome, Node (for Vite) and Pillow.
"""

import functools
import http.server
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
EXTENSION = HERE.parent
BUILD = HERE / "build"
SCREENS = 5
SIZE = (1280, 800)
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
]


def find_chrome() -> str:
    for candidate in CHROME_PATHS:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    sys.exit("Chrome not found; add its path to CHROME_PATHS.")


def build_page() -> None:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    subprocess.run(
        [npx, "vite", "build", "--config", str(HERE / "vite.config.js")],
        cwd=EXTENSION,
        check=True,
    )


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(folder: Path) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(QuietHandler, directory=str(folder))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def capture(chrome: str, url: str, path: Path) -> None:
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                # US English, so times read "1:00 PM" like the rest of the popup.
                "--lang=en-US",
                f"--window-size={SIZE[0]},{SIZE[1]}",
                # Time for the web font and the slot finder's async render.
                "--virtual-time-budget=6000",
                f"--user-data-dir={profile}",
                f"--screenshot={path}",
                url,
            ],
            check=True,
            capture_output=True,
        )


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "prompt2cal-store-screenshots"
    out.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    build_page()
    server = serve(BUILD)
    port = server.server_address[1]
    try:
        for number in range(1, SCREENS + 1):
            raw = out / f"raw-{number}.png"
            capture(chrome, f"http://127.0.0.1:{port}/index.html#{number}", raw)
            image = Image.open(raw).convert("RGB")  # the store wants no alpha
            if image.size != SIZE:
                image = image.crop((0, 0, *SIZE))
            final = out / f"prompt2cal-screenshot-{number}.png"
            image.save(final, "PNG")
            raw.unlink()
            print(f"wrote {final} ({image.size[0]}x{image.size[1]}, {image.mode})")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
