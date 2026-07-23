# 0_m6cmac6e rendition — 13-timing SyncNet run (SUP-52486)

- **Content:** `0_m6cmac6e`
- **File (on disk):** `0_m6cmac6e_0_f4bulitp_1080p.mp4` (1080p, ~24.92 fps) — the rendition
- **Date:** 2026-07-21
- **Tool:** `sync_offset.py` (original flow), defaults `--window 12 --vshift 15`
- **Work dir (kept):** `/tmp/syncoff_ssgnd32f` (ephemeral — /tmp)
- **Sign convention:** `+` = audio leads video; `|offset| ≤ 40 ms` (1 frame) at good conf = in sync; conf `<2` = unreliable.

| at | offset_f | offset_ms | conf | tracks | verdict |
|---|---|---|---|---|---|
| 1:26  | +1  | +40 ms  | 5.72 | 1 | in sync (≤1 frame) |
| 3:36  | -15 | -600 ms | 0.51 | 3 | weak — unreliable |
| 5:45  | +2  | +80 ms  | 2.16 | 1 | audio leads 80 ms (marginal conf) |
| 9:49  | +1  | +40 ms  | 5.76 | 1 | in sync (≤1 frame) |
| 13:45 | +1  | +40 ms  | 4.23 | 2 | in sync (≤1 frame) |
| 18:50 | –   | –       | –    | 0 | no face track |
| 22:47 | +1  | +40 ms  | 7.26 | 1 | in sync (≤1 frame) |
| 2:00  | +1  | +40 ms  | 5.77 | 1 | in sync (≤1 frame) |
| 5:22  | +3  | +120 ms | 4.44 | 1 | audio leads 120 ms |
| 9:20  | –   | –       | –    | 0 | no face track |
| 11:40 | +1  | +40 ms  | 3.86 | 1 | in sync (≤1 frame) |
| 15:45 | +2  | +80 ms  | 4.14 | 4 | audio leads 80 ms |
| 18:30 | –   | –       | –    | 0 | no face track |

**Result:** at the highest-confidence points (conf ≥ 4) this content sits at
**+40 ms = within one frame (in sync)** — 6 such points. Scattered smaller-conf
excursions at +80/+120 ms (5:22, 15:45; 5:45 marginal). 1 weak (3:36), 3 no-face
(18:50, 9:20, 18:30). Not the uniform +80 ms seen on the other content.
