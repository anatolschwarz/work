# A/V Lipsync Investigation

> From session `0caae3cc` (2026-07-05). Diagnostic only — no tools run yet.

## Problem
- **VOD** (not live). Mezzanine ~30 MB/s UHD, 1h25m talking-head lecture.
- Transcoded to ABR ladder (360p/400k → 1080p/4000k).
- Customer reports lipsync issue **only on Kaltura web players**. Severity unknown.
- QA: downloaded source + rendition, played on **desktop** → clean (or <100ms).

## Ruled out
- **Transcoding** — desktop-clean rendition means the decoded essence is aligned.
- **Edit lists** — none present in the renditions.
- **AAC priming** — with no edit list to trim it, untrimmed priming would desync **desktop too**, not web-only. Desktop is clean → priming isn't the hidden offset.
- (Caveat: rule-outs only hold if QA checked the **end** of 85 min, not just the start.)

## Remaining suspects (packaging → web playback only)
1. Audio/video segment boundaries not duration-aligned → offset.
2. Per-track timestamp rebasing (audio & video zeroed independently) → constant desync.
3. Timescale rounding drift over 85 min.
4. **MSE handling of per-track start-PTS** — if audio/video start at different PTS in the MP4, desktop honors it, browser may not. ← main web-only candidate.

## Decisive test
Play the **actual Kaltura HLS/DASH stream** (not the files) and check sync at the **end**, not the start.
