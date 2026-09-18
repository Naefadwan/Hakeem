# Optional AI upscale (process-images.sh)

`process-images.sh` expects **waifu2x-ncnn-vulkan** on your PATH and **ImageMagick** (`magick`).

Real-ESRGAN is optional; the placeholder `realesrgan.zip` in this folder is not a real archive.
If you use Real-ESRGAN, download a Linux build from the [Real-ESRGAN releases](https://github.com/xinntao/Real-ESRGAN/releases) and extract it here, or install waifu2x from your package manager.

Quick install examples (Arch/CachyOS):

```bash
sudo pacman -S imagemagick   # required
# waifu2x-ncnn-vulkan — AUR or build from https://github.com/nihui/waifu2x-ncnn-vulkan
```

Usage:

```bash
bash process-images.sh ~/Downloads/event-photos set-13
bash process-images.sh ~/Downloads/singles auto
python3 update_html_collections.py
```
