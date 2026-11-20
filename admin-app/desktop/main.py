# -*- coding: utf-8 -*-
"""Stagepulse Yönetim Paneli: localhost üzerinden güvenli statik varlık sunucusu."""
from __future__ import annotations

import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import webview

APP_VERSION = "4.1.0"
HOST = "127.0.0.1"
PORT = 5173


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative


class LocalAssetServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    assets = resource_path("assets").resolve()
    if not assets.is_dir():
        raise RuntimeError(f"Yönetim arayüzü varlık klasörü bulunamadı: {assets}")

    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(
        *args, directory=str(assets), **kwargs
    )
    server = LocalAssetServer((HOST, PORT), handler)
    thread = threading.Thread(target=server.serve_forever, name="StagepulseLocalUI", daemon=True)
    thread.start()
    try:
        webview.create_window(
            f"Stagepulse | Usta Öğretmen Yönetim Paneli v{APP_VERSION}",
            f"http://{HOST}:{PORT}/index.html",
            width=1280,
            height=820,
            min_size=(980, 650),
            background_color="#0b0b0c",
            text_select=True,
        )
        webview.start(debug=False)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
