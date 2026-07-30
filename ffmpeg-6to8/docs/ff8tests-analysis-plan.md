# ff8tests — Test Analysis Plan

Verification of the Kaltura **FFmpeg 6 → 8.1.1** migration by converting sample assets
with both FF6 and FF8 and comparing them (against each other and against the prod-generated
reference). Sample assets are grouped into **sets** (`setX`, `setY`, …; few sets, each up to
a couple thousand samples).

**Scope of this doc:** methodology + layout only. It stays stable. **Results do NOT live here** —
they live per set under `sets/<SET>/` (see *Local analysis record*). This doc carries at most a
small campaign-status table, never raw rows.

---

## 1. Objectives & the three compares

Each sample is a **session = `<entry>_<asset>`**, encoded twice (our FF6, our FF8). Three compares:

| compare | operands | question |
|---|---|---|
| `compare_ff6` | prod reference vs **our FF6** | baseline sanity — does our FF6 reproduce prod? |
| `compare_ff8` | prod reference vs **our FF8** | **the migration answer** — is FF8 output acceptable vs prod? |
| `compare_ff6_vs_ff8` | our FF6 vs our FF8 (no prod) | **confounder-free** migration signal — isolates the 6→8 change from prod-reference noise |

The dual (`ff6_vs_ff8`) matters because a prod reference can itself be worse/mispaired, producing
false failures in `compare_ff8`; a clean dual says the 6→8 change is not the cause.

---

## 2. Remote layout & naming conventions

Verified live against `setX`, 2026-07-28. Root:
`http://ny-www.kaltura.com/content/shared/tmp/qualityTest/TestBench.11/ff8tests/`
(internal host — reach by `curl` over http, not https/WebFetch; no dir index; a missing path
returns HTTP 200 size 0, an existing one supports Range → 206).

```
ff8tests/
  convert/<SET>/    per-session convert outputs, conversion logs, compare logs, per-set .res roll-ups
  data/             manifest CSV(s) = the planned-input population; also 1.cmd, ffmpeg_stats_output.md, old/
  docs/             redundant with git (this repo is canonical) — not maintained remotely
```

### Per session, under `convert/<SET>/` (session = `<entry>_<asset>`)

| file / dir | meaning |
|---|---|
| `convert_ff6_<session>.mp4` \| `.mp3` | our FF6 output (also resolves without the extension — Apache MultiViews) |
| `convert_ff6_<session>.conv.log` | FF6 conversion log |
| `convert_ff6_<session>_chunkenc/` | FF6 chunked-encode workdir |
| `convert_ff8_<session>.mp4` \| `.mp3` (+ `.conv.log`, `_chunkenc/`) | same, for FF8 |
| `compare_convert_ff6_<session>.log` | prod ref vs our FF6 (baseline) |
| `compare_convert_ff8_<session>.log` | prod ref vs our FF8 (**migration answer**) |
| `compare_convert_ff6_vs_convert_ff8_<session>.log` | our FF6 vs our FF8 (no prod) |

`.mp3` = audio-only flavor (VMAF is N/A for these).

### Per-set roll-ups (`.res`)

`grep RESULT …` of the per-session compare logs, one line per session — a fast whole-set scan.
Supplied per set (no fixed naming to pin here). All real detail lives in the per-session logs.

---

## 3. Local analysis record (this repo)

One folder per set, flat at the harness root; results are data, not prose:

```
work/ffmpeg-6to8/
  docs/ff8tests-analysis-plan.md    # this doc
  analyze_set.py                    # planned.csv + .res (+ logs) -> results.csv, idempotent upsert
  setX/
    objective.md                    # what this set targets, selection criteria, source-CSV range
    planned.csv                     # the planned session list (input)
    *.res                           # roll-ups supplied for the set
    results.csv                     # GENERATED: one row/session, phase column-groups, triage class
    findings.md                     # short: counts + the regressions worth attention
  setY/ ...
```

`results.csv` is the single source of truth per set — one row per session, keyed on `session`,
with column groups filled **incrementally** by phase (`conv_ff6`, `conv_ff8`, `cmp_ff6`,
`cmp_ff8`, `cmp_ff6v8`); phases not yet run = `pending` cells, not errors. `analyze_set.py`
merges by session and never clobbers columns it has no input for, so partial/per-phase analysis
is just "run with whatever inputs exist so far"; git history of `results.csv` gives the
phase-by-phase snapshots. Media/logs are **not** pulled local wholesale — pull the compact
`.res`, join with `planned.csv`, and fetch individual per-session logs only for failures needing
triage.

---

## 4. Acceptance & scoring model (from code review)

Grounded by reading the engine + driver + report tool directly. Sources:
- **Engine (authoritative gate):** `_zbale_/TestBench.11/test_kdl_compare.php`, `KDLTestBenchUtils.php`, `KMediaQualityMeasurement.php` + `…Utils.php` (these staged classes *are* the Kaltura quality-measurement code).
- **Driver:** `test_ffmpeg8.php`; operand wiring in `run_test_ffmpeg8.sh`.
- **Report:** `ffm8_report.py` — parses engine output, non-gating.

Every compare is **one** `runCompare` over **three** files: `source` (original), `f1` (= `file` / prod-or-ff6 `assetPath`), `f2` (= `file2` / new encode). The three compares (`compare_ff6`, `compare_ff8`, `compare_ff6_vs_ff8`) are this same routine with different f1/f2 pairings chosen by the shell wrapper; the PHP has no per-compare branch.

### 4.1 The gate

`RESULT:Success!!!` ⟺ inner `RESULT:OK`, which requires **ALL** (test_kdl_compare.php:182-186):

1. `anlys` (f1-vs-f2 metadata) has **zero** diffs, **AND**
2. SourceCompare grade ≠ `BAD`, **AND**
3. no `VMAF:BAD`, **AND**
4. no `PSNR:BAD`.

Binary AND, no severity — any one failure ⟹ `Failure!!!`. **CPU does not gate** (computed after the verdict is fixed: test_ffmpeg8.php:370 vs :389). It is a **parity** gate (is f2 as close to the reference as f1?), *not* an absolute-quality floor. **Field diffs are stricter than VMAF:** any non-null `anlys` diff fails, whereas VMAF fails only on `BAD`.

### 4.2 Metadata tolerances — `anlys` (f1 vs f2)

`$fieldsToCompare` (test_kdl_compare.php:61-88); operators in `compareObjects` (KDLTestBenchUtils.php:236-263). Equal values skip before tolerance; a surviving mismatch emits `diff<field:f1,f2>` and flips `anlys` to BAD.

| tolerance | fields |
|---|---|
| **5%** ratio | `videoBitRate` |
| **20%** ratio | `fileSize`, `containerBitRate`, `audioBitRate` |
| **500 ms** abs | `containerDuration`, `videoDuration`, `audioDuration` |
| **exact** | `containerFormat`, `containerId`, `videoFormat`, `videoCodecId`, `videoBitRateMode`, `videoWidth`, `videoHeight`, `videoFrameRate`, `videoDar`, `videoRotation`, `scanType`, `audioFormat`, `audioCodecId`, `audioChannels`, `audioSamplingRate`, `audioResolution` |
| **recurse** (same map) | `contentStreams` (per-stream) |

Ratio is **asymmetric** — divides by f1: `abs(1 − f2/f1) < crit`.

### 4.3 SourceCompare (source vs each operand)

test_kdl_compare.php:119-180. Uses a **smaller** field set: `{containerDuration, contentStreams, videoDuration, videoFrameRate, audioDuration}`. Per-operand grades `1st:`/`2nd:` (source-vs-f1, source-vs-f2), each OK/BAD. **Aggregate grade = string-equality of the two source-diff strings** (:154): equal → OK, differ → BAD — i.e. "does f2 diverge from source the *same way* f1 does," not a fidelity test. Never tests `videoDar` / `videoRotation` / `videoWidth`/`Height` / `containerId` (top-level or per-stream). Only aggregate BAD gates.

### 4.4 VMAF

`KMediaQualityMeasurement*.php`. Model `vmaf_v0.6.1.pkl`, subsample 5, `yuv420p`, `--thread 4`, mean pooling; driver caps to 30 s. Two independent layers:

- **Per-operand CLASS** (`GradePerFrameSize`, Utils:427-446) — bands 93 / 85 / 70 with a height-dependent `threshErr` floor → `EXEL / GOOD / SUFF / LOW / ERR`. **Informational; does not gate.**
- **VERDICT** (`DiffGrade`, Utils:246-260) — from the score gap of the two operands, `diffGood=3`, `diffOk=6`, `threshHigh=93`:
  - `scoreDiff < 3` → **GOOD**
  - `< 6` → **OK**
  - `≥ 6` **and both scores > 93** → **SUFF** (large gap, yet both still excellent)
  - else → **BAD** (the only value that gates)
  - **NA** when a side has no video (audio-only `.mp3`)

Parity, not floor. (Verdict vocabulary is GOOD/OK/SUFF/BAD/NA — SUFF is a *verdict* value, not just a class.)

### 4.5 PSNR — inert

`setup->psnr` unset → always `PSNR:NA`, never BAD (test_kdl_compare.php:143-144; QM:359-362). Skip in analysis.

### 4.6 CPU token — non-gating

`compareUserCpu` (test_ffmpeg8.php:402-432): ratio `cpu1/cpu2`, `eq` within 2%, `1st`/`2nd` by direction, `+` suffix when gap > 10% and both > 30. **`cpu1` = prod/f1, `cpu2` = ours/f2.** Emitted *after* the verdict → never gates. Present on video lines; **absent on audio** (both `userCpu` null).

### 4.7 Report tool — non-gating heuristics

`ffm8_report.py` (ffm8_report.py:298-445) parses the engine's RESULT/NOTICE strings, **takes them as truth**, and layers its *own* severity cascade + VMAF winner-margin deltas. It contributes **nothing** to pass/fail. Behaviors to keep in mind (frozen — see §5): it recomputes and **overwrites** the engine VMAF winner; `compare_reports` **hardcodes** report1=ff6 / report2=ff8 arg order (swap silently inverts the "incompatible" labels); no benign bucket for `videoDar`/`videoRotation`/`scanType`-only diffs → those fall to the "Unknown / no significant differences" fallback.

### 4.8 Triage taxonomy & cross-phase rule

Classes: real FF8 regression / benign-expected / test-infra artifact / N/A. **Clean dual** (`compare_ff6_vs_ff8`) ⇒ the 6→8 change is not the cause. Because f1/f2 share the flavor setup and differ only in the ffmpeg binary, a `videoDar` / `videoRotation` / `scanType` diff in the dual is an **unambiguous encoder-version signal** — surface it, never suppress.

*Still to write (process, not code):* session model & manifest-CSV schema (`~`-delimited) → `planned.csv`; the planned→executed→success/failure→quality-compliant matrix; the phased/incremental per-step workflow.

---

## 5. Open items

Deliberately not done yet — TODO / reminders.

### Action item

- **containerId brand-family grouping** — in **our triage layer** (not the engine/parser), treat container brands as one equivalence family (`isom` / `mp41` / `mp42` / `mp4v` / `iso2` / `dash` / …) so a `containerId`-only diff is classified **benign**, not a regression. It otherwise differs on nearly every prod-vs-ff8 line and inflates the failure count. (The parser reports the true brand correctly — no operational-code change.)

### Owed after the P-review (deferred)

1. **Systematic-drift demo** — the gate tests only VMAF *parity* (closeness within 3/6), never an absolute floor, so a small, consistent **set-wide** VMAF drop stays invisible: each rendition passes parity while the whole set drifts down. Demo = cross-set aggregate stats on the **raw** VMAF scores to expose it. *(Origin: P1 "no absolute-quality floor" → surfaced at P4.)*
2. **prod `.conv.log`** — largely resolved: `compare_ff6.res` shows prod-vs-ff6 **video** lines carry `CPU:type,cpu1,cpu2` (cpu1 = prod, numeric) ⇒ a readable `.conv.log` exists beside the prod flavor. Open only for **audio** — confirm and close.
3. **Audio has no CPU token — test why** — `.mp3` compares emit no CPU token (both `userCpu` null). Determine whether the `.conv.log` is missing beside the prod flavor, beside our audio output, or simply lacks a `RESULT:Success!…cpu:` line. CPU is non-gating regardless.

### Frozen (not now)

- `ffm8_report.py` corrections — VMAF winner recompute/overwrite; `compare_reports` hardcoded report1=ff6 / report2=ff8 arg order.
