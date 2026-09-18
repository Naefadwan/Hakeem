#!/usr/bin/env python3
"""Import media/decor/new-set/* into media/decor/set-XX/ (non-destructive)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEW_SET = ROOT / "media" / "decor" / "new-set"
DECOR = ROOT / "media" / "decor"
SKIP = {"redbackground.jpeg", ".meta.json"}

TITLES = [
    "Floral Entrance Arch",
    "Reception Table Styling",
    "Stage & Backdrop Design",
    "Balloon & Theme Install",
    "Candlelit Centerpieces",
    "Outdoor Celebration Setup",
    "Luxury Lounge Corner",
    "Birthday Feature Wall",
    "Gold & White Palette",
    "Evening Ambient Lighting",
]


def next_set_number() -> int:
    nums = []
    for path in DECOR.glob("set-*"):
        suffix = path.name.split("-")[-1]
        if suffix.isdigit():
            nums.append(int(suffix))
    return max(nums, default=0) + 1


def to_cover_jpg(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in (".jpg", ".jpeg"):
        result = subprocess.run(
            ["magick", str(src), "-strip", "-quality", "88", str(dest)],
            capture_output=True,
        )
        if result.returncode != 0:
            shutil.copy2(src, dest)
    else:
        subprocess.run(["magick", str(src), "-strip", "-quality", "88", str(dest)], check=True)


def main() -> None:
    if not NEW_SET.is_dir():
        print("  ✗ media/decor/new-set/ not found")
        raise SystemExit(1)

    sources = sorted(
        p
        for p in NEW_SET.iterdir()
        if p.is_file() and p.name not in SKIP and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    )
    if not sources:
        print("  ✗ No images to import in new-set/")
        raise SystemExit(1)

    created = 0
    for idx, src in enumerate(sources):
        set_num = next_set_number()
        set_dir = DECOR / f"set-{set_num:02d}"
        if set_dir.exists():
            print(f"  ! Skip {src.name} — {set_dir.name} exists")
            continue
        title = TITLES[idx % len(TITLES)]
        if idx < len(TITLES):
            title = TITLES[idx]
        to_cover_jpg(src, set_dir / "cover.jpg")
        meta = {
            "title": title,
            "description": f"{title} — custom event styling by BAZEEVENT. Follow @bazevents20 for more.",
        }
        (set_dir / ".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  ✓ {src.name} → {set_dir.name} ({title})")
        created += 1

    print(f"\n✓ Imported {created} set(s). Run: .venv/bin/python update_html_collections.py")


if __name__ == "__main__":
    main()
