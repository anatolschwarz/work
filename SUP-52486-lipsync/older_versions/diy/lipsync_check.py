#!/usr/bin/env python3
"""
lipsync_check.py — estimate audio/video lip-sync offset in a video file.

Approach (no ML sync model): build two 1-D signals over a window and
cross-correlate them.
  - VIDEO: mouth-openness per frame (mediapipe FaceMesh inner-lip gap,
           normalized by face height -> scale invariant).
  - AUDIO: speech-energy envelope (RMS), resampled to the video frame rate.
The lag at peak correlation is the A/V offset; the peak height is confidence.

Measures the offset baked into THIS file only. It cannot reproduce
streaming/playback (ABR/stall/dropped-frame) desync.

Usage:
  lipsync_check.py VIDEO --at 00:30,05:00,15:00 [--window 6] [--json out.json]
  lipsync_check.py VIDEO --auto [-n 5]

Sign convention: offset_ms > 0  => audio LEADS video (sound ahead of picture).
"""
import argparse, json, subprocess, sys, tempfile, os
import numpy as np

MAX_LAG_S = 0.25   # search +/- 250 ms (real in-file A/V errors are small)
BP_LO, BP_HI = 1.0, 8.0  # syllable-rhythm band (Hz)


def parse_ts(s):
    """'90', '1:30', '01:02:03' -> seconds (float)."""
    s = s.strip()
    parts = s.split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"bad timestamp: {s}")


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=avg_frame_rate,duration",
         "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"][0]
    num, den = st["avg_frame_rate"].split("/")
    fps = float(num) / float(den) if float(den) else 25.0
    dur = float(st.get("duration", 0) or 0)
    return fps, dur


def audio_envelope(path, start, dur, fps, ar=16000):
    """RMS envelope of the audio window, one value per video frame."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{start}", "-t", f"{dur}",
         "-i", path, "-ac", "1", "-ar", str(ar), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    hop = int(round(ar / fps))
    if hop < 1 or len(a) < hop:
        return np.zeros(0)
    n = len(a) // hop
    a = a[: n * hop].reshape(n, hop)
    return np.sqrt((a ** 2).mean(axis=1) + 1e-9)


MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "models", "face_landmarker.task")


def mouth_openness(path, start, dur, fps):
    """Mouth-open ratio per frame over the window; NaN where no face."""
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
    if not os.path.exists(MODEL):
        raise RuntimeError(f"model not found: {MODEL}")
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000.0)
    n_frames = int(round(dur * fps))
    opts = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL),
        running_mode=vision.RunningMode.VIDEO, num_faces=1)
    landmarker = vision.FaceLandmarker.create_from_options(opts)
    vals, got = [], 0
    for i in range(n_frames):
        ok, frame = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int(round((start + i / fps) * 1000))
        res = landmarker.detect_for_video(mp_img, ts_ms)
        if not res.face_landmarks:
            vals.append(np.nan)
            continue
        lm = res.face_landmarks[0]
        lip = abs(lm[13].y - lm[14].y)          # inner lip vertical gap
        face_h = abs(lm[10].y - lm[152].y) + 1e-6  # forehead->chin
        vals.append(lip / face_h)
        got += 1
    cap.release(); landmarker.close()
    return np.array(vals, dtype=np.float32), (got / n_frames if n_frames else 0.0)


def _interp_nans(x):
    x = x.copy()
    idx = np.arange(len(x))
    good = ~np.isnan(x)
    if good.sum() < 2:
        return None
    x[~good] = np.interp(idx[~good], idx[good], x[good])
    return x


def _z(x):
    x = x - x.mean()
    s = x.std()
    return x / s if s > 1e-9 else x


def _bandpass(x, fps):
    """Band-pass to the syllable band; strips DC/slow drift that causes
    spurious edge-latching in the cross-correlation."""
    from scipy.signal import butter, filtfilt
    hi = min(BP_HI, fps / 2 - 0.5)
    if len(x) < 30 or hi <= BP_LO:
        return _z(x)
    b, a = butter(3, [BP_LO, hi], btype="band", fs=fps)
    if len(x) <= 3 * max(len(a), len(b)):
        return _z(x)
    return _z(filtfilt(b, a, x))


def measure(path, at, window, fps):
    """`at` is the point of interest; the window is centered on it."""
    read_start = max(0.0, at - window / 2.0)
    vid, det = mouth_openness(path, read_start, window, fps)
    aud = audio_envelope(path, read_start, window, fps)
    vid = _interp_nans(vid) if len(vid) else None
    if vid is None or len(aud) < 4:
        return {"at_s": at, "offset_ms": None, "confidence": 0.0,
                "face_detect_rate": round(det, 2), "note": "no face / no audio"}
    m = min(len(vid), len(aud))
    v, a = _bandpass(vid[:m], fps), _bandpass(aud[:m], fps)
    from scipy.signal import correlate, correlation_lags
    corr = correlate(v, a, mode="full") / m
    lags = correlation_lags(len(v), len(a), mode="full")
    max_lag = int(round(MAX_LAG_S * fps))
    keep = np.abs(lags) <= max_lag
    corr, lags = corr[keep], lags[keep]
    k = int(np.argmax(corr))
    peak = float(corr[k])
    lag = float(lags[k])
    # parabolic sub-sample refinement
    if 0 < k < len(corr) - 1:
        y0, y1, y2 = corr[k - 1], corr[k], corr[k + 1]
        denom = (y0 - 2 * y1 + y2)
        if abs(denom) > 1e-9:
            lag += 0.5 * (y0 - y2) / denom
    # positive lag = video lags audio = audio leads video
    offset_ms = lag / fps * 1000.0
    edge = abs(lags[k]) >= max_lag  # peak at boundary -> no real lock
    r = {"at_s": at, "offset_ms": round(offset_ms, 1),
         "confidence": round(max(peak, 0.0), 2),
         "face_detect_rate": round(det, 2)}
    if edge:
        r["confidence"] = 0.0
        r["note"] = "peak at search edge (no lock)"
    return r


def auto_windows(path, dur, window, n):
    """Pick n loudest, spread-out windows across the file."""
    env = audio_envelope(path, 0, dur, fps=1.0)  # 1 value/sec
    if len(env) == 0:
        return [dur * (i + 1) / (n + 1) for i in range(n)]
    order = np.argsort(env)[::-1]
    picks, min_gap = [], max(window * 2, dur / (n * 2 + 1))
    for c in order:
        if all(abs(c - p) >= min_gap for p in picks):
            picks.append(float(c))
        if len(picks) >= n:
            break
    return sorted(float(p) for p in picks)  # centers; measure() windows around


def main():
    ap = argparse.ArgumentParser(description="Estimate A/V lip-sync offset.")
    ap.add_argument("video")
    ap.add_argument("--at", help="comma list of timestamps, e.g. 00:30,05:00")
    ap.add_argument("--auto", action="store_true", help="auto-pick loud windows")
    ap.add_argument("-n", type=int, default=5, help="# windows for --auto")
    ap.add_argument("--window", type=float, default=6.0, help="window seconds")
    ap.add_argument("--json", help="write results to JSON file")
    args = ap.parse_args()

    if not os.path.exists(args.video):
        sys.exit(f"not found: {args.video}")
    fps, dur = probe(args.video)

    if args.auto:
        starts = auto_windows(args.video, dur, args.window, args.n)
    elif args.at:
        starts = [parse_ts(s) for s in args.at.split(",")]
    else:
        sys.exit("give --at TIMES or --auto")

    print(f"file: {os.path.basename(args.video)}  fps={fps:.3f}  "
          f"dur={dur:.1f}s  window={args.window}s")
    print(f"{'at':>9}  {'offset_ms':>10}  {'conf':>5}  {'face%':>5}")
    results = []
    for s in starts:
        r = measure(args.video, s, args.window, fps)
        results.append(r)
        off = "n/a" if r["offset_ms"] is None else f"{r['offset_ms']:+.1f}"
        mm, ss = divmod(int(s), 60)
        print(f"{mm:02d}:{ss:02d}    {off:>10}  {r['confidence']:>5.2f}  "
              f"{r['face_detect_rate']*100:>4.0f}%")

    good = [r["offset_ms"] for r in results
            if r["offset_ms"] is not None and r["confidence"] >= 0.3]
    if good:
        print(f"\nmedian offset (conf>=0.3): {np.median(good):+.1f} ms  "
              f"[{min(good):+.1f} .. {max(good):+.1f}]  "
              f"(+ = audio leads video)")
    else:
        print("\nno confident windows — pick clearer speech/face timings")

    if args.json:
        json.dump({"file": args.video, "fps": fps, "window": args.window,
                   "results": results}, open(args.json, "w"), indent=2,
                  default=float)
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
