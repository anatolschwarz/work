# SUP-52853-WebM-aspect-ratio

Support case **SUP-52853** — WebM rendition comes out with the wrong aspect ratio /
transposed frame size. Root-caused 2026-07-21.

## Symptom
- **Portrait** source → the **webm** flavor is emitted **landscape/transposed**; every other
  flavor is correct.
- Repro asset: entry `1_nxncz9fn` (iOS ReplayKit HEVC screen recording).
  - Source: **670×1192** portrait (DAR ≈ 0.562, ~9:16), HEVC, no rotation tag.
  - webm out (`1_nxncz9fn_1_ot168rao`, flavor id 487111): VP8 **640×360** landscape, SAR 1:1 /
    DAR 16:9 → picture squished; that's 360×640 with W/H **transposed**.
  - correct sibling (`1_nxncz9fn_1_ahz3t32u`, flavor id 301991): mpeg4/3gp **176×320** portrait ✓.
- Assets/logs: `~/Downloads/1_nxncz9fn_source.mp4`, `..._ot168rao.webm|.log`, `..._ahz3t32u.log`
  (Win Downloads; MobaXterm session copies rotate).

## Root cause (FOUND)
`infra/cdl/kdl/KDLFlavor.php` → `evaluateTargetVideoFramesize()`.
- Portrait sources are handled by **invert → fit-as-landscape → invert-back** (invert at ~L963
  sets `$invertedVideo=true`; invert-back at **L1195–1201**).
- The mod-16 block (**L1177–1187**) has an early **`return;` (L1185)** that fires when the
  computed size is a hardcoded "industry-standard" (640×360 / 480×360 / 1920×1080) **and** the
  codec is **not** H264/H265 (`$auxTargets`). That `return` was meant to skip only the mod-16
  rounding, but it **exits the whole function**, so the **invert-back never runs** → target
  left landscape.
- Only webm trips it here: VP8 (`_id` set at L847) isn't in `$auxTargets`, and the webm flavor
  lands exactly on **640×360**. mpeg4 → 176×320 (never enters the block). H264/H265 → get
  `$modVal=2`, no return. So the bug hits any **non-H264/H265** flavor whose target computes to
  640×360 / 480×360 / 1920×1080 from a portrait (inverted) source.

## The fix — TWO equivalent candidate files (both drop-in for `infra/cdl/kdl/KDLFlavor.php`)
Both make the mod-16 block fall through to the invert-back instead of `return`-ing, so portrait
sources are inverted back for every codec. Behaviorally identical (same `matchBest` call matrix:
mod-16 for normal sizes, mod-2 for H264/H265 at standard sizes, **skipped** for non-H264 standard
sizes like webm 640×360 → preserved → invert-back → 360×640). Verified vs. kaltura/server default
branch; **not built/transcode-tested; `php -l` not run (no PHP locally).**
- **`KDLFlavor.php`** — flag version: `return;` → `$skipModConstraint = true;` + guard the single
  `matchBest` call. Keeps one call site.
- **`KDLFlavor.elsefix.php`** — else-branch version (user's preferred structure): `matchBest`
  called inside the H264 inner-`if` and in an `else` for the `CONDITION`-false path; the non-H264
  standard-size path calls nothing. Two call sites; brace-less `else`.

Neither is marked canonical — pick one to deploy. (No `.patch` kept, by request.)

## Repo / how to work
- Analysis clone (throwaway): `/tmp/kaltura-server` (shallow, default branch). Re-clone if gone;
  do NOT edit it — patch is authored by reading it.
- KDL cmd-line generation: `infra/cdl/kdl/` (dimension math = `KDLFlavor.php`; per-codec cmd =
  `KDLOperatorFfmpeg*.php`). Convert plugin just token-substitutes the built line.

## Status (2026-07-22)
- Root cause found (2026-07-21). Two equivalent candidate fixes written & reviewed (2026-07-22):
  `KDLFlavor.php` (flag) + `KDLFlavor.elsefix.php` (else-branch). Both verified logically vs. the
  clone; neither built, transcode-tested, or `php -l`'d (no PHP locally).
- **Next:** pick one candidate → build/transcode the repro asset and confirm webm comes out
  360×640; `git blame` KDLFlavor.php ~L1185 for when the `return` was introduced; decide upstream
  PR vs local-fork delivery.
