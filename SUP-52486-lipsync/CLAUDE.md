# SUP-52486 — Lipsync investigation

Support case: customer reports lip-sync issues on **Kaltura web players** (VOD).

## Scope (IMPORTANT)
- **IN scope:** measuring the **baked-in A/V sync of the asset/file itself** — producing a hard, quotable in-file offset number.
- **OUT of scope (do not raise):** playback-side causes — network/ABR/stall, client device/dropped-frame. The user explicitly excluded these. Ignore entirely.

## Goal
Measure the asset's baked-in audio/video sync and report a defensible offset figure (e.g. "within ±X ms → file not at fault").

## State (updated 2026-07-23)
- **Tool packaged + checked into git.** The SyncNet tool now lives in the separate `tools` repo at `tools/syncnet-lipsync/` (GitHub, private, pushed) — vendored SyncNet + `sync_offset.py` + `salvage_crops.py`, with `README.md`/`INSTALL.md`/`requirements.txt`. This folder (`work/SUP-52486-lipsync/`, in the `work` repo, pushed) is the **case record** only — no tool code. Improvement made while packaging: `sync_offset.py` now **streams each timing's result** as it is computed (was buffered to the end → a crash lost everything and forced the salvage script); re-validated against the prior 4-timing rendition run — identical numbers (+80 ms, matching confidences).
- **DIY estimator (v1) — ARCHIVED.** mediapipe mouth-openness × audio RMS envelope, cross-correlated. Too noisy to lock on 540p lecture footage (max conf ~0.24). `older_versions/diy/`.
- **SyncNet — BUILT and RUN.** venv `~/.venvs/sup-52486-syncnet`. Sign convention: **+ms = audio leads video**; 40 ms/frame.
- **Two content sets tested** (each source + rendition), 6–13 timings each:
  - `0_mq6kac22` — src 2160p/60, rendition 1080p/30. Flat **+80 ms (2 fr)** audio-lead on BOTH. **Not** visually detectable.
  - `0_m6cmac6e` — src & rendition both 1080p/~24.92fps. Flat **~+40 ms (1 fr)**, a couple +80/+120 blips, 3 no-face, 1 weak. **Slight** visible audio-lead.
  - Results saved in `results/*.md`.
- **Key conclusions:**
  1. Offsets are **flat (no drift)** across timings, and **essence-level** (src≡rendition behaviour ⇒ not container/codec/PTS).
  2. **SyncNet is the wrong instrument here.** ±1-frame (40 ms) accuracy ⇒ only reliable for gross desync ≥ ~2–3 frames. The perceptually-relevant offsets here are ~1 frame — inside its noise. This is why measured magnitude does **not** track what the eye sees (mq6kac22 measures larger yet looks clean; m6cmac6e measures smaller yet is visible).
  3. `sync_offset.py` also forces `-r 25` + `-async 1`, which discards container timing and re-quantises non-25fps content — another reason its ms isn't comparable across the two sets.

## Current task
Need a **sub-frame, essence-level** sync measurement (SyncNet can't resolve ~1-frame offsets).
Planned method: **forced-alignment vs lip-closure** — ASR forced-alignment for exact audio timestamps of bilabials (m/b/p, lips fully close) vs landmark-detected video lip-closure frames; take the gap at native fps + full sample rate (~5–10 ms resolution, no resample, no container dependence). Not yet started.

## Tooling / env
- Reference asset: `1_v9fjnlso_1_9l1ayldb_540p.mp4` (in `~/Downloads` → `/mnt/c/Users/anatol.schwartz/Downloads/`): 540p H.264 25fps (tb 1/12800), AAC 44100Hz, ~29m. ffprobe: video & audio both `start_pts=0`.
- DIY venv (external, mediapipe/scipy): `/home/anatolschwartz/.venvs/sup-52486-lipsync`. SyncNet will need a **separate** venv (PyTorch).
- ffmpeg 6.1.1 on PATH; python 3.12; x86_64 WSL.

## Files
**Tool (moved out):** `sync_offset.py`, `salvage_crops.py`, and the vendored SyncNet pipeline now live in the `tools` repo at `tools/syncnet-lipsync/` — not here.

**This folder (case record):**
- `results/*.md` — saved per-content offset tables (`0_mq6kac22_*`, `0_m6cmac6e_*`).
- `SYNCNET_PLAN.md` — original SyncNet implementation plan (now done).
- `lipsync-discussion.md`, `lipsync-csm-note.md` — earlier diagnostic notes (out-of-scope playback material; history only).
- `older_versions/diy/` — archived DIY v1 tool (mediapipe × RMS cross-corr — basis for the planned sub-frame method).
