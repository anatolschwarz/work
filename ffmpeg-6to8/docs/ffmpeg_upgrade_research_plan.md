# FFmpeg Version Upgrade Research Plan

> Purpose: Structured research process to identify breaking changes, deprecations, and behavioral shifts between FFmpeg versions.  
> Reusable for any version gap. Version-agnostic until Phase 3.  
> Can be executed by a human, LLM, or automated pipeline.

---

## Inputs Required

1. **Source version** — the FFmpeg version currently in production (e.g., 6.0)
2. **Target version** — the FFmpeg version being upgraded to (e.g., 8.0)
3. **Inventory file** — `kaltura-ffmpeg-inventory.md` (or equivalent): list of codecs, flags, filters, ffprobe fields, muxers in use
4. **Stats file** — `ffmpeg_stats_output.md` (or equivalent): frequency-ranked usage from production command lines

---

## Phase 1: Repo Scan (version-agnostic)

**Goal:** Know what your codebase actually uses.

1. Clone/access the transcoding codebase
2. Extract:
   - Video/audio encoders
   - Filters (video, audio, lavfi)
   - Muxers/container formats
   - All CLI flags (with values where possible)
   - ffprobe invocation patterns and parsed fields
   - Implicit defaults (flags NOT set that have a default in ffmpeg)
   - Any version-conditional code already present
3. Output: `ffmpeg-inventory.md`

## Phase 2: Production Command-Line Analysis (version-agnostic)

**Goal:** Know what's hot path vs. edge case.

1. Obtain a representative sample of real encode commands (the bigger the better)
2. Run extraction script to produce frequency-ranked tables:
   - Codecs, filters, formats, resolutions, CRF/GOP/FPS values
   - All flags ranked by frequency
   - Deprecated flags still in use (with count)
   - Expected flags never seen (cross-ref with inventory)
3. Output: `ffmpeg-stats.md`

## Phase 3: Changelog & Docs Research (version-specific)

**Goal:** For each item in the inventory, determine if it changed between source and target versions.

### Sources to check:

| Source | URL / Location |
|--------|---------------|
| FFmpeg Changelog | `Changelog` in source tree |
| FFmpeg Release Notes | https://ffmpeg.org/download.html (per-version) |
| APIchanges | `doc/APIchanges` in source tree |
| Deprecation list | `doc/deprecated.rst` or `FATE` |
| ffmpeg CLI docs | `doc/ffmpeg.texi` in source tree |
| ffprobe docs | `doc/ffprobe.texi` in source tree |
| Codec-specific docs | `doc/encoders.texi` — libx264/libx265/libfdk_aac sections |
| Filter docs | `doc/filters.texi` |
| Muxer docs | `doc/muxers.texi` |
| Git log (targeted) | `git log --oneline vX..vY -- libavcodec/libx264.c` etc. |
| Mailing list / trac | https://trac.ffmpeg.org |
| FFmpeg wiki | https://trac.ffmpeg.org/wiki (migration guides, encoding guides) |
| Trac regressions | https://trac.ffmpeg.org/query?keywords=~regression |
| Community blogs / posts | Search: "ffmpeg <ver> breaking changes", "ffmpeg <ver> migration" |
| Mailing list archives | https://lists.ffmpeg.org/pipermail/ffmpeg-user/ |
| libx264 upstream changelog | https://code.videolan.org/videolan/x264 — encoder defaults tied to linked lib version |
| libx265 upstream changelog | https://bitbucket.org/multicoreware/x265_git |
| libfdk_aac upstream | https://github.com/mstorsjo/fdk-aac |

### Full help diff (requires both binaries built):

```bash
# ffmpeg full help
ffmpeg-old -h full > ffmpeg_help_old.txt
ffmpeg-new -h full > ffmpeg_help_new.txt
diff ffmpeg_help_old.txt ffmpeg_help_new.txt > ffmpeg_help_diff.txt

# ffprobe help
ffprobe-old -h > ffprobe_help_old.txt
ffprobe-new -h > ffprobe_help_new.txt
diff ffprobe_help_old.txt ffprobe_help_new.txt > ffprobe_help_diff.txt

# Per-encoder options
for enc in libx264 libx265 libfdk_aac; do
  ffmpeg-old -h encoder=$enc > enc_${enc}_old.txt
  ffmpeg-new -h encoder=$enc > enc_${enc}_new.txt
  diff enc_${enc}_old.txt enc_${enc}_new.txt > enc_${enc}_diff.txt
done

# Per-muxer options
for mux in mp4 mpegts hls segment matroska; do
  ffmpeg-old -h muxer=$mux > mux_${mux}_old.txt
  ffmpeg-new -h muxer=$mux > mux_${mux}_new.txt
  diff mux_${mux}_old.txt mux_${mux}_new.txt > mux_${mux}_diff.txt
done

# Per-filter options
for flt in aresample yadif scale overlay loudnorm amerge pan; do
  ffmpeg-old -h filter=$flt > flt_${flt}_old.txt
  ffmpeg-new -h filter=$flt > flt_${flt}_new.txt
  diff flt_${flt}_old.txt flt_${flt}_new.txt > flt_${flt}_diff.txt
done
```

### Documentation diff (source tree):

```bash
diff ffmpeg-old/doc/ffmpeg.texi ffmpeg-new/doc/ffmpeg.texi > doc_ffmpeg_diff.txt
diff ffmpeg-old/doc/ffprobe.texi ffmpeg-new/doc/ffprobe.texi > doc_ffprobe_diff.txt
diff ffmpeg-old/doc/filters.texi ffmpeg-new/doc/filters.texi > doc_filters_diff.txt
diff ffmpeg-old/doc/muxers.texi ffmpeg-new/doc/muxers.texi > doc_muxers_diff.txt
diff ffmpeg-old/doc/encoders.texi ffmpeg-new/doc/encoders.texi > doc_encoders_diff.txt
```

Filter diffs by relevant sections:
```bash
grep -B5 -A20 "libx264\|libx265\|libfdk" doc_encoders_diff.txt > doc_encoders_relevant.txt
grep -B5 -A20 "aresample\|yadif\|scale\|overlay\|loudnorm" doc_filters_diff.txt > doc_filters_relevant.txt
grep -B5 -A20 "mp4\|movflags\|concat\|segment\|hls" doc_muxers_diff.txt > doc_muxers_relevant.txt
```

### ffprobe empirical diff (requires both binaries built):

```bash
# Stream/format JSON output
ffprobe-old -show_streams -show_format -print_format json -v quiet test.mp4 > probe_streams_old.json
ffprobe-new -show_streams -show_format -print_format json -v quiet test.mp4 > probe_streams_new.json
diff probe_streams_old.json probe_streams_new.json

# Frame output JSON
ffprobe-old -show_frames -select_streams v -of json -v quiet test.mp4 | head -100 > probe_frames_old.json
ffprobe-new -show_frames -select_streams v -of json -v quiet test.mp4 | head -100 > probe_frames_new.json
diff probe_frames_old.json probe_frames_new.json

# CSV frame output (column order matters for positional parsers)
ffprobe-old -show_frames -select_streams v -of csv -v quiet test.mp4 | head -5 > probe_csv_old.txt
ffprobe-new -show_frames -select_streams v -of csv -v quiet test.mp4 | head -5 > probe_csv_new.txt
diff probe_csv_old.txt probe_csv_new.txt

# Test behavior with removed fields in -show_entries
ffprobe-new -show_frames -show_entries frame=pkt_pts_time,pts_time,pkt_duration_time,duration_time,coded_picture_number -of json -v quiet test.mp4 | head -30
```

### External web research:

Search for known caveats not captured in source/doc diffs:

- `"ffmpeg <target_ver> breaking changes"`
- `"ffmpeg upgrade from <source_ver> to <target_ver>"`
- `"ffmpeg <target_ver> regression"`
- `"libx264 default changes <year>"`
- Trac tickets: https://trac.ffmpeg.org/query?keywords=~regression
- Mailing list archives: https://lists.ffmpeg.org/pipermail/ffmpeg-user/

### Research categories (run separately, can be parallelized):

1. **Encoders/codecs** — flag changes, default changes, removed options
2. **Filters** — renamed, removed, changed parameters/defaults
3. **Muxers/demuxers** — option changes, default behavior, new requirements
4. **CLI flags** — removed, deprecated, syntax changes, interaction changes
5. **ffprobe** — output format changes, field renames/removals, JSON structure changes, new/removed fields, `-show_*` behavioral changes, `-of` format differences

### Research per item:

For each flag/codec/filter/field in the inventory (prioritized by frequency from stats):

1. **Still exists?** — removed, renamed, or still present
2. **Default changed?** — different default value between versions
3. **Syntax changed?** — same name but different accepted values or format
4. **Behavioral change?** — same syntax but different output (e.g., quality, speed, metadata)
5. **Deprecated?** — still works but emits warning; when will it be removed?
6. **Interaction change?** — flag combinations that now conflict or behave differently together

### ffprobe-specific checks:

For each field parsed by the codebase (from inventory section 9):

1. **Field still present?** — renamed (e.g., `pkt_pts_time` → `pts_time`) or removed
2. **JSON structure changed?** — nesting, array vs object, new wrapper keys
3. **Value format changed?** — numeric precision, string encoding, null vs absent
4. **New required flags?** — does `-show_streams` still produce the same fields without extra args
5. **`-print_format` / `-of` behavior** — csv column order, json key order, default output format
6. **`-show_data` / `-show_programs`** — output structure changes
7. **`side_data_list`** — structure and key naming changes

### Output format per finding:

```
| Flag/Feature | Status | Versions Affected | Impact | Replacement | Notes |
```

Where Status is one of: `removed`, `deprecated`, `default-changed`, `syntax-changed`, `behavior-changed`, `unchanged`

And Impact is: `fatal` (command fails), `silent` (different output, no error), `warning` (runs with deprecation message), `cosmetic` (log noise only)

## Phase 4: Risk Assessment

**Goal:** Prioritize what to fix vs. what to monitor.

Combine Phase 3 findings with Phase 2 frequency data:

```
Risk Score = Impact Severity × Frequency Percentage
```

Categories:
- **P0 — Fix before upgrade**: Fatal errors on hot-path commands (e.g., `-rc_eq` removed, 94.6% of commands)
- **P1 — Fix before production**: Silent behavioral changes on hot path (output differs, no error)
- **P2 — Fix soon**: Deprecated with warning on hot path (works but noisy)
- **P3 — Monitor**: Changes affecting <1% of commands
- **P4 — Ignore**: Cosmetic or affects dead code paths only

Output: `ffmpeg-risk-matrix.md`

## Phase 5: Verification Plan

**Goal:** Confirm findings empirically before and after upgrade.

For each P0/P1 finding:

1. **Construct minimal reproduce command** — simplest command that exercises the flag/behavior
2. **Run on source version** — capture: exit code, stderr, output file metadata (ffprobe JSON), VMAF/SSIM if relevant
3. **Run on target version** — same capture
4. **Diff results** — flag: errors, warnings, metadata changes, quality delta

For P2 findings:
- Run and confirm warning message text (for log monitoring)

### Automated test script structure:

```bash
#!/bin/bash
# For each test case:
#   1. Run command on ffmpeg-old
#   2. Run command on ffmpeg-new
#   3. Compare: exit code, stderr (warnings/errors), ffprobe output, VMAF
#   4. Report pass/fail/delta
```

Output: `ffmpeg-verification-results.md`

## Phase 6: Migration Recommendations

**Goal:** Actionable fix list.

For each finding that requires action:

1. **What to change** — exact flag/syntax replacement
2. **Where to change** — file and line in codebase (from Phase 1)
3. **Backward compatible?** — does the fix work on BOTH old and new versions? (important for rolling upgrades)
4. **Test command** — before/after command pair to verify the fix

Output: `ffmpeg-migration-actions.md`

---

## Execution Notes

- Phases 1-2 are **version-agnostic** — do them once, reuse across upgrades
- Phase 3 is the bulk of the work — can be parallelized by category (codecs, filters, muxers, ffprobe)
- Phase 4 is mechanical — combine phase 2 + 3 outputs
- Phase 5 requires both FFmpeg binaries available on the same machine
- Phase 6 requires access to the codebase

### For LLM execution:

- Feed the inventory + stats files as context
- Ask it to research one category at a time (e.g., "check all flags in section 17 against FFmpeg 7/8 changelogs")
- Provide the changelog/docs as fetched content if the LLM has no web access
- Validate LLM claims against actual ffmpeg binary (`ffmpeg -h encoder=libx264`, `ffmpeg -h full`)

### For CI/automation:

- Phase 5 can be a shell script comparing ffprobe JSON output between two binaries
- Flag any delta in: stream count, codec params, duration, bitrate (>5% deviation), pixel format, color metadata
- Run VMAF on a reference set for quality regression detection

---

## Appendix: Known High-Risk Areas Across FFmpeg Majors

These areas historically cause silent regressions:

1. **Default thread count** — changes per version and per codec
2. **Color metadata handling** — color_range, color_space defaults shift
3. **Filter graph auto-insertion** — scale/format filters auto-added in some versions
4. **Timestamp handling** — pts/dts calculation edge cases
5. **Muxer defaults** — movflags, frag behavior, btrt atom
6. **Encoder defaults** — x264/x265 internal defaults change with linked library version, not just ffmpeg version
7. **Deprecated flag removal** — usually warned for 2 major versions, then hard-removed
8. **force_key_frames expr parsing** — subtle syntax interpretation changes
9. **filter_complex stream mapping** — resolved ambiguity in FFmpeg 6 (named outputs required)
10. **Bitrate control interaction** — `-crf` + `-b:v` + `-maxrate` priority/override logic
