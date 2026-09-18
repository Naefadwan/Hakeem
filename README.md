# BAZEEVENT × DJ Fatoom

Single-page portfolio site for **BAZEEVENT** (events & decor) and **DJ Fatoom**.

## View locally

```bash
cd /path/to/Hakeem
python3 -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080).

## Finish / refresh site content (no Instagram)

```bash
bash finish_project.sh
```

This imports `media/decor/new-set/` into new `set-XX` folders, writes decor titles, and updates `index.html`.

## Decor workflow

| Step | Command |
|------|---------|
| Import WhatsApp / loose photos | `python3 import_new_set.py` |
| AI upscale (optional) | `bash process-images.sh ~/photos set-13` — see [.tools/README.md](.tools/README.md) |
| Regenerate gallery in HTML | `python3 update_html_collections.py` |

Collage splitter (destructive): `python3 process_collages.py --replace-sets` only if you mean to wipe sets 2+.

## DJ workflow

1. Edit `media/dj/reels.json` (or sync from Instagram).
2. Run `python3 update_dj_content.py`.

Instagram sync (when not rate-limited):

```bash
bash import_instagram_session.sh auto
export INSTAGRAM_USERNAME=your_ig_user
bash sync_instagram.sh
```

## Deploy (GitHub Pages)

1. Push this repo to GitHub (`main` branch).
2. **Settings → Pages → Build and deployment → GitHub Actions**.
3. Push to `main`; workflow [.github/workflows/pages.yml](.github/workflows/pages.yml) publishes the site.

## Links

- Decor: [@bazevents20](https://www.instagram.com/bazevents20)
- DJ: [@fatoomdyab.dj](https://www.instagram.com/fatoomdyab.dj)

## Python tools

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
