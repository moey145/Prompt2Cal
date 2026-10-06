#!/usr/bin/env python3
"""Make the Chrome Web Store screenshots and promo tiles: 24-bit PNG, no alpha.

Usage (from chrome-extension/):
    python store-screenshots/capture.py [output folder]

Builds the screenshot page (real extension components with sample data),
serves it locally, photographs each screen with headless Chrome, and saves
RGB PNGs. Also writes transparent WebP visuals for prompt2cal.com into
docs/public/images. Needs Chrome, Node (for Vite) and Pillow.
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
SITE_IMAGES_DIR = EXTENSION.parent / "docs" / "public" / "images"
# Visuals for prompt2cal.com: transparent, cropped, at 2x for sharp screens.
SITE_IMAGES = ["input", "review", "clash", "slots", "rightclick"]
BUILD = HERE / "build"
# (file name, page hash, size): five screenshots and the two promo tiles.
IMAGES = [(f"prompt2cal-screenshot-{n}", str(n), (1280, 800)) for n in range(1, 6)] + [
    ("prompt2cal-promo-small", "small", (440, 280)),
    ("prompt2cal-promo-marquee", "marquee", (1400, 560)),
]
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


def capture(chrome: str, url: str, path: Path, size, scale=1, transparent=False) -> None:
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--force-device-scale-factor={scale}",
                *(["--default-background-color=00000000"] if transparent else []),
                # US English, so times read "1:00 PM" like the rest of the popup.
                "--lang=en-US",
                f"--window-size={size[0]},{size[1]}",
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
        for name, page, size in IMAGES:
            raw = out / f"raw-{name}.png"
            capture(chrome, f"http://127.0.0.1:{port}/index.html#{page}", raw, size)
            image = Image.open(raw).convert("RGB")  # the store wants no alpha
            if image.size != size:
                image = image.crop((0, 0, *size))
            final = out / f"{name}.png"
            # Save beside it and swap in, so a viewer holding the old file
            # open does not leave a half-written image.
            fresh = out / f"new-{name}.png"
            image.save(fresh, "PNG")
            fresh.replace(final)
            raw.unlink()
            print(f"wrote {final} ({image.size[0]}x{image.size[1]}, {image.mode})")
        SITE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        for name in SITE_IMAGES:
            raw = SITE_IMAGES_DIR / f"raw-{name}.png"
            url = f"http://127.0.0.1:{port}/index.html#site-{name}"
            capture(chrome, url, raw, (760, 1100), scale=2, transparent=True)
            image = Image.open(raw).convert("RGBA")
            image = image.crop(image.getchannel("A").getbbox())  # trim to the shadow's edge
            final = SITE_IMAGES_DIR / f"{name}.webp"
            image.save(final, "WEBP", quality=88, method=6)
            raw.unlink()
            print(f"wrote {final} ({image.size[0]}x{image.size[1]}, {final.stat().st_size // 1024} KB)")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
