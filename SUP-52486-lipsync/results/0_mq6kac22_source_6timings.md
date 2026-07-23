# 0_mq6kac22 source — 6-timing SyncNet run (SUP-52486)

- **Content:** `0_mq6kac22`
- **File (on disk):** `0_mq6kac22_source.m4v` (2160p, 60 fps) — the source
- **Date:** 2026-07-21
- **Tool:** `sync_offset.py` (original flow), defaults `--window 12 --vshift 15`
- **Work dir (kept):** `/tmp/syncoff_cq6h2xxp` (ephemeral — /tmp)
- **Sign convention:** `+` = audio leads video; `|offset| ≤ 40 ms` (1 frame) at good conf = in sync; conf `<2` = unreliable.

| at | offset_f | offset_ms | conf | tracks | verdict |
|---|---|---|---|---|---|
| 2:00  | +2 | +80 ms  | 7.50 | 1 | audio leads 80 ms |
| 5:22  | +2 | +80 ms  | 7.89 | 1 | audio leads 80 ms |
| 9:20  | +2 | +80 ms  | 5.12 | 1 | audio leads 80 ms |
| 11:40 | +2 | +80 ms  | 5.41 | 1 | audio leads 80 ms |
| 15:45 | +2 | +80 ms  | 5.04 | 1 | audio leads 80 ms |
| 18:30 | +3 | +120 ms | 7.47 | 2 | audio leads 120 ms |

**Result:** 6/6 locked, all confident. 5 at **+80 ms (audio leads)**, 1 at **+120 ms** (18:30) — within one frame of the rest.
