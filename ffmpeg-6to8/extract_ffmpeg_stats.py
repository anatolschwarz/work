#!/usr/bin/env python3
"""
Extract ffmpeg usage statistics from Kaltura command-line dump.
Input: ~-delimited file with PHP-serialized cmd_lines in field 8 (0-indexed: 7).
Output: frequency-ranked inventory of flags, codecs, filters, values, deprecated usage.
"""

import sys
import re
from collections import Counter, defaultdict
from pathlib import Path

# --- Config ---
INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else None
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else "ffmpeg_stats_output.md"

if not INPUT_FILE:
    print("Usage: python3 extract_ffmpeg_stats.py <input_file> [output_file]")
    print("  input_file:  the ~-delimited dump")
    print("  output_file: defaults to ffmpeg_stats_output.md")
    sys.exit(1)

# --- Counters ---
total_lines = 0
total_cmds = 0
codec_video = Counter()
codec_audio = Counter()
filters_video = Counter()
filters_audio = Counter()
flags = Counter()
flag_values = defaultdict(Counter)  # flag -> value -> count
formats = Counter()
resolutions = Counter()
framerates = Counter()
pix_fmts = Counter()
profiles = Counter()
deprecated_flags = Counter()
x264opts_values = Counter()
x265params_values = Counter()
force_kf_exprs = Counter()
movflags_values = Counter()
thread_counts = Counter()
crf_values = Counter()
gop_values = Counter()

# Flags known to be deprecated/removed in FFmpeg 6+
DEPRECATED = {
    '-deinterlace', '-async', '-map_channel', '-rc_eq',
    '-x264opts',  # replaced by -x264-params
    '-vcodec', '-acodec',  # legacy aliases
}

# --- Extract cmdlines from PHP serialized field ---
CMD_PATTERN = re.compile(r'"([^"]+?);;;FS"')

def extract_cmds(field):
    return CMD_PATTERN.findall(field)

def is_ffmpeg_cmd(cmd):
    """Filter out MEncoder commands (contain -ovc, -oac, -of, -ofps, -x264encopts, etc.)."""
    tokens = cmd.split()
    mencoder_markers = {'-ovc', '-oac', '-of', '-ofps', '-lavfopts', '-faacopts', '-x264encopts'}
    return not mencoder_markers.intersection(tokens)

# --- Parse a single command line ---
FLAG_PATTERN = re.compile(r'-[\w:]+')

def is_flag(tok):
    """Return True if token looks like an ffmpeg flag (not a negative number or value)."""
    if not tok.startswith('-'):
        return False
    # Negative numbers: -1, -0.5, etc.
    if re.match(r'^-\d+(\.\d+)?$', tok):
        return False
    # Must start with - followed by a letter
    if len(tok) < 2 or not tok[1].isalpha():
        return False
    return True

# Known flags whose value starts with '-' (to avoid skipping it)
FLAGS_WITH_NEGATIVE_VALUES = {'-map_chapters', '-map_metadata', '-map'}

def parse_cmd(cmd):
    global total_cmds
    total_cmds += 1

    tokens = cmd.split()
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if not is_flag(tok) or tok == '-i' or tok == '-y':
            i += 1
            continue

        flags[tok] += 1

        if tok in DEPRECATED:
            deprecated_flags[tok] += 1

        # Grab value (next token if not another flag, or if current flag expects negative values)
        val = None
        if i + 1 < len(tokens):
            next_tok = tokens[i+1]
            if tok in FLAGS_WITH_NEGATIVE_VALUES or not is_flag(next_tok):
                val = next_tok
                # Skip special placeholders
                if val in ('__inFileName__', '__outFileName__'):
                    val = None

        if val:
            flag_values[tok][val] += 1

        # Specific extractions
        if tok == '-c:v' or tok == '-vcodec':
            if val:
                codec_video[val] += 1
        elif tok == '-c:a' or tok == '-acodec':
            if val:
                codec_audio[val] += 1
        elif tok == '-f':
            if val:
                formats[val] += 1
        elif tok == '-s':
            if val:
                resolutions[val] += 1
        elif tok == '-r':
            if val:
                framerates[val] += 1
        elif tok == '-pix_fmt':
            if val:
                pix_fmts[val] += 1
        elif tok == '-vprofile' or tok == '-profile:v':
            if val:
                profiles[val] += 1
        elif tok == '-crf':
            if val:
                crf_values[val] += 1
        elif tok == '-g':
            if val:
                gop_values[val] += 1
        elif tok == '-threads':
            if val:
                thread_counts[val] += 1
        elif tok == '-x264opts':
            if val:
                x264opts_values[val] += 1
        elif tok == '-x265-params':
            if val:
                x265params_values[val] += 1
        elif tok == '-force_key_frames':
            if val:
                force_kf_exprs[val] += 1
        elif tok == '-movflags':
            if val:
                movflags_values[val] += 1
        elif tok == '-filter_complex':
            if val:
                parse_filters(val)
        elif tok == '-vf':
            if val:
                parse_vf(val)

        i += 1

def parse_filters(val):
    """Extract filter names from -filter_complex value."""
    clean = val.strip("'\"")
    # Split filter chain by semicolons (chain separators)
    chains = clean.split(';')
    for chain in chains:
        # Remove stream labels like [0:v], [aout], [vout], [vflt0], etc.
        chain = re.sub(r'\[[^\]]*\]', ' ', chain).strip()
        # Split by commas (filter separators within a chain)
        parts = chain.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Filter name is before the first '='
            match = re.match(r'([a-z_][a-z0-9_]*)', part)
            if match:
                name = match.group(1)
                # Skip common non-filter tokens (stream labels, format specs)
                if name in ('i', 'v', 'a', 's', 'f', 'p'):
                    continue
                # Skip named output labels that leaked through
                if re.match(r'^(aout|vout|aflt\d*|vflt\d*|overlayed\d*|watermarked|wmimg\d*)$', name):
                    continue
                # Classify
                if name in ('aresample', 'amerge', 'amix', 'pan', 'loudnorm',
                            'volume', 'channelsplit', 'afade', 'aformat'):
                    filters_audio[name] += 1
                else:
                    filters_video[name] += 1

def parse_vf(val):
    """Extract filter names from -vf value."""
    clean = val.strip("'\"")
    parts = re.split(r'[,;]', clean)
    for p in parts:
        match = re.match(r'([a-z_][a-z0-9_]*)', p.strip())
        if match:
            filters_video[match.group(1)] += 1

# --- Main ---
print(f"Reading: {INPUT_FILE}")
with open(INPUT_FILE, 'r', errors='replace') as fh:
    for line in fh:
        total_lines += 1
        fields = line.split('~')
        if len(fields) < 8:
            continue
        cmd_field = fields[7]
        cmds = extract_cmds(cmd_field)
        # Deduplicate within same entry (flavors 92/2/99 are often identical)
        seen = set()
        for cmd in cmds:
            cmd_stripped = cmd.strip()
            if cmd_stripped and cmd_stripped not in seen and is_ffmpeg_cmd(cmd_stripped):
                seen.add(cmd_stripped)
                parse_cmd(cmd_stripped)

        if total_lines % 100000 == 0:
            print(f"  ...processed {total_lines:,} lines, {total_cmds:,} commands")

print(f"Done: {total_lines:,} lines, {total_cmds:,} total commands extracted\n")

# --- Output ---
def top(counter, n=30):
    lines = []
    for item, count in counter.most_common(n):
        pct = 100.0 * count / total_cmds if total_cmds else 0
        lines.append(f"| {item} | {count:,} | {pct:.1f}% |")
    return lines

with open(OUTPUT_FILE, 'w') as out:
    out.write(f"# FFmpeg Command-Line Statistics\n\n")
    out.write(f"> Source: {Path(INPUT_FILE).name}\n")
    out.write(f"> Lines: {total_lines:,} | Unique commands parsed: {total_cmds:,}\n\n")
    out.write("---\n\n")

    out.write("## 1. Video Codecs (frequency)\n\n")
    out.write("| Codec | Count | % |\n|-------|------:|---:|\n")
    out.write('\n'.join(top(codec_video)) + '\n\n')

    out.write("## 2. Audio Codecs (frequency)\n\n")
    out.write("| Codec | Count | % |\n|-------|------:|---:|\n")
    out.write('\n'.join(top(codec_audio)) + '\n\n')

    out.write("## 3. Output Formats (frequency)\n\n")
    out.write("| Format | Count | % |\n|--------|------:|---:|\n")
    out.write('\n'.join(top(formats)) + '\n\n')

    out.write("## 4. Video Filters (frequency)\n\n")
    out.write("| Filter | Count | % |\n|--------|------:|---:|\n")
    out.write('\n'.join(top(filters_video)) + '\n\n')

    out.write("## 5. Audio Filters (frequency)\n\n")
    out.write("| Filter | Count | % |\n|--------|------:|---:|\n")
    out.write('\n'.join(top(filters_audio)) + '\n\n')

    out.write("## 6. Resolutions (top 30)\n\n")
    out.write("| Resolution | Count | % |\n|------------|------:|---:|\n")
    out.write('\n'.join(top(resolutions)) + '\n\n')

    out.write("## 7. CRF Values\n\n")
    out.write("| CRF | Count | % |\n|-----|------:|---:|\n")
    out.write('\n'.join(top(crf_values)) + '\n\n')

    out.write("## 8. GOP (-g) Values\n\n")
    out.write("| GOP | Count | % |\n|-----|------:|---:|\n")
    out.write('\n'.join(top(gop_values)) + '\n\n')

    out.write("## 9. Frame Rates\n\n")
    out.write("| FPS | Count | % |\n|-----|------:|---:|\n")
    out.write('\n'.join(top(framerates)) + '\n\n')

    out.write("## 10. Pixel Formats\n\n")
    out.write("| Format | Count | % |\n|--------|------:|---:|\n")
    out.write('\n'.join(top(pix_fmts)) + '\n\n')

    out.write("## 11. Profiles\n\n")
    out.write("| Profile | Count | % |\n|---------|------:|---:|\n")
    out.write('\n'.join(top(profiles)) + '\n\n')

    out.write("## 12. Thread Counts\n\n")
    out.write("| Threads | Count | % |\n|---------|------:|---:|\n")
    out.write('\n'.join(top(thread_counts)) + '\n\n')

    out.write("## 13. x264opts Values\n\n")
    out.write("| Opts | Count | % |\n|------|------:|---:|\n")
    out.write('\n'.join(top(x264opts_values)) + '\n\n')

    out.write("## 14. x265-params Values\n\n")
    out.write("| Params | Count | % |\n|--------|------:|---:|\n")
    out.write('\n'.join(top(x265params_values)) + '\n\n')

    out.write("## 15. force_key_frames Expressions\n\n")
    out.write("| Expression | Count | % |\n|------------|------:|---:|\n")
    out.write('\n'.join(top(force_kf_exprs)) + '\n\n')

    out.write("## 16. movflags Values\n\n")
    out.write("| Flags | Count | % |\n|-------|------:|---:|\n")
    out.write('\n'.join(top(movflags_values)) + '\n\n')

    out.write("## 17. All Flags (top 50)\n\n")
    out.write("| Flag | Count | % |\n|------|------:|---:|\n")
    out.write('\n'.join(top(flags, 50)) + '\n\n')

    out.write("## 18. DEPRECATED Flags Still in Use\n\n")
    out.write("| Flag | Count | % | Replacement |\n|------|------:|---:|-------------|\n")
    replacements = {
        '-deinterlace': '-vf yadif',
        '-async': 'aresample filter',
        '-map_channel': 'pan / channelmap filter',
        '-rc_eq': 'removed (no-op in recent ffmpeg)',
        '-x264opts': '-x264-params',
        '-vcodec': '-c:v',
        '-acodec': '-c:a',
    }
    for flag, count in deprecated_flags.most_common():
        pct = 100.0 * count / total_cmds if total_cmds else 0
        repl = replacements.get(flag, '?')
        out.write(f"| {flag} | {count:,} | {pct:.1f}% | {repl} |\n")
    out.write('\n')

    # Flags never seen (from inventory)
    expected_with_source = {
        '-color_range': 'never set on encode; only read from ffprobe output',
        '-color_primaries': 'never set on encode; only read from ffprobe output',
        '-color_trc': 'never set on encode; only read from ffprobe output',
        '-colorspace': 'never set on encode; only read from ffprobe output',
        '-max_muxing_queue_size': 'set in encode commands (check parser if missing)',
        '-probesize': 'used in chunked encode concat phase, not per-flavor encode',
        '-analyzeduration': 'used in chunked encode concat phase, not per-flavor encode',
        '-protocol_whitelist': 'used in chunked encode demuxer concat, not per-flavor encode',
        '-safe': 'used in chunked encode demuxer concat (-f concat -safe 0)',
        '-segment_format': 'used in HLS/segment muxer paths; not in mp4 encode commands',
    }
    never_seen = {k: v for k, v in expected_with_source.items() if k not in flags}
    if never_seen:
        out.write("## 19. Expected Flags NEVER Seen in Commands\n\n")
        out.write("These flags exist in the codebase but did not appear in the encode command lines.\n")
        out.write("Explanation of where they actually come from:\n\n")
        out.write("| Flag | Source |\n|------|--------|\n")
        for f in sorted(never_seen):
            out.write(f"| `{f}` | {never_seen[f]} |\n")
        out.write('\n')

print(f"Output written to: {OUTPUT_FILE}")
