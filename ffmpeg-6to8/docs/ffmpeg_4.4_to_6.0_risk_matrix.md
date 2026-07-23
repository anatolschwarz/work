# FFmpeg 4.4 → 6.0 Risk Matrix

> Based on: Kaltura production commands (3.15M, Jan-May 2026), codebase inventory, FFmpeg source comparison  
> Generated: 2026-06-07

---

## P0 — Fatal on Hot Path

| Item | Frequency | Change | Detail |
|------|---:|---|---|
| `-async` | 4.9% | **Removed** | Option definition gone from fftools in 6.0. Commands will error. Replacement: `-af aresample=async=1:min_hard_comp=0.1:first_pts=0` |
| `pkt_pts_time` (ffprobe) | Used in code | **Removed** | Field `pkt_pts_time` no longer printed in `-show_frames` output. Renamed to `pts_time`. Field `pkt_pts` (integer) also removed — use `pts`. Kaltura parses this in scene detection, interlace checks, keyframe analysis. |
| `pkt_pts` (ffprobe) | Used in code | **Removed** | Same as above — integer PTS field gone. Use `pts`. |

## P1 — Silent Regression (different output, no error)

| Item | Frequency | Change | Detail |
|------|---:|---|---|
| filter_complex + `-map` duplication | 96.9% | **Behavioral change** | In 4.4: filter_complex output + explicit `-map` = one stream. In 6.0: additive — causes duplicate streams. Fix: named outputs `[vout]`/`[aout]` + map only those. **Already mitigated in Kaltura 6.0 code.** |
| `side_data_list` structure (ffprobe) | Used in code | **Extended** | 6.0 adds nested `components` → `pieces` under frame side data. Code that expects flat structure may break on new content types. Existing types (displaymatrix) unchanged. |
| New frame fields `duration` / `duration_time` (ffprobe) | N/A | **Added** | 6.0 adds frame-level `duration` and `duration_time` alongside existing `pkt_duration`/`pkt_duration_time`. Not breaking but may confuse parsers expecting exact field count in CSV mode. |
| `rotation` in displaymatrix (ffprobe) | Used in code | **NaN handling added** | 6.0 adds `if (isnan(rotation)) rotation = 0` guard. In 4.4 a malformed matrix could produce NaN in JSON output. Behavior improves but output value may differ for edge-case files. |
| Threaded muxing | 100% | **New in 6.0** | Every muxer runs in its own thread. Changes timing, interleaving, memory usage. May surface race conditions in downstream processing that reads output mid-write. |

## P2 — Warning on Hot Path (functional but noisy)

| Item | Frequency | Change | Detail |
|------|---:|---|---|
| `-vsync` (flag name) | 98.3% | **Deprecated** | Prints: "-vsync is deprecated. Use -fps_mode". Still functional. |
| `-vsync` (numeric values) | 0% in stats | **Deprecated** | Prints: "Passing a number to -vsync is deprecated". Already mitigated — stats show `cfr` (text). |
| `-rc_eq` | 98.3% | **No-op for libx264** | `rc_eq` is an mpegvideo encoder option (mpeg1/2/4/snow only). Still exists in 6.0 for those codecs. With libx264, it was never applied — passed as unrecognized generic option. In 6.0 with stricter option routing: **verify empirically** — may warn or silently drop. |
| `-map_channel` | In code, 0% in stats | **Deprecated** | Docs state: "deprecated and will be removed. It can be replaced by the pan filter." Still functional in 6.0. |

## P3 — Low Frequency / Low Impact

| Item | Frequency | Change | Detail |
|------|---:|---|---|
| `libfaac` | 0.0% (9 cmds) | **Removed** | Encoder removed in FFmpeg 3.2. Fatal for those 9 commands. Use `libfdk_aac`. |
| `channel_layout` (ffprobe) | Used in code | **Internal API changed** | Output field name unchanged (`channel_layout`). Internal source changed from `frame->channels`/bitmask to `frame->ch_layout.nb_channels`/AVChannelLayout. JSON output format same — no action needed unless parsing layout strings that changed naming. |
| `-encryption_scheme` / `-encryption_key` | 0.0% (1234 cmds) | **Unchanged** | Still functional in 6.0. |

## P4 — No Action Required

| Item | Frequency | Status in 6.0 |
|------|---:|---|
| `-x264opts` | 96.7% | Still functional (both `x264opts` and `x264-params` exist) |
| `-flags +loop+mv4` | 98.3% | Still defined. No-op for libx264 (only mpeg4/mpeg2 use them) |
| `-cmp 256` | 98.3% | Still defined. No-op for libx264 |
| `-partitions` | 98.3% | Still functional for libx264 |
| `-subq`, `-me_range`, `-keyint_min`, `-i_qfactor`, `-trellis`, `-refs`, `-bf`, `-sc_threshold`, `-bt`, `-coder` | 93-98% | All still valid in options_table.h |
| `-qmin`, `-qmax`, `-qcomp`, `-qdiff` | 96.7% | Unchanged |
| `-force_key_frames expr:'gte(t,n_forced*2)'` | 96.6% | Unchanged |
| `-write_btrt 0` | 99.9% | Works (new option in 6.0, absent in 4.4) |
| `-max_muxing_queue_size` | 91.2% | Default unchanged (128). Explicitly set — safe. |
| `-vprofile` | 96.7% | Routes to `-profile:v` internally. No warning. |
| `-map_chapters -1`, `-map_metadata -1` | 99.6% | Unchanged |
| `aresample=async=1:...` | 93.3% | Filter unchanged |
| `-print_format json` (ffprobe) | Used in code | Unchanged |
| `-show_streams`, `-show_format`, `-show_programs`, `-show_data` | Used in code | All unchanged |
| `-of csv` (ffprobe) | Used in code | Writer unchanged |
| ffprobe fields: `codec_name`, `codec_type`, `pix_fmt`, `width`, `height`, `bit_rate`, `duration`, `sample_rate`, `channels`, `display_aspect_ratio`, `r_frame_rate`, `avg_frame_rate`, `profile`, `level`, `format_name`, `size` | Used in code | All unchanged |
| ffprobe fields: `color_space`, `color_transfer`, `color_primaries` | Used in code | Unchanged |
| ffprobe frame fields: `pkt_duration_time`, `pkt_size`, `pict_type`, `coded_picture_number`, `interlaced_frame`, `top_field_first`, `key_frame` | Used in code | All unchanged |
| `rotation` tag in stream tags | Used in code | Unchanged (read from metadata) |

---

## ffprobe Summary

| Field | 4.4 | 6.0 | Action |
|-------|-----|-----|--------|
| `pkt_pts` | ✓ (frame) | **REMOVED** | Use `pts` |
| `pkt_pts_time` | ✓ (frame) | **REMOVED** | Use `pts_time` |
| `pkt_dts` | ✓ | ✓ | None |
| `pkt_dts_time` | ✓ | ✓ | None |
| `pts_time` | ✓ | ✓ | None |
| `pkt_duration` | ✓ | ✓ | None |
| `pkt_duration_time` | ✓ | ✓ | None |
| `duration` (frame) | ✗ | **NEW** | No action (additive) |
| `duration_time` (frame) | ✗ | **NEW** | No action (additive) |
| `key_frame` | ✓ | ✓ | None |
| `coded_picture_number` | ✓ | ✓ | None |
| `interlaced_frame` | ✓ | ✓ | None |
| `top_field_first` | ✓ | ✓ | None |
| `pict_type` | ✓ | ✓ | None |
| `pkt_size` | ✓ | ✓ | None |
| `channels` | ✓ | ✓ | None (internal API changed, output same) |
| `channel_layout` | ✓ | ✓ | None (internal API changed, output same) |
| `side_data_list` | flat | **extended** (components/pieces) | Verify parser handles unknown nested keys |

---

## Required Actions

### Must fix before upgrade:

1. **`-async` (4.9%)** — Remove from commands. Replace with `-af aresample=async=1:min_hard_comp=0.1:first_pts=0` (or confirm the `-filter_complex 'aresample=...[aout]'` path already covers these commands).

2. **ffprobe `pkt_pts_time` parsing** — Update all `-show_entries frame=pkt_pts_time,...` to use `pts_time` instead. Check `KFFMpegMediaParser.php` and `KChunkedEncodeUtils.php` for:
   - `-show_entries frame=pkt_pts_time,pts_time` → change to `pts_time` only
   - Any code that reads the `pkt_pts_time` key from JSON → read `pts_time`
   - Note: Kaltura code already requests BOTH `pkt_pts_time,pts_time` in some places — in 6.0, only `pts_time` will have a value.

### Verify empirically:

3. **`-rc_eq` (98.3%)** — Run a test command with `-rc_eq 'blurCplx^(1-qComp)'` on FFmpeg 6.0 with `-c:v libx264`. Determine if it: errors, warns, or is silently ignored.

4. **`-show_entries` with removed field** — Run `ffprobe -show_frames -show_entries frame=pkt_pts_time -of json test.mp4` on 6.0. Confirm it outputs empty/absent for that field rather than erroring.

### Already mitigated in Kaltura 6.0 code:

- filter_complex named outputs ✓
- -vsync text values ✓
- -deinterlace → -vf yadif ✓
- -write_btrt 0 ✓
- -async → aresample filter ✓ (in the 6.0 code path)

---

## Empirical Verification Commands

```bash
# 1. Does -rc_eq error with libx264?
ffmpeg -i test.mp4 -c:v libx264 -crf 23 -rc_eq 'blurCplx^(1-qComp)' -f null - 2>&1 | grep -iE "error|warn|not found|unrecognized"

# 2. Does -async error?
ffmpeg -i test.mp4 -c:a libfdk_aac -async 1 -f null - 2>&1 | grep -iE "error|option"

# 3. ffprobe pkt_pts_time — does it silently omit or error?
ffprobe -show_frames -show_entries frame=pkt_pts_time,pts_time -of json -v quiet test.mp4 2>&1 | head -30

# 4. ffprobe side_data_list structure check
ffprobe -show_streams -print_format json -v quiet test.mp4 | python3 -c "import sys,json; d=json.load(sys.stdin); [print(s.get('side_data_list','none')) for s in d['streams']]"

# 5. filter_complex duplication check (without named outputs)
ffmpeg -i test.mp4 -filter_complex 'aresample=async=1' -map v:0 -map a:0 -c:v libx264 -c:a libfdk_aac -f mp4 /tmp/test_dup.mp4 2>&1
ffprobe -show_streams -v quiet /tmp/test_dup.mp4 | grep -c "codec_type=audio"
# Should be 1. If 2 → duplication confirmed.
```
