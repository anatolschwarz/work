# lipsync_check — quick user guide

Estimates the audio/video lip-sync offset baked into a video file, at chosen
timings. Cross-correlates mouth-openness (mediapipe face landmarks) against the
speech-energy envelope. **Measures the file only — it cannot reproduce
streaming/playback (ABR / stall / dropped-frame) desync.**

## Requirements
- ffmpeg on PATH
- the venv with deps (mediapipe, scipy): `/home/anatolschwartz/.venvs/sup-52486-lipsync`
- `models/face_landmarker.task` (already in this folder)

## Run
```bash
V=/home/anatolschwartz/.venvs/sup-52486-lipsync/bin/python

# specific timings (mm:ss, hh:mm:ss, or seconds)
$V lipsync_check.py VIDEO.mp4 --at 02:30,05:00,15:00

# auto-pick the N loudest windows
$V lipsync_check.py VIDEO.mp4 --auto -n 5

# options
--window 12        # window length in s, CENTERED on each timing
                   #   (--at 02:30 --window 6  ->  02:27-02:33; default 6)
--json out.json    # also write results to JSON
```

## Reading the output
- `offset_ms` — **+ = audio leads video**, − = video ahead.
- `confidence` — 0–1 (cross-correlation peak height). **Trust only ≥ 0.30.**
  Forced to 0 when the peak hits the search edge (no real lock).
- `face%` — frames with a face detected. High face% + low confidence = face
  visible but its mouth doesn't track the audio (voiceover / listening / not
  the speaker) → pick a different moment.
- Bottom line prints the median offset over confident windows only.

## Tips / limits
- Pick moments with a **large, front-facing, clearly-speaking** face.
- Loudest ≠ best: `--auto` may land on slides or non-speakers.
- Rough method (mouth-open ↔ loudness is loose); good for ~tens-of-ms offsets
  and drift trends, not exact per-phoneme timing. For reliable numbers use a
  dedicated AV-sync model (e.g. SyncNet).
- Search range is ±250 ms; offsets beyond that read as "no lock".
