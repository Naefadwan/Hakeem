#!/usr/bin/env python3
import json
import glob
import os

def update_dj():
    if not os.path.exists("index.html"):
        print("index.html not found!")
        return

    reels_json_path = "media/dj/reels.json"
    if os.path.exists(reels_json_path):
        with open(reels_json_path, "r", encoding="utf-8") as f:
            dj_shows = json.load(f)
    else:
        dj_shows = []

    # Also check if any local video files exist in media/dj/
    local_videos = sorted(glob.glob("media/dj/*.mp4") + glob.glob("media/dj/*.webm"))
    for idx, vid_path in enumerate(local_videos, start=len(dj_shows) + 1):
        filename = os.path.basename(vid_path)
        # Avoid duplicate if already in dj_shows
        if not any(item.get("videoUrl") == vid_path for item in dj_shows):
            dj_shows.append({
                "id": idx,
                "title": f"Showcase Video - {os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()}",
                "category": "Showcase Video",
                "date": "Recent",
                "type": "video",
                "instagramUrl": "https://www.instagram.com/fatoomdyab.dj",
                "videoUrl": vid_path,
                "image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&q=80",
                "description": "Exclusive video showcase from DJ Fatoom.",
                "details": f"Local showcase video asset ({filename}) playing directly on site with option to visit Instagram.",
                "venue": "Live Show",
                "duration": "Showcase",
                "genre": "DJ Set / Atmospheric",
                "tags": ["Video Showcase", "Live Set", "Featured"]
            })

    js_code = "const djShows = " + json.dumps(dj_shows, indent=4) + ";"

    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    start_token = "const djShows = ["
    start_pos = content.find(start_token)
    if start_pos == -1:
        print("djShows declaration not found in index.html")
        return

    end_token = "// ═══════════════════════════════════════════\n            //  STATE"
    end_pos = content.find(end_token)
    if end_pos == -1:
        # Fallback end search
        end_token = "let currentPage = 'home';"
        end_pos = content.find(end_token)

    if end_pos == -1:
        print("End token after djShows not found in index.html")
        return

    new_content = content[:start_pos] + js_code + "\n\n" + content[end_pos:]

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✓ Successfully updated index.html with {len(dj_shows)} DJ Reels & Showcase videos!")

if __name__ == "__main__":
    update_dj()
