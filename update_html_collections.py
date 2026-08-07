#!/usr/bin/env python3
import json
import glob
import os

def update_html():
    if not os.path.exists("index.html"):
        print("index.html not found!")
        return

    collections = [
        {
            "id": 1,
            "title": "Bazevent Portfolio",
            "category": "Events & Decor",
            "cover": "media/decor/set-01/cover.jpg",
            "tall": True,
            "description": "A curated collection of our finest event decorations and luxury setups — every detail crafted to create memories that last a lifetime.",
            "images": [
                "media/decor/set-01/cover.jpg",
                "media/decor/set-01/01.jpg",
                "media/decor/set-01/02.jpg",
                "media/decor/set-01/03.jpg",
                "media/decor/set-01/04.jpg",
                "media/decor/set-01/05.jpg",
                "media/decor/set-01/06.jpg",
                "media/decor/set-01/07.jpg",
                "media/decor/set-01/08.jpg",
                "media/decor/set-01/09.jpg",
                "media/decor/set-01/10.jpg",
                "media/decor/set-01/11.jpg"
            ]
        }
    ]

    set_dirs = sorted(glob.glob("media/decor/set-*"))
    for sdir in set_dirs:
        set_num = int(sdir.split("-")[-1])
        if set_num == 1:
            continue
        
        imgs = sorted(glob.glob(f"{sdir}/*.jpg"))
        if not imgs:
            continue
        
        cover = f"{sdir}/cover.jpg"
        if not os.path.exists(cover):
            cover = imgs[0]
            
        collections.append({
            "id": set_num,
            "title": f"Event Decor {set_num - 1}",
            "category": "Events & Decor",
            "cover": cover,
            "description": "A luxury decor setup crafted with elegance and attention to detail.",
            "images": imgs
        })

    js_code = "const decorCollections = " + json.dumps(collections, indent=4) + ";"

    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    start_token = "const decorCollections = ["
    start_pos = content.find(start_token)
    if start_pos == -1:
        print("decorCollections not found in index.html")
        return

    end_token = "const djShows = ["
    end_pos = content.find(end_token)
    if end_pos == -1:
        print("djShows not found in index.html")
        return

    new_content = content[:start_pos] + js_code + "\n\n            " + content[end_pos:]

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✓ Successfully updated index.html with {len(collections)} collections!")

if __name__ == "__main__":
    update_html()
