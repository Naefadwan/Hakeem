# DJ showcase data

Edit `reels.json`, then run from project root:

```bash
python3 update_dj_content.py
```

Or sync from Instagram when rate limits allow:

```bash
bash sync_instagram.sh --dj-only --dj-max 10 --dj-replace
```

Each item supports `reelId` (Instagram embed) and optional local `videoUrl` under `media/dj/`.
