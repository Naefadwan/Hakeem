#!/usr/bin/env python3
import os
import sys
import glob
import subprocess
import numpy as np
from PIL import Image

def get_ranges(indices, max_val):
    if len(indices) == 0:
        return [(0, max_val)]
    cuts = []
    start = indices[0]
    prev = indices[0]
    for idx in indices[1:]:
        if idx > prev + 1:
            cuts.append((start, prev))
            start = idx
        prev = idx
    cuts.append((start, prev))
    
    segs = []
    curr = 0
    for c_start, c_end in cuts:
        if c_start > curr + 15: # min 15px
            segs.append((curr, c_start))
        curr = c_end + 1
    if curr < max_val - 15:
        segs.append((curr, max_val))
    return segs

def process():
    input_dir = "media/decor/new-set"
    files = sorted(glob.glob(f"{input_dir}/*"))
    if not files:
        print("No files found!")
        return

    # Clean out set-02 through set-99
    for set_dir in glob.glob("media/decor/set-*"):
        if set_dir != "media/decor/set-01":
            subprocess.run(["rm", "-rf", set_dir])

    set_counter = 2
    decor_collections = []

    tmp_dir = "/tmp/bazevent_proc"
    os.makedirs(tmp_dir, exist_ok=True)

    for p in files:
        fname = os.path.basename(p)
        print(f"\nProcessing source file: {fname}")

        im = Image.open(p).convert("RGB")
        arr = np.array(im)
        h, w, _ = arr.shape

        v_means = arr.mean(axis=(0,2))
        v_cuts = np.where(v_means > 240)[0]
        
        h_means = arr.mean(axis=(1,2))
        h_cuts = np.where(h_means > 240)[0]

        col_segs = get_ranges(v_cuts, w)
        row_segs = get_ranges(h_cuts, h)

        crops = []
        for r_start, r_end in row_segs:
            for c_start, c_end in col_segs:
                crop = im.crop((c_start, r_start, c_end, r_end))
                crops.append(crop)

        set_dir_name = f"set-{set_counter:02d}"
        set_dir_path = f"media/decor/{set_dir_name}"
        os.makedirs(set_dir_path, exist_ok=True)

        set_images = []
        for i, crop in enumerate(crops):
            out_filename = "cover.jpg" if i == 0 else f"{i:02d}.jpg"
            final_path = f"{set_dir_path}/{out_filename}"
            set_images.append(final_path)

            crop_tmp = f"{tmp_dir}/crop_raw_{i}.png"
            crop_ai = f"{tmp_dir}/crop_ai_{i}.png"
            crop.save(crop_tmp)

            # AI upscale with waifu2x
            print(f"  → Sub-photo {i+1}/{len(crops)}: AI upscaling with waifu2x...")
            cmd_ai = [
                "waifu2x-ncnn-vulkan",
                "-i", crop_tmp,
                "-o", crop_ai,
                "-n", "2",
                "-s", "2",
                "-f", "png",
                "-g", "0"
            ]
            res = subprocess.run(cmd_ai, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            source_for_magick = crop_ai if (res.returncode == 0 and os.path.exists(crop_ai)) else crop_tmp

            # Color grade with ImageMagick
            print(f"  → Sub-photo {i+1}/{len(crops)}: Color grading & exporting...")
            cmd_magick = [
                "magick", source_for_magick,
                "-auto-level",
                "-modulate", "103,118",
                "-sharpen", "0x0.5",
                "-unsharp", "0x0.8+0.4+0",
                "-resize", "1920x1920>",
                "-quality", "88",
                "-strip",
                "-interlace", "Plane",
                "-colorspace", "sRGB",
                final_path
            ]
            subprocess.run(cmd_magick)
            print(f"     Saved: {final_path} ({os.path.getsize(final_path)//1024} KB)")

        decor_collections.append({
            "id": set_counter,
            "title": "Event Decor",
            "category": "Events & Decor",
            "cover": f"{set_dir_path}/cover.jpg",
            "description": "A luxury decor setup crafted with elegance and attention to detail.",
            "images": set_images
        })

        set_counter += 1

    subprocess.run(["rm", "-rf", tmp_dir])
    print(f"\n✓ Created {len(decor_collections)} sets with total clean photos processed!")
    return decor_collections

if __name__ == "__main__":
    process()
