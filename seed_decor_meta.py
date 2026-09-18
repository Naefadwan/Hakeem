#!/usr/bin/env python3
"""Write .meta.json titles for decor sets that don't have one yet."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DECOR = ROOT / "media" / "decor"

PRESET: dict[int, tuple[str, str]] = {
    2: ("Garden Wedding Reception", "Soft florals and elegant tablescapes for an outdoor celebration."),
    3: ("Classic White & Gold Theme", "Timeless white and gold decor with refined centerpiece styling."),
    4: ("Modern Minimal Setup", "Clean lines, ambient lighting, and understated luxury details."),
    5: ("Intimate Dinner Styling", "Warm candlelight and layered textures for a private dinner event."),
    6: ("Grand Entrance Decor", "Statement entrance piece designed to welcome guests in style."),
    7: ("Celebration Backdrop", "Photo-ready backdrop and coordinated accent pieces."),
    8: ("Full Venue Transformation", "Multi-zone decor — entrance, seating, and focal display."),
    9: ("Seasonal Table Design", "Curated table settings with seasonal florals and linens."),
    10: ("Corporate Gala Styling", "Polished decor for corporate celebrations and awards nights."),
    11: ("Birthday Feature Display", "Bold feature elements tailored to the guest of honor."),
    12: ("Evening Lounge Ambience", "Mood lighting and lounge styling for late-evening entertaining."),
}


def main() -> None:
    written = 0
    for set_dir in sorted(DECOR.glob("set-*")):
        suffix = set_dir.name.split("-")[-1]
        if not suffix.isdigit():
            continue
        num = int(suffix)
        if num == 1:
            continue
        meta_path = set_dir / ".meta.json"
        if meta_path.is_file():
            continue
        if num in PRESET:
            title, desc = PRESET[num]
        else:
            title = f"BAZEEVENT Showcase {num}"
            desc = "Custom event decor by BAZEEVENT — design, setup, and styling."
        meta_path.write_text(
            json.dumps({"title": title, "description": desc}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written += 1
        print(f"  ✓ {set_dir.name}: {title}")

    print(f"\n✓ Wrote {written} meta file(s)")


if __name__ == "__main__":
    main()
