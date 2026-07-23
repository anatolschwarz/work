# FFmpeg 6.0 → 8.1.1 Risk Matrix

> Based on: Kaltura production commands (3.15M, Jan-May 2026), codebase inventory, FFmpeg source comparison  
> Generated: 2026-06-07

---

## P0 — Fatal on Hot Path

| Item | Frequency | Change | Detail |
|------|---:|---|---|
| `-map_channel` | In code (multi-lang path) | **Removed in 7.0** | Changelog: "removed deprecated ffmpeg CLI options -psnr and -map_channel". Commands using it will error. Replacement: `pan` filter or `channelmap` filter. |
| ffprobe `pkt_duration` (frame) | Used in code | **Removed** | Not printed in 8.1 frame output. Replaced by `duration` (frame-level). |
| ffprobe `pkt_duration_time` (frame) | Used in code | **Removed** | Not printed in 8.1 frame output. Replaced by `duration_time` (frame-level). |
| ffprobe `coded_picture_number` | Used in code | **Removed** | Not printed in 8.1 frame output. No direct replacement. |

## P1 — Silent Regression

| Item | Frequency | Change | Detail |
|------|---:|---|---|
| Full parallel pipeline | 100% | **New in 7.0** | "demuxing, decoding, filtering, encoding, and muxing in the ffmpeg CLI now all run in parallel". Broader than 6.0's muxer-only threading. May surface timing/ordering issues in chunk processing. |
| ffprobe `-print_format` | Used in code | **Deprecated** | Renamed to `-output_format` in 6.1. `-print_format` still works as alias in 8.1 but marked deprecated. |
| ffprobe `side_data_list` | Used in code | **Extended further** | 8.1 adds typed side data with `get_type` functions, `HAS_VARIABLE_FIELDS` flag. More nested than 6.0. Parsers expecting fixed structure may trip on new content types. |
| `force_key_frames source_no_drop` | In code (rare) | **Deprecated in 8.x** | Prints warning, still works. Use `source` instead. |
| `-vsync drop` / `-fps_mode drop` | In code | **Deprecated in 8.1** | Prints: "-vsync/fps_mode drop is deprecated". |
| YUV colorspace negotiation | Implicit | **Changed in 7.1** | "YUV colorspace negotiation for codecs and filters, obsoleting the YUVJ pixel format". May affect how `yuv420p` is interpreted with certain sources. Verify no unexpected full-range/limited-range conversion. |

## P2 — Warning (functional but noisy)

| Item | Frequency | Change | Detail |
|------|---:|---|---|
| `-vsync` (flag name) | 98.3% | **Still deprecated** | Same warning as 6.0: "Use -fps_mode". Not removed yet. |
| `-vsync` (numeric) | 0% in stats | **Still deprecated** | Same as 6.0. |
| `-rc_eq` | 98.3% | **Still exists for mpegvideo/snow only** | Same status as 6.0 — no-op for libx264. Needs empirical test. |

## P3 — Low Frequency / Low Impact

| Item | Frequency | Change | Detail |
|------|---:|---|---|
| ffprobe `pkt_pos` source | Used in code | **Moved** | Now accessed via `fd->pkt_pos` (frame decode info) instead of `frame->pkt_pos`. Same output field name — no parsing change needed. |
| ffprobe `pkt_size` source | Used in code | **Moved** | Same as pkt_pos — accessed via `fd->pkt_size`. Output unchanged. |
| Stream specifier syntax | In code | **Minor changes in 7.1** | Metadata matching (`:m:<key>:<val>`) now requires backslash-escaping colons. Multiple stream types in single specifier now error. Unlikely to affect Kaltura's use. |

## P4 — No Action Required

| Item | Frequency | Status in 8.1 |
|------|---:|---|
| `-x264opts` | 96.7% | Still functional |
| `-x264-params` | In code | Still functional |
| `-flags +loop+mv4` | 98.3% | Still defined (no-op for libx264) |
| `-cmp`, `-partitions`, `-trellis`, `-me_range`, `-keyint_min`, `-i_qfactor`, `-refs`, `-bf`, `-sc_threshold`, `-bt`, `-subq` | 93-98% | All still in options_table.h |
| `-force_key_frames expr:'gte(t,n_forced*2)'` | 96.6% | Unchanged (expr syntax works) |
| `-write_btrt 0` | 99.9% | Unchanged |
| `-max_muxing_queue_size` | 91.2% | Unchanged (default still 128) |
| `-vprofile` | 96.7% | Routes to `-profile:v` (with warning to use explicit form) |
| `-filter_complex` + named outputs | 96.9% | Unchanged behavior |
| `-probesize`, `-analyzeduration` | Concat path | Unchanged |
| `-f concat -safe 0` | Concat path | Unchanged |
| `aresample=async=1:...` | 93.3% | Unchanged |
| ffprobe: `pts_time`, `pkt_dts`, `pkt_dts_time` | Used in code | Unchanged |
| ffprobe: `key_frame`, `interlaced_frame`, `top_field_first`, `pict_type` | Used in code | Unchanged (field names same, internal source changed to flags) |
| ffprobe: `pkt_pos`, `pkt_size` | Used in code | Unchanged output |
| ffprobe: `codec_name`, `codec_type`, `pix_fmt`, `width`, `height`, `bit_rate`, `duration`, `sample_rate`, `channels`, `channel_layout`, `display_aspect_ratio`, `r_frame_rate`, `avg_frame_rate`, `profile`, `level` | Used in code | All unchanged |
| ffprobe: `color_space`, `color_transfer`, `color_primaries`, `color_range` | Used in code | Unchanged |
| ffprobe: `format_name`, `size` | Used in code | Unchanged |
| ffprobe: `-show_streams`, `-show_format`, `-show_programs`, `-show_data` | Used in code | All present |
| ffprobe: `-of json` / `-of csv` | Used in code | Still work (via `-output_format` alias) |

---

## ffprobe Frame Fields: 6.0 vs 8.1

| Field | 6.0 | 8.1 | Action |
|-------|-----|-----|--------|
| `pkt_pts` | Already removed | ✗ | — |
| `pkt_pts_time` | Already removed | ✗ | — |
| `pts` | ✓ | ✓ | None |
| `pts_time` | ✓ | ✓ | None |
| `pkt_dts` | ✓ | ✓ | None |
| `pkt_dts_time` | ✓ | ✓ | None |
| `pkt_duration` | ✓ | **REMOVED** | Use `duration` |
| `pkt_duration_time` | ✓ | **REMOVED** | Use `duration_time` |
| `duration` | ✓ | ✓ | None |
| `duration_time` | ✓ | ✓ | None |
| `pkt_pos` | ✓ | ✓ | None |
| `pkt_size` | ✓ | ✓ | None |
| `key_frame` | ✓ | ✓ | None |
| `pict_type` | ✓ | ✓ | None |
| `coded_picture_number` | ✓ | **REMOVED** | No replacement |
| `interlaced_frame` | ✓ | ✓ | None |
| `top_field_first` | ✓ | ✓ | None |
| `best_effort_timestamp` | ✓ | ✓ | None (new in output position) |
| `crop_top/bottom/left/right` | ✗ | **NEW** | No action (additive) |
| `lossless` | ✗ | **NEW** | No action (additive) |

---

## Required Actions for 6.0 → 8.1

### Must fix:

1. **`-map_channel`** — Remove from all code paths. Replace with `pan` filter or `channelmap` filter. Affects multi-language stream handling in `KDLOperatorFfmpeg6_0.php` → `getMappingsForMultiStream()`.

2. **ffprobe `pkt_duration_time`** — Update all `-show_entries frame=...pkt_duration_time...` to use `duration_time`. Affects `KFFMpegMediaParser.php` frame analysis.

3. **ffprobe `pkt_duration`** — Same as above, use `duration`.

4. **ffprobe `coded_picture_number`** — Remove from `-show_entries`. Find alternative if this data is needed (may require decoding with counters).

### Should fix:

5. **`-print_format json`** → `-output_format json` (deprecated alias still works but may be removed).

6. **`force_key_frames source_no_drop`** → `source` (if used anywhere).

### Verify empirically:

7. **YUV colorspace negotiation** — Encode same source with both versions, compare ffprobe `color_range` on output. Check for unexpected full→limited or limited→full conversion with `yuv420p`.

8. **Full parallel pipeline** — Run chunked encode workload, verify chunk timing consistency matches 6.0 behavior.

---

## Empirical Verification Commands

```bash
# 1. Does -map_channel error?
ffmpeg -i test.mp4 -map_channel 0.0.0 -c:a libfdk_aac -f null - 2>&1 | head -5

# 2. ffprobe pkt_duration_time — gone?
ffprobe -show_frames -show_entries frame=pkt_duration_time,duration_time -of json -v quiet test.mp4 2>&1 | head -20

# 3. ffprobe coded_picture_number — gone?
ffprobe -show_frames -show_entries frame=coded_picture_number -of json -v quiet test.mp4 2>&1 | head -20

# 4. Color range check
ffmpeg -i test.mp4 -c:v libx264 -pix_fmt yuv420p -crf 23 -f mp4 /tmp/out81.mp4 2>&1
ffprobe -show_streams -of json /tmp/out81.mp4 | grep color_range

# 5. -print_format still works?
ffprobe -print_format json -show_streams -v quiet test.mp4 2>&1 | head -5

# 6. Parallel pipeline timing (chunked encode)
# Run a chunked encode job, compare chunk durations vs 6.0 output
```
