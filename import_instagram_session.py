#!/usr/bin/env python3
"""
Import an Instagram session from your browser (no password).

Prerequisites:
  1. Log in to instagram.com in your browser (complete any checkpoint there).
  2. Close that browser completely (helps cookie access on Linux).
  3. Run this script.

Usage:
  .venv/bin/python import_instagram_session.py --list-profiles
  .venv/bin/python import_instagram_session.py --browser firefox
  .venv/bin/python import_instagram_session.py --auto
  .venv/bin/python import_instagram_session.py -B ~/.config/mozilla/firefox/PROFILE/cookies.sqlite

Then:
  export INSTAGRAM_USERNAME=your_username
  bash sync_instagram.sh --decor-only --decor-max 5
"""

from __future__ import annotations

import argparse
from pathlib import Path

import instaloader

from instagram_common import SESSION_DIR, get_loader

SUPPORTED_BROWSERS = (
    "brave",
    "chrome",
    "chromium",
    "edge",
    "firefox",
    "librewolf",
    "opera",
    "opera_gx",
    "safari",
    "vivaldi",
)

FIREFOX_BASE_DIRS = (
    Path.home() / ".mozilla" / "firefox",
    Path.home() / ".config" / "mozilla" / "firefox",
    Path.home() / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox",
)


def _load_browser_cookie3():
    try:
        import browser_cookie3  # type: ignore
    except ImportError:
        print("  ✗ Missing browser_cookie3 — run: .venv/bin/pip install browser_cookie3")
        raise SystemExit(1) from None
    return browser_cookie3


def discover_cookie_files() -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()

    for base in FIREFOX_BASE_DIRS:
        if not base.is_dir():
            continue
        for profile in sorted(base.iterdir()):
            if not profile.is_dir():
                continue
            cookie = profile / "cookies.sqlite"
            if cookie.is_file():
                resolved = cookie.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    found.append(resolved)

    for pattern in (
        Path.home() / ".config" / "google-chrome" / "Default" / "Cookies",
        Path.home() / ".config" / "google-chrome" / "Profile 1" / "Cookies",
        Path.home() / ".config" / "chromium" / "Default" / "Cookies",
        Path.home() / ".config" / "BraveSoftware" / "Brave-Browser" / "Default" / "Cookies",
    ):
        if pattern.is_file():
            resolved = pattern.resolve()
            if resolved not in seen:
                seen.add(resolved)
                found.append(resolved)

    return found


def pick_firefox_cookie_file(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    profiles = [p for p in discover_cookie_files() if p.name == "cookies.sqlite"]
    if not profiles:
        return None
    for p in profiles:
        if "default-release" in p.parent.name:
            return str(p)
    return str(profiles[0])


def list_profiles() -> None:
    files = discover_cookie_files()
    if not files:
        print("  No browser cookie databases found under common Linux paths.")
        print("  Log in to Instagram in a browser, then run this again.")
        return
    print("  Cookie databases found (use with --cookie-file / -B):\n")
    for path in files:
        print(f"    {path}")
    print("")


def apply_browser_session(L: instaloader.Instaloader, cookies: dict[str, str]) -> str | None:
    """Load cookies into Instaloader and verify login. Returns Instagram username."""
    probe = get_loader()
    probe.context.update_cookies(cookies)
    detected = probe.test_login()
    if not detected:
        return None
    L.load_session(detected, cookies)
    return detected


def instagram_cookies(
    browser: str,
    cookie_file: str | None,
    *,
    quiet: bool = False,
) -> dict[str, str] | None:
    browser_cookie3 = _load_browser_cookie3()
    loaders = {
        "brave": browser_cookie3.brave,
        "chrome": browser_cookie3.chrome,
        "chromium": browser_cookie3.chromium,
        "edge": browser_cookie3.edge,
        "firefox": browser_cookie3.firefox,
        "librewolf": browser_cookie3.librewolf,
        "opera": browser_cookie3.opera,
        "opera_gx": browser_cookie3.opera_gx,
        "safari": browser_cookie3.safari,
        "vivaldi": browser_cookie3.vivaldi,
    }
    if browser not in loaders:
        print(f"  ✗ Unsupported browser: {browser}")
        print(f"    Supported: {', '.join(SUPPORTED_BROWSERS)}")
        raise SystemExit(1)

    if browser in ("firefox", "librewolf") and not cookie_file:
        cookie_file = pick_firefox_cookie_file(None)

    try:
        jar = loaders[browser](cookie_file=cookie_file)
    except browser_cookie3.BrowserCookieError as e:
        print(f"  ✗ Could not read {browser} cookies: {e}")
        print("")
        print("  On this system Firefox is often under ~/.config/mozilla/firefox/")
        print("  Run:  .venv/bin/python import_instagram_session.py --list-profiles")
        print("  Then: .venv/bin/python import_instagram_session.py -B /path/to/cookies.sqlite")
        print("  Or:   .venv/bin/python import_instagram_session.py --auto")
        raise SystemExit(1) from None

    found: dict[str, str] = {}
    for cookie in jar:
        if "instagram.com" in cookie.domain:
            found[cookie.name] = cookie.value

    if not found.get("sessionid"):
        if not quiet:
            print(f"  ✗ No Instagram sessionid in {browser} cookies.")
            if cookie_file:
                print(f"    Cookie file: {cookie_file}")
            print("    • Open https://www.instagram.com and confirm you are logged in.")
            print("    • Complete any security checkpoint in the browser first.")
            print("    • Quit the browser completely, then run this script again.")
            if browser in ("chrome", "chromium", "brave", "edge"):
                print("    • On Linux, Chrome must be fully closed to read its cookie store.")
            print("    • Try another profile: --list-profiles")
        return None

    return found


def try_auto_import(username: str | None) -> None:
    browser_cookie3 = _load_browser_cookie3()
    attempts: list[tuple[str, str | None]] = []

    for cookie_path in discover_cookie_files():
        if cookie_path.name == "cookies.sqlite":
            attempts.append(("firefox", str(cookie_path)))
        elif cookie_path.name == "Cookies":
            attempts.append(("chromium", str(cookie_path)))

    for browser in ("chromium", "chrome", "brave", "firefox"):
        if (browser, None) not in attempts:
            attempts.append((browser, None))

    last_err = ""
    for browser, cookie_file in attempts:
        label = f"{browser}" + (f" ({cookie_file})" if cookie_file else "")
        print(f"  … trying {label}")
        try:
            cookies = instagram_cookies(browser, cookie_file, quiet=True)
        except browser_cookie3.BrowserCookieError as e:
            last_err = str(e)
            continue

        if not cookies:
            continue

        L = get_loader()
        detected = apply_browser_session(L, cookies)
        if not detected:
            continue

        print(f"  ✓ Logged in as @{detected}")
        save_session(L, detected, username)
        return

    print("  ✗ Could not import from any browser profile.")
    if last_err:
        print(f"    Last error: {last_err}")
    print("  Run: .venv/bin/python import_instagram_session.py --list-profiles")
    raise SystemExit(1)


def save_session(L: instaloader.Instaloader, detected: str, username: str | None) -> None:
    username_final = detected.lstrip("@")
    if username and username.lstrip("@") != username_final:
        print(f"  ! Ignoring --username @{username.lstrip('@')}; session belongs to @{username_final}.")

    session_path = SESSION_DIR / f"session-{username_final}"
    L.save_session_to_file(str(session_path))

    print("")
    print(f"  ✓ Saved session → {session_path}")
    print(f"  export INSTAGRAM_USERNAME={username_final}")
    print("  bash sync_instagram.sh --decor-only --decor-max 5")
    print("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Instagram session from browser cookies (no password)")
    parser.add_argument(
        "--browser",
        "-b",
        default="firefox",
        choices=SUPPORTED_BROWSERS,
        help="Browser where you are logged in to Instagram (default: firefox)",
    )
    parser.add_argument(
        "--cookie-file",
        "-B",
        default=None,
        help="Path to cookies.sqlite (Firefox) or Cookies (Chromium)",
    )
    parser.add_argument(
        "--username",
        "-u",
        default=None,
        help="Instagram username (optional; detected from session when possible)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List cookie database paths on this machine",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Try each known browser/profile until one works",
    )
    args = parser.parse_args()

    if args.list_profiles:
        list_profiles()
        return

    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    if args.auto:
        try_auto_import(args.username)
        return

    cookie_file = args.cookie_file
    if args.browser in ("firefox", "librewolf") and not cookie_file:
        cookie_file = pick_firefox_cookie_file(None)
        if cookie_file:
            print(f"  Using Firefox cookies: {cookie_file}")

    cookies = instagram_cookies(args.browser, cookie_file)
    if not cookies:
        raise SystemExit(1)

    L = get_loader()
    detected = apply_browser_session(L, cookies)
    if not detected:
        print("  ✗ Cookies found but Instagram did not accept the session.")
        print("    Refresh instagram.com in your browser, then retry.")
        raise SystemExit(1)

    print(f"  ✓ Logged in as @{detected}")
    save_session(L, detected, args.username)


if __name__ == "__main__":
    main()
