#!/usr/bin/env python3
"""Shared Instaloader setup for BAZEEVENT Instagram sync scripts."""

from __future__ import annotations

import os
import time
from pathlib import Path

import instaloader

ROOT = Path(__file__).resolve().parent
SESSION_DIR = ROOT / ".instagram"


def project_root() -> Path:
    return ROOT


def session_file_path() -> Path | None:
    username = os.environ.get("INSTAGRAM_USERNAME", "").strip()
    if not username:
        return None
    path = SESSION_DIR / f"session-{username}"
    return path if path.is_file() else None


def has_saved_session() -> bool:
    return session_file_path() is not None


def get_loader(*, download_pictures: bool = False, download_videos: bool = False) -> instaloader.Instaloader:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    max_attempts = int(os.environ.get("INSTAGRAM_MAX_RETRIES", "3"))
    return instaloader.Instaloader(
        quiet=False,
        dirname_pattern=str(SESSION_DIR / "downloads"),
        download_pictures=download_pictures,
        download_videos=download_videos,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern="",
        max_connection_attempts=max_attempts,
        request_timeout=60,
        iphone_support=True,
    )


def load_session(L: instaloader.Instaloader) -> bool:
    """Load saved session if INSTAGRAM_USERNAME is set and session file exists."""
    username = os.environ.get("INSTAGRAM_USERNAME", "").strip()
    if not username:
        return False
    session_file = SESSION_DIR / f"session-{username}"
    if not session_file.is_file():
        print(f"  ! No session file: {session_file}")
        print("    Import from browser:  bash import_instagram_session.sh firefox")
        print("    Or password login:    .venv/bin/instaloader --login YOUR_IG_USER --filename .instagram/session")
        return False
    L.load_session_from_file(username, str(session_file))
    print(f"  ✓ Loaded Instagram session for @{username}")
    return True


def ensure_session_or_exit(*, allow_anonymous: bool) -> None:
    if has_saved_session():
        return
    print("")
    print("  ✗ No Instagram login session found.")
    print("    Anonymous requests often get 429 Too Many Requests (rate limit).")
    print("")
    print("    1. export INSTAGRAM_USERNAME=your_ig_login")
    print("    2. bash import_instagram_session.sh firefox   # no password (logged-in browser)")
    print("       — or — instaloader --login … if you prefer password")
    print("    3. Wait ~15 minutes if you were just rate-limited, then retry.")
    print("")
    if not allow_anonymous:
        raise SystemExit(1)
    print("  ! Continuing without session (--allow-anonymous). Rate limits are likely.")
    print("")


def rate_limit_help() -> None:
    print("")
    print("  ✗ Instagram rate limit (HTTP 429).")
    print("    • Stop the script (Ctrl+C if it is still retrying).")
    print("    • Do not run decor + DJ back-to-back; use sync_instagram.sh --decor-only, wait, then --dj-only.")
    print("    • Close the Instagram app while syncing.")
    print("    • Use a saved login session (see ensure_session_or_exit message above).")
    print("    • Wait 15–60 minutes before trying again.")
    print("    • Retry with gentler settings:")
    print("        INSTAGRAM_WARMUP_SEC=30 INSTAGRAM_MAX_RETRIES=5 bash sync_instagram.sh --decor-only --decor-max 3")
    print("")


def profile_from_username(L: instaloader.Instaloader, username: str) -> instaloader.Profile:
    username = username.lstrip("@")
    warmup = float(os.environ.get("INSTAGRAM_WARMUP_SEC", "8"))
    if warmup > 0:
        print(f"  ⏸ Waiting {warmup:.0f}s before Instagram API requests…")
        time.sleep(warmup)

    attempts = int(os.environ.get("INSTAGRAM_PROFILE_RETRIES", "3"))
    last_err: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return instaloader.Profile.from_username(L.context, username)
        except instaloader.exceptions.AbortDownloadException as err:
            last_err = err
            if "429" not in str(err) or attempt == attempts:
                raise
            wait = 45 * attempt
            print(f"  ! Rate limited (429), retry {attempt}/{attempts} in {wait}s…")
            time.sleep(wait)
        except instaloader.exceptions.ConnectionException as err:
            last_err = err
            if "429" not in str(err) or attempt == attempts:
                raise
            wait = 45 * attempt
            print(f"  ! Rate limited (429), retry {attempt}/{attempts} in {wait}s…")
            time.sleep(wait)
    assert last_err is not None
    raise last_err


def polite_sleep(seconds: float = 1.5) -> None:
    time.sleep(seconds)


def title_from_caption(caption: str | None, fallback: str) -> str:
    if not caption:
        return fallback
    line = caption.strip().splitlines()[0].strip()
    if len(line) > 80:
        line = line[:77] + "..."
    return line or fallback
