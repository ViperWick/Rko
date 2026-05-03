# -*- coding: utf-8 -*-
"""將專案內 bat/ps1 的 miniconda3 路徑改為 anaconda3。關閉 Cursor 內開著的 .bat 後再執行。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD, NEW = "miniconda3", "anaconda3"


def main() -> int:
    changed = []
    for pattern in ("*.bat", "*.ps1"):
        for p in ROOT.rglob(pattern):
            if "node_modules" in p.parts or ".git" in p.parts:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                print("skip (read):", p, e, file=sys.stderr)
                continue
            if OLD not in text:
                continue
            new_text = text.replace(OLD, NEW)
            try:
                p.write_text(new_text, encoding="utf-8")
            except OSError as e:
                print("skip (write):", p, e, file=sys.stderr)
                continue
            changed.append(p)
    for p in changed:
        print("updated:", p)
    print(f"Done. {len(changed)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
