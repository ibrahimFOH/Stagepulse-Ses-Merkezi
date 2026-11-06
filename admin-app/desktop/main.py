# -*- coding: utf-8 -*-
"""Stagepulse Yönetim Paneli: yerel dosyaları paketlenmiş Windows kabuğu."""
import sys
from pathlib import Path
import webview


def resource_path(relative: str) -> str:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base / relative)


def main() -> None:
    webview.create_window(
        "Stagepulse | Usta Öğretmen Yönetim Paneli",
        resource_path("assets/index.html"),
        width=1280,
        height=820,
        min_size=(980, 650),
        background_color="#0b0b0c",
        text_select=True,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
