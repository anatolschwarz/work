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

## 4. Methodology — to be written

- **Session model & data inputs** — manifest CSV schema (`~`-delimited), building `planned.csv`.
- **Analysis matrix** — planned → executed → success/failure → quality-compliant.
- **VMAF verdict/class grammar** — verdict (GOOD/OK/BAD/NA) vs class (EXEL/GOOD/SUFF/LOW); PSNR inactive.
- **Metadata-diff grammar** — `diff<metric:a,b>`, SourceCompare, CPU tokens.
- **Triage taxonomy** — real FF8 regression / benign-expected / test-infra artifact / N/A; cross-phase rule (clean dual ⇒ not a migration regression).
- **Phased/incremental workflow** — running analysis per convert/compare step.
