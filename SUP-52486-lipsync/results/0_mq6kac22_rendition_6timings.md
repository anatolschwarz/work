# 0_mq6kac22 rendition — 6-timing SyncNet run (SUP-52486)

- **Content:** `0_mq6kac22`
- **File (on disk):** `0_mq6kac22_1080p.mp4` (1080p H.264, 30 fps) — the rendition
- **Date:** 2026-07-21
- **Tool:** `sync_offset.py` (original flow), defaults `--window 12 --vshift 15`
- **Work dir (kept):** `/tmp/syncoff_316pw34i` (ephemeral — /tmp)
- **Sign convention:** `+` = audio leads video; `|offset| ≤ 40 ms` (1 frame) at good conf = in sync; conf `<2` = unreliable.

| at | offset_f | offset_ms | conf | tracks | verdict |
|---|---|---|---|---|---|
| 2:00  | +2 | +80 ms | 7.60 | 1 | audio leads 80 ms |
| 5:22  | +2 | +80 ms | 7.58 | 1 | audio leads 80 ms |
| 9:20  | +2 | +80 ms | 5.26 | 1 | audio leads 80 ms |
| 11:40 | +2 | +80 ms | 5.07 | 1 | audio leads 80 ms |
| 15:45 | +2 | +80 ms | 4.81 | 1 | audio leads 80 ms |
| 18:30 | –  | –      | –    | 0 | no face track |

**Result:** 5/6 lock at **+80 ms (audio leads)**; 18:30 no detectable face.
