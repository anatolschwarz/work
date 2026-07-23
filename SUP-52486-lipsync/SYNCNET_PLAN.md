# SyncNet implementation plan (SUP-52486)

Goal: reliable **in-file** A/V offset for the reference asset (and reusable on
other files). Replaces the archived DIY estimator. **Playback-side is OUT of
scope** (see CLAUDE.md) — this only measures the file.

## Approach
Use the established **SyncNet** pipeline (Chung & Zisserman, VGG):
`run_pipeline` (S3FD face detect + track + crop to 224, 25 fps) → `run_syncnet`
(pretrained two-tower CNN: mouth-crop features vs MFCC audio features; slides
audio vs video across lags, picks min-distance lag). Outputs **offset in
frames** + **AV confidence** + min distance.

Reference: https://github.com/joonson/syncnet_python (use a **python-3
compatible fork** — original is py2-era).

## Steps
1. **Venv (separate from DIY):** `python3 -m venv ~/.venvs/sup-52486-syncnet`.
2. **Deps:** torch + torchvision (CPU is fine for short clips), numpy, scipy,
   opencv-python, python_speech_features. ffmpeg already on PATH.
3. **Vendor the code** under `syncnet/` in the project (clone the py3 fork).
4. **Download weights** (repo's `download_model.sh`): `syncnet_v2.model`,
   `sfd_face.pth` → keep under `syncnet/weights/` (or `models/`).
5. **Wrap a CLI** (mirror the old DIY UX): input video, optional `--at`
   timings (trim with `ffmpeg -ss/-t` around each, centered), run
   pipeline+syncnet on each clip, print table: `at | offset_ms | confidence`.
   offset_ms = offset_frames / 25 * 1000. **Confirm sign convention from code
   and document it** (which direction = audio leads).
6. **Test** on `1_v9fjnlso_1_9l1ayldb_540p.mp4`; sanity-check offset+confidence.
   File is 25 fps (matches SyncNet); audio 44.1 kHz is resampled to 16 kHz
   internally — fine.
7. Write `README.md` (usage + install) and update `CLAUDE.md` state.

## Risks / notes
- Fork/torch version compatibility is the main setup risk — pick a maintained
  py3 fork; pin torch to a version its code supports.
- S3FD is heavier than mediapipe but robust to the small 540p face that broke
  the DIY method.
- For specific timings, trim first (ffmpeg) then run the pipeline on the short
  clip — faster than tracking the full 29 min.
- SyncNet confidence is calibrated; typical "good lock" >~ 3–5. Report it raw
  plus a plain-language verdict.

## Definition of done
CLI returns a confident, signed in-file offset (ms) for chosen timings on the
reference asset, with a documented sign convention and a short README.
