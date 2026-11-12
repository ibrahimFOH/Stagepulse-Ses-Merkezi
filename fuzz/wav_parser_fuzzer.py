#!/usr/bin/env python3
"""Atheris fuzz target for the untrusted PCM WAV parser and RIFF chunk boundaries."""
from __future__ import annotations

import os
import sys
import tempfile

import atheris

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "windows"))

with atheris.instrument_imports():
    import wave
    from core.audio_tools import analyze_wav


def TestOneInput(data: bytes) -> None:
    # Mutations cover truncated RIFF chunks and attacker-controlled declared sizes.
    if len(data) > 1_048_576:
        return
    fd, path = tempfile.mkstemp(suffix=".wav")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        try:
            report = analyze_wav(path)
        except (ValueError, OSError):
            return
        assert report["channels"] > 0
        assert report["frames"] > 0
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
