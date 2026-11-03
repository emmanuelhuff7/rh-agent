#!/usr/bin/env python3
"""Download all videos found on a given URL.

Uses yt-dlp first, falls back to Playwright browser-based extraction
for sites with custom JS video players.
"""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp


def get_opts(output_dir: str, best_quality: bool = True) -> dict:
    opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "restrictfilenames": True,
        "noplaylist": False,
        "ignoreerrors": True,
        "no_warnings": True,
        "quiet": False,
        "merge_output_format": "mp4",
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
        ],
    }
    if best_quality:
        opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    else:
        opts["format"] = "best[height<=720]/best"
    return opts


def try_ytdlp(url: str, output_dir: str, list_only: bool = False, best_quality: bool = True) -> list:
    """Try yt-dlp first. Returns list of videos found/downloaded, or empty list on failure."""
    try:
        if list_only:
            with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": False, "ignoreerrors": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    return []
                entries = info.get("entries", [info])
                return [e for e in entries if e is not None and e.get("url") or e.get("webpage_url")]
        else:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            opts = get_opts(output_dir, best_quality)
            downloaded = []
            opts["progress_hooks"] = [lambda d: downloaded.append(d.get("filename", "")) if d["status"] == "finished" else None]
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            return downloaded
    except Exception:
        return []


def extract_with_browser(url: str, wait_seconds: int = 10) -> list[dict]:
    """Use Playwright to load the page and capture video stream URLs from network traffic."""
    from playwright.sync_api import sync_playwright

    video_patterns = re.compile(r"\.(m3u8|mpd|mp4|webm|ts)(\?|$)", re.IGNORECASE)
    content_types = {"video/", "application/x-mpegurl", "application/dash+xml", "application/vnd.apple.mpegurl"}

    found = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        def on_response(response):
            req_url = response.url
            ct = response.headers.get("content-type", "")
            if video_patterns.search(req_url) or any(t in ct for t in content_types):
                if req_url not in found:
                    found[req_url] = {
                        "url": req_url,
                        "content_type": ct,
                        "status": response.status,
                    }

        page.on("response", on_response)

        print(f"  Loading page in headless browser...")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Try clicking play buttons
        for selector in ["video", "[class*='play']", "button[aria-label*='play' i]", "[data-testid*='play']", ".video-player", "[class*='video']"]:
            try:
                el = page.query_selector(selector)
                if el and el.is_visible():
                    el.click()
                    time.sleep(1)
            except Exception:
                pass

        # Also try triggering any video elements directly
        page.evaluate("""
            document.querySelectorAll('video').forEach(v => {
                if (v.paused) v.play().catch(() => {});
            });
        """)

        print(f"  Waiting {wait_seconds}s for video streams to load...")
        time.sleep(wait_seconds)

        # Check for video elements with src
        video_srcs = page.evaluate("""
            [...document.querySelectorAll('video, video source, iframe')].map(el => ({
                tag: el.tagName,
                src: el.src || el.getAttribute('src') || '',
                currentSrc: el.currentSrc || '',
                dataSrc: el.getAttribute('data-src') || '',
            })).filter(v => v.src || v.currentSrc || v.dataSrc)
        """)

        for vs in video_srcs:
            for key in ["src", "currentSrc", "dataSrc"]:
                u = vs.get(key, "")
                if u and u.startswith("http") and u not in found:
                    found[u] = {"url": u, "content_type": "from-dom", "status": 200}

        browser.close()

    return list(found.values())


def download_stream(url: str, output_dir: str, index: int) -> str | None:
    """Download a video stream URL using ffmpeg."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    parsed = urlparse(url)
    ext = "mp4"
    if ".m3u8" in parsed.path:
        ext = "mp4"
    elif ".mpd" in parsed.path:
        ext = "mp4"
    elif ".webm" in parsed.path:
        ext = "webm"

    output_path = os.path.join(output_dir, f"video_{index}.{ext}")

    cmd = [
        "ffmpeg", "-y",
        "-headers", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36\r\n",
        "-i", url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        output_path,
    ]

    print(f"  Downloading to {output_path}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  Done: {output_path} ({size_mb:.1f} MB)")
        return output_path
    return None


def pick_best_streams(streams: list[dict]) -> list[dict]:
    """From all captured URLs, pick the best video streams (prefer m3u8 master playlists, then mp4)."""
    m3u8 = [s for s in streams if ".m3u8" in s["url"]]
    mp4 = [s for s in streams if ".mp4" in s["url"] and ".ts" not in s["url"]]
    mpd = [s for s in streams if ".mpd" in s["url"]]

    # Prefer master m3u8 (shorter URLs are usually the master, not chunk playlists)
    if m3u8:
        m3u8.sort(key=lambda s: len(s["url"]))
        seen_bases = set()
        best = []
        for s in m3u8:
            base = urlparse(s["url"]).path.rsplit("/", 1)[0]
            if base not in seen_bases:
                seen_bases.add(base)
                best.append(s)
        return best

    if mp4:
        return mp4

    if mpd:
        return mpd

    return streams


def main():
    parser = argparse.ArgumentParser(description="Download all videos from a URL")
    parser.add_argument("url", help="URL to scrape for videos")
    parser.add_argument("-o", "--output", default="./downloads", help="Output directory (default: ./downloads)")
    parser.add_argument("--list", action="store_true", help="List videos without downloading")
    parser.add_argument("--low", action="store_true", help="Download 720p instead of best quality")
    parser.add_argument("--wait", type=int, default=10, help="Seconds to wait for video streams (default: 10)")
    parser.add_argument("--browser-only", action="store_true", help="Skip yt-dlp, go straight to browser extraction")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output)

    # Step 1: Try yt-dlp
    if not args.browser_only:
        print(f"[1/2] Trying yt-dlp for: {args.url}")
        results = try_ytdlp(args.url, output_dir, list_only=args.list, best_quality=not args.low)
        if results:
            if args.list:
                print(f"\nFound {len(results)} video(s):")
                for i, v in enumerate(results, 1):
                    title = v.get("title", "unknown")
                    dur = f" ({v.get('duration', '?')}s)" if v.get("duration") else ""
                    print(f"  {i}. {title}{dur}")
            else:
                print(f"\nDone — {len(results)} video(s) downloaded to {output_dir}")
            return

        print("  yt-dlp found nothing, falling back to browser.\n")

    # Step 2: Browser-based extraction
    print(f"[2/2] Scanning with headless browser: {args.url}")
    streams = extract_with_browser(args.url, wait_seconds=args.wait)

    if not streams:
        print("\nNo video streams found on this page.")
        return

    print(f"\n  Captured {len(streams)} video-related URL(s):")
    for s in streams:
        print(f"    {s['content_type']:30s} {s['url'][:120]}")

    best = pick_best_streams(streams)
    print(f"\n  Best stream(s) to download: {len(best)}")

    if args.list:
        for i, s in enumerate(best, 1):
            print(f"  {i}. {s['url']}")
        return

    downloaded = []
    for i, s in enumerate(best, 1):
        result = download_stream(s["url"], output_dir, i)
        if result:
            downloaded.append(result)

    if downloaded:
        print(f"\nDone — {len(downloaded)} video(s) saved to {output_dir}")
    else:
        print("\nFailed to download any streams. The URLs captured were:")
        for s in best:
            print(f"  {s['url']}")
        print("\nYou can try manually with: ffmpeg -i <url> -c copy output.mp4")


if __name__ == "__main__":
    main()
