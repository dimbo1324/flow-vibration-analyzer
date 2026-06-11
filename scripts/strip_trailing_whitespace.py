#!/usr/bin/env python
"""Remove trailing spaces and tabs while preserving file encoding and line endings."""

from __future__ import annotations

import re
import sys
from pathlib import Path

TRAILING_WHITESPACE = re.compile(rb"[ \t]+(?=\r?\n)")


def clean_file(path: Path) -> bool:
    """Clean one file and return whether it changed."""
    original = path.read_bytes()

    def replacement(match: re.Match[bytes]) -> bytes:
        whitespace = match.group(0)
        if path.suffix.lower() == ".md" and b"\t" not in whitespace and len(whitespace) >= 2:
            return b"  "
        return b""

    cleaned = TRAILING_WHITESPACE.sub(replacement, original)
    if cleaned == original:
        return False
    path.write_bytes(cleaned)
    return True


def main(paths: list[str]) -> int:
    changed = False
    for raw_path in paths:
        changed = clean_file(Path(raw_path)) or changed
    return int(changed)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
