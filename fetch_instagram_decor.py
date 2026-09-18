#!/usr/bin/env python3
"""
Fetch photos from @bazevents20 into media/decor/set-XX/ folders.

Usage (from project root):
  .venv/bin/python fetch_instagram_decor.py
  .venv/bin/python fetch_instagram_decor.py --max-posts 10

Instagram often requires a logged-in session:
  export INSTAGRAM_USERNAME=your_ig_login
  .venv/bin/instaloader --login "$INSTAGRAM_USERNAME" --filename .instagram/session

Then run update_html_collections.py (or sync_instagram.sh).
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

import instaloader

from instagram_common import (
    ensure_session_or_exit,
    get_loader,
    load_session,
    polite_sleep,
    profile_from_username,
    project_root,
    rate_limit_help,
    title_from_caption,
)

DEFAULT_USER = "bazevents20"
DECOR_ROOT = project_root() / "media" / "decor"
MANIFEST_PATH = DECOR_ROOT / ".instagram-bazevents-manifest.json"
PROFILE_URL = "https://www.instagram.com/bazevents20"


def load_manifest() -> dict:
    if MANIFEST_PATH.is_file():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"username": DEFAULT_USER, "posts": {}}


def save_manifest(data: dict) -> None:
    DECOR_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def next_set_number() -> int:
    nums = []
    for path in DECOR_ROOT.glob("set-*"):
        suffix = path.name.split("-")[-1]
        if suffix.isdigit():
            nums.append(int(suffix))
    return max(nums, default=0) + 1


def download_file(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            dest.write_bytes(resp.read())
        return dest.is_file() and dest.stat().st_size > 0
    except OSError as e:
        print(f"    ✗ Download failed: {dest.name} ({e})")
        return False


def image_urls_for_post(post: instaloader.Post) -> list[str]:
    if post.typename == "GraphSidecar":
        return [node.display_url for node in post.get_sidecar_nodes() if node.is_video is False]
    if post.is_video:
        return [post.url] if post.url else []
    return [post.url] if post.url else []


def write_set(
    set_dir: Path,
    image_urls: list[str],
    title: str,
    caption: str,
) -> list[str]:
    set_dir.mkdir(parents=True, exist_ok=True)
    meta = {"title": title, "description": caption.strip() or title}
    (set_dir / ".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    saved: list[str] = []
    for i, url in enumerate(image_urls):
        name = "cover.jpg" if i == 0 else f"{i:02d}.jpg"
        dest = set_dir / name
        if dest.is_file():
            saved.append(str(dest.relative_to(project_root())).replace("\\", "/"))
            continue
        print(f"    ↓ {set_dir.name}/{name}")
        if download_file(url, dest):
            saved.append(str(dest.relative_to(project_root())).replace("\\", "/"))
            polite_sleep(0.8)
    return saved


def fetch(username: str, max_posts: int, skip_existing: bool) -> int:
    L = get_loader()
    load_session(L)
    profile = profile_from_username(L, username)
    print(f"  Profile @{profile.username} — {profile.mediacount} posts")

    manifest = load_manifest()
    posts_map: dict = manifest.setdefault("posts", {})
    created = 0

    for post in profile.get_posts():
        shortcode = post.shortcode
        if skip_existing and shortcode in posts_map:
            continue

        urls = image_urls_for_post(post)
        if not urls:
            continue

        caption = post.caption or ""
        title = title_from_caption(caption, f"Event Decor — {post.date_utc.strftime('%b %Y')}")
        title = re.sub(r"\s+", " ", title)

        if shortcode in posts_map and posts_map[shortcode].get("set_dir"):
            set_name = posts_map[shortcode]["set_dir"]
        else:
            set_num = next_set_number()
            set_name = f"set-{set_num:02d}"
            created += 1

        set_dir = DECOR_ROOT / set_name
        print(f"  + {post.date_utc.date()} {shortcode} → {set_name} ({len(urls)} image(s))")
        saved = write_set(set_dir, urls, title, caption)
        if not saved:
            continue

        posts_map[shortcode] = {
            "set_dir": set_name,
            "title": title,
            "date": post.date_utc.isoformat(),
            "permalink": f"https://www.instagram.com/p/{shortcode}/",
            "images": len(saved),
        }
        polite_sleep()

        if created >= max_posts:
            break

    manifest["username"] = username
    save_manifest(manifest)
    print(f"\n✓ Decor sync done ({created} new set folder(s) this run)")
    print(f"  Next: .venv/bin/python update_html_collections.py")
    print(f"  BAZEVENT Instagram: {PROFILE_URL}")
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync decor photos from Instagram into media/decor/set-*")
    parser.add_argument("--username", default=DEFAULT_USER, help=f"Instagram handle (default: {DEFAULT_USER})")
    parser.add_argument("--max-posts", type=int, default=15, help="Max new Instagram posts to import per run")
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-process posts already listed in the manifest",
    )
    parser.add_argument(
        "--allow-anonymous",
        action="store_true",
        help="Allow running without a saved login session (often hits 429)",
    )
    args = parser.parse_args()

    ensure_session_or_exit(allow_anonymous=args.allow_anonymous)

    try:
        fetch(args.username, args.max_posts, skip_existing=not args.no_skip_existing)
    except (instaloader.exceptions.ConnectionException, instaloader.exceptions.AbortDownloadException) as e:
        if "429" in str(e):
            rate_limit_help()
        raise SystemExit(1) from None
    except instaloader.exceptions.LoginRequiredException:
        print("\n✗ Instagram requires login for this profile.")
        print("  export INSTAGRAM_USERNAME=your_ig_login")
        print("  .venv/bin/instaloader --login \"$INSTAGRAM_USERNAME\" --filename .instagram/session")
        raise SystemExit(1) from None
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"\n✗ Profile not found: @{args.username.lstrip('@')}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
