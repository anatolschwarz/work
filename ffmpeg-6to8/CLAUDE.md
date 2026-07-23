# ffmpeg-6to8

FFmpeg **6.0 → 8.1.1** upgrade for the media-encoding pipeline (Kaltura-based, AWS Graviton).

This folder is the project's **continuity layer** — curated docs + status so the work can be
resumed cold. Curated artifacts live **here**; the **real working files live on the remote server**
(reached via MobaXterm SSH) and partly in `Downloads`. Local copies are referenced read-only.

## Status

FFmpeg 8.1.1 built for **both arches** (x86_64 + aarch64 / Graviton 3+4); in the **test/compare
phase**.

- **2026-06-21:** fixes `C1/C3/H1/H3` applied to the report parser `ffm8_report.py` — **not yet
  run/validated**; reports must be regenerated before any FF8 verdict. ⚠️ These edits were made to
  the MobaXterm-mounted copy, which has since rotated out of the local cache — **confirm they were
  saved back to the server.**
- **2026-06-28 (latest local activity):** `build-ffmpeg.sh` re-edited via MobaXterm — newer than
  the project memory. Purpose **to confirm**. (The Jun-28 `magicyuv.c` work belongs to the separate
  `ffmpeg6-cve-fix` project — not this one.)

## The real test harness — on the REMOTE server (source of truth)

Reached via MobaXterm SSH. MobaXterm caches opened files under
`Downloads/MobaXterm/RemoteFiles/<session_id>/`, but **session IDs rotate and old ones vanish** —
do not treat the local cache as complete or stable. Re-open a file in MobaXterm to refresh it.

- `ffm8_report.py` — the report **parser** (the C1/C3/H1/H3 fixes live here)
- `run_test_ffmpeg8.sh`, `test_ffmpeg8.php`, `test_kdl_compare.php` — the test bench
- `build-ffmpeg.sh`, `dependencies8.json` — the build (FF8 wrappers →
  `/web/content/shared/bin/ffmpeg-8.1.1-{arm,x86}-bin/`)
- PHP sources + ff wrappers fetchable from
  `http://ny-www.kaltura.com/content/shared/tmp/qualityTest/TestBench.11/`

_Currently cached locally (Jun 28):_ `RemoteFiles/67944_2_0/build-ffmpeg.sh`,
`67944_2_1/magicyuv.c`, `67944_2_2/magicyuv.c.bak`.

## Curated docs — in this folder

- `docs/ffmpeg_upgrade_research_plan.md`, `docs/ffmpeg-migration-guide.md`
- `docs/ffmpeg_6.0_to_8.1_risk_matrix.md` (the 6→8 matrix), `docs/ffmpeg_4.4_to_6.0_risk_matrix.md`
- `docs/kaltura-ffmpeg-inventory.md`
- `docs/ffmpeg_stats_output.md` — **frozen snapshot** (live original regenerates in Downloads)

LLM-generated; newer versions tend to land in Downloads → **promote the keeper here**, replacing.

## Other files in `Downloads` (do NOT move or overwrite — foundation data)

`C:\Users\anatol.schwartz\Downloads`

- Scripts (ours): `extract_ffmpeg_stats.py`, `KDLOperatorFfmpeg0_10.php`, `test_ffmpeg7.dev.php`
  — relationship to the remote harness **to confirm** (earlier/local analysis layer?)
- Data (read-only): `report_ff6.csv` (+`.orig`), `ffmpeg_stats_output.md` (live),
  `BuildNotes.ffmpeg-7.0 - setA_ff6_ff7.csv`
- Reference binaries: `ffmpeg-6.0-…amd64.tar.gz`, `ffmpeg-4.4-…amd64.tar.gz`, `ffmpeg-7.1-essentials_build.7z`
- MagicYUV test asset: `magicyuv_yuv422p.avi` (ties to the Jun-28 `magicyuv.c` work)
- Lipsync media (parked, separate thread): `1_v9fjnlso_lipsync_596-608.mp4`,
  `1_v9fjnlso_1_qn2iwn07_src.mp4`, `1_v9fjnlso_1_9l1ayldb_540p.mp4`

## Open threads

- [ ] **Did the Jun-21 `ffm8_report.py` fixes get saved to the server?** (local Moba copy rotated out)
- [ ] Run/validate the parser — regenerate reports before any FF8 verdict.
- [ ] Confirm the loose `Downloads` scripts/csv vs the remote harness — same project layer or not.
- [ ] (Later) the lipsync media.

## How to resume

1. Reconnect MobaXterm to the remote; re-open the harness files to refresh the local cache.
2. Read `docs/` (research plan + 6→8 risk matrix) for intent; check the parser bug list in the
   `project_ffmpeg8-build` memory.
3. Verify the parser fixes are present server-side, then run + regenerate reports.
4. Update "Status" here and the `project_ffmpeg8-build` memory before stopping.

## Notes / chat log

<!-- Drop exported chats, decisions, and running notes below. -->
