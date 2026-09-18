#!/usr/bin/env python3
"""
Fetch video posts / reels from @fatoomdyab.dj → media/dj/reels.json

Usage (from project root):
  .venv/bin/python fetch_instagram_dj.py
  .venv/bin/python fetch_instagram_dj.py --max-posts 15 --download-videos

Instagram often requires a logged-in session:
  export INSTAGRAM_USERNAME=your_ig_login
  .venv/bin/instaloader --login "$INSTAGRAM_USERNAME" --filename .instagram/session

Then run update_dj_content.py (or sync_instagram.sh).
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

DEFAULT_USER = "fatoomdyab.dj"
REELS_PATH = project_root() / "media" / "dj" / "reels.json"
MEDIA_DIR = project_root() / "media" / "dj"
MANIFEST_PATH = MEDIA_DIR / ".instagram-dj-manifest.json"
PROFILE_URL = "https://www.instagram.com/fatoomdyab.dj"


def load_manifest() -> dict:
    if MANIFEST_PATH.is_file():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"username": DEFAULT_USER, "shortcodes": []}


def save_manifest(data: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def download_file(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            dest.write_bytes(resp.read())
        return True
    except OSError as e:
        print(f"    ✗ Download failed: {dest.name} ({e})")
        return False


def post_permalink(shortcode: str, is_reel: bool) -> str:
    kind = "reel" if is_reel else "p"
    return f"https://www.instagram.com/{kind}/{shortcode}/"


def build_show_entry(
    post: instaloader.Post,
    idx: int,
    *,
    download_videos: bool,
    media_dir: Path,
) -> dict:
    shortcode = post.shortcode
    caption = post.caption or ""
    is_reel = post.typename == "GraphVideo" or (post.is_video and "reel" in (post.url or "").lower())
    title = title_from_caption(caption, f"DJ Set — {post.date_utc.strftime('%b %Y')}")
    date_str = post.date_utc.strftime("%b %Y")

    thumb_path = media_dir / f"{shortcode}.jpg"
    image_ref = post.url
    if not thumb_path.is_file() and post.url:
        if download_file(post.url, thumb_path):
            image_ref = f"media/dj/{shortcode}.jpg"
            polite_sleep(0.8)

    video_ref = None
    if download_videos and post.is_video and post.video_url:
        video_path = media_dir / f"{shortcode}.mp4"
        if not video_path.is_file():
            print(f"    ↓ video {shortcode}.mp4")
            if download_file(post.video_url, video_path):
                video_ref = f"media/dj/{shortcode}.mp4"
                polite_sleep(1.2)
        else:
            video_ref = f"media/dj/{shortcode}.mp4"

    tags = ["Instagram Reel", "Live Set"] if is_reel else ["Video Showcase", "Live Set"]
    if caption:
        hashtags = re.findall(r"#(\w+)", caption)[:5]
        tags.extend(hashtags)

    entry: dict = {
        "id": idx,
        "title": title,
        "category": "Instagram Reel" if is_reel else "Showcase Video",
        "date": date_str,
        "type": "reel" if is_reel else "video",
        "instagramUrl": post_permalink(shortcode, is_reel),
        "reelId": shortcode,
        "image": image_ref,
        "description": (caption.splitlines()[0][:200] if caption else title),
        "details": caption.strip() if caption else title,
        "venue": "Live Event",
        "duration": "Reel" if is_reel else "Showcase",
        "genre": "DJ Set",
        "tags": tags[:8],
    }
    if video_ref:
        entry["videoUrl"] = video_ref
    return entry


def fetch(username: str, max_posts: int, download_videos: bool, replace: bool) -> int:
    L = get_loader()
    load_session(L)
    profile = profile_from_username(L, username)
    print(f"  Profile @{profile.username} — {profile.mediacount} posts")

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    seen = set(manifest.get("shortcodes", []))

    shows: list[dict] = []
    if not replace and REELS_PATH.is_file():
        shows = json.loads(REELS_PATH.read_text(encoding="utf-8"))
        seen.update(item.get("reelId") for item in shows if item.get("reelId"))

    new_count = 0
    for post in profile.get_posts():
        if not post.is_video:
            continue
        if not replace and post.shortcode in seen:
            continue

        print(f"  + {post.date_utc.date()} {post.shortcode}")
        entry = build_show_entry(
            post,
            len(shows) + 1,
            download_videos=download_videos,
            media_dir=MEDIA_DIR,
        )
        shows.append(entry)
        seen.add(post.shortcode)
        new_count += 1
        polite_sleep()

        if (replace and len(shows) >= max_posts) or (not replace and new_count >= max_posts):
            break

    for i, show in enumerate(shows, start=1):
        show["id"] = i

    REELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REELS_PATH.write_text(json.dumps(shows, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest["username"] = username
    manifest["shortcodes"] = list(seen)
    save_manifest(manifest)

    print(f"\n✓ Wrote {len(shows)} items → {REELS_PATH.relative_to(project_root())} ({new_count} fetched this run)")
    print(f"  Next: .venv/bin/python update_dj_content.py")
    print(f"  DJ Instagram: {PROFILE_URL}")
    return len(shows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync DJ reels from Instagram into reels.json")
    parser.add_argument("--username", default=DEFAULT_USER, help=f"Instagram handle (default: {DEFAULT_USER})")
    parser.add_argument("--max-posts", type=int, default=20, help="Max video posts to include")
    parser.add_argument(
        "--download-videos",
        action="store_true",
        help="Download MP4s to media/dj/ for on-site playback (slower; needs session)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace reels.json with latest feed (default: append only new shortcodes)",
    )
    parser.add_argument(
        "--allow-anonymous",
        action="store_true",
        help="Allow running without a saved login session (often hits 429)",
    )
    args = parser.parse_args()

    ensure_session_or_exit(allow_anonymous=args.allow_anonymous)

    try:
        fetch(args.username, args.max_posts, args.download_videos, args.replace)
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
