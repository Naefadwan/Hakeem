
#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  BAZEVENT — AI Image Enhancement & Organizer
#  Uses: waifu2x-ncnn-vulkan (AI denoise+upscale) + ImageMagick (color grade)
#
#  Usage: bash process-images.sh <input-folder> <set-name>
#  Example: bash process-images.sh ~/Downloads/new-photos set-02
#
#  Single-image mode (each image = its own set):
#  bash process-images.sh <input-folder> auto
# ═══════════════════════════════════════════════════════════

INPUT_DIR="$1"
SET_ARG="$2"

# ── Validate args ───────────────────────────────────────────
if ! command -v magick >/dev/null 2>&1; then
    echo "  ✗ ImageMagick (magick) is required. See .tools/README.md"
    exit 1
fi

if [ -z "$INPUT_DIR" ] || [ -z "$SET_ARG" ]; then
    echo ""
    echo "  Usage: bash process-images.sh <input-folder> <set-name|auto>"
    echo "  Example: bash process-images.sh ~/Downloads/wedding set-02"
    echo "  Auto:    bash process-images.sh ~/Downloads/mixed auto"
    echo ""
    exit 1
fi

if [ ! -d "$INPUT_DIR" ]; then
    echo "  ✗ Input folder not found: $INPUT_DIR"
    exit 1
fi

# ── Collect images ──────────────────────────────────────────
shopt -s nullglob nocaseglob
FILES=("$INPUT_DIR"/*.jpg "$INPUT_DIR"/*.jpeg "$INPUT_DIR"/*.png "$INPUT_DIR"/*.webp "$INPUT_DIR"/*.heic)

if [ ${#FILES[@]} -eq 0 ]; then
    echo "  ✗ No images found in: $INPUT_DIR"
    exit 1
fi

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   BAZEVENT — AI Image Processor              ║"
echo "  ║   Step 1: waifu2x  → AI denoise + upscale   ║"
echo "  ║   Step 2: magick   → Color grade + resize    ║"
echo "  ╚══════════════════════════════════════════════╝"
echo "  Found ${#FILES[@]} image(s) in: $INPUT_DIR"
echo ""

# ── Temp folder for waifu2x output ─────────────────────────
TMPDIR_AI="/tmp/bazevent_ai_$$"
mkdir -p "$TMPDIR_AI"

# ── Helper: find next available set number ──────────────────
next_set_number() {
    local n=2
    while [ -d "media/decor/set-$(printf '%02d' $n)" ]; do
        n=$((n + 1))
    done
    echo $(printf '%02d' $n)
}

# ── Process function for one image ─────────────────────────
process_one() {
    local FILE="$1"
    local OUT_DIR="$2"
    local OUT_NAME="$3"
    local LABEL="$4"

    local FILENAME=$(basename "$FILE")
    local AI_OUT="$TMPDIR_AI/${OUT_NAME%.jpg}_ai.png"
    local FINAL_OUT="$OUT_DIR/$OUT_NAME"

    echo "  ┌─ $LABEL"
    echo "  │  File : $FILENAME"

    # ── STEP 1: waifu2x AI denoise + 2x upscale ────────────
    echo "  │  [1/2] AI enhancing with waifu2x..."
    waifu2x-ncnn-vulkan \
        -i "$FILE" \
        -o "$AI_OUT" \
        -n 2 \
        -s 2 \
        -f png \
        -g 0 2>/dev/null

    if [ ! -f "$AI_OUT" ]; then
        echo "  │  ⚠ waifu2x failed, using original"
        AI_OUT="$FILE"
    fi

    # ── STEP 2: ImageMagick color grade + resize + export ──
    echo "  │  [2/2] Color grading + compressing..."
    magick "$AI_OUT" \
        -auto-level \
        -modulate 103,118 \
        -sharpen 0x0.5 \
        -unsharp 0x0.8+0.4+0 \
        -resize 1920x1920\> \
        -quality 88 \
        -strip \
        -interlace Plane \
        -colorspace sRGB \
        "$FINAL_OUT"

    if [ $? -eq 0 ]; then
        local ORIG_SIZE=$(du -k "$FILE" | cut -f1)
        local NEW_SIZE=$(du -k "$FINAL_OUT" | cut -f1)
        echo "  │  ✓ Done — ${ORIG_SIZE}KB → ${NEW_SIZE}KB"
    else
        echo "  │  ✗ Color grade failed"
    fi
    echo "  └─────────────────────────────────────────"
    echo ""
}

# ═══════════════════════════════════════════════════════════
#  MODE A: All images → one set
# ═══════════════════════════════════════════════════════════
if [ "$SET_ARG" != "auto" ]; then
    OUTPUT_DIR="media/decor/${SET_ARG}"
    mkdir -p "$OUTPUT_DIR"
    echo "  Mode    : Single set → $OUTPUT_DIR"
    echo ""

    COUNTER=0
    for FILE in "${FILES[@]}"; do
        if [ $COUNTER -eq 0 ]; then
            OUT_NAME="cover.jpg"
        else
            OUT_NAME=$(printf "%02d.jpg" $COUNTER)
        fi
        process_one "$FILE" "$OUTPUT_DIR" "$OUT_NAME" "Image $((COUNTER+1))/${#FILES[@]}"
        COUNTER=$((COUNTER + 1))
    done

    # Print code block to paste
    echo "  ══════════════════════════════════════════"
    echo "  ✓ Add this to decorCollections in index.html:"
    echo ""
    echo "    {"
    echo "        id:X, title:\"Your Title\", category:\"Your Category\","
    echo "        cover:\"${OUTPUT_DIR}/cover.jpg\", tall:true,"
    echo "        description:\"Your description.\","
    echo "        images:["
    for F in "$OUTPUT_DIR"/*.jpg; do
        echo "            \"$F\","
    done
    echo "        ]"
    echo "    },"
    echo ""

# ═══════════════════════════════════════════════════════════
#  MODE B: Each image → its own set (auto mode)
# ═══════════════════════════════════════════════════════════
else
    echo "  Mode    : Auto — each image gets its own set folder"
    echo ""

    CREATED_SETS=()

    for FILE in "${FILES[@]}"; do
        SET_NUM=$(next_set_number)
        OUTPUT_DIR="media/decor/set-${SET_NUM}"
        mkdir -p "$OUTPUT_DIR"
        process_one "$FILE" "$OUTPUT_DIR" "cover.jpg" "→ set-${SET_NUM}"
        CREATED_SETS+=("$OUTPUT_DIR")
    done

    # Print all code blocks
    echo "  ══════════════════════════════════════════"
    echo "  ✓ Add these entries to decorCollections in index.html:"
    echo ""
    SET_ID=2
    for DIR in "${CREATED_SETS[@]}"; do
        echo "    {"
        echo "        id:${SET_ID}, title:\"Set Title Here\", category:\"Events & Decor\","
        echo "        cover:\"${DIR}/cover.jpg\","
        echo "        description:\"Description here.\","
        echo "        images:["
        for F in "$DIR"/*.jpg; do
            echo "            \"$F\","
        done
        echo "        ]"
        echo "    },"
        echo ""
        SET_ID=$((SET_ID + 1))
    done
fi

# ── Cleanup ─────────────────────────────────────────────────
rm -rf "$TMPDIR_AI"
echo "  Done! Clean temp files removed."
echo ""
