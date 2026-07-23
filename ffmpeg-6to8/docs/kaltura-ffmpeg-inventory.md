# Kaltura FFmpeg/FFprobe Usage Inventory

> Source: `kaltura/server` repo (scanned 2026-06-06)
> Purpose: regression-check input when upgrading FFmpeg versions.
> Version-agnostic — compare against changelogs for your specific version gap.

---

## 1. Video Encoders

- libx264
- libx265
- libvpx (VP8)
- libvpx-vp9
- libaom-av1
- mpeg2video
- mpeg4
- dvvideo
- flv
- libtheora
- wmv2
- copy

## 2. Audio Encoders

- libfdk_aac
- aac (native)
- libmp3lame
- libfaac
- libvorbis
- libopencore_amrnb
- mp2
- pcm_s16le
- wmav2
- copy

## 3. Video Filters

- scale
- fade
- crop
- overlay
- rotate
- yadif (deinterlace)
- subtitles
- setsar
- blackdetect

## 4. Audio Filters

- aresample (incl. async= resampling)
- amerge
- amix
- pan
- loudnorm
- volume
- channelsplit

## 5. lavfi Synthetic Sources

- `movie` — scene detection via `select=gt(scene,.4)`
- `amovie` + `astats` — audio loudness measurement

## 6. Muxers / Container Formats

- mp4
- mov
- mpegts
- matroska
- flv
- hls (`-hls_time`, `-hls_list_size`)
- ismv (Smooth Streaming)
- segment (`-segment_time`, `-segment_format`, `-segment_frames`, `-segment_list`, `-segment_start_number`)
- concat (demuxer: `-f concat -safe 0`)
- webm
- ogg
- mpeg
- wav
- mxf
- yuv4mpegpipe
- rawvideo
- s16le
- null

## 7. FFmpeg CLI Flags Used

### Input / Output
- `-i`
- `-y`
- `-f <format>`

### Video Codec
- `-c:v` / `-vcodec`
- `-vn`

### Audio Codec
- `-c:a` / `-acodec`
- `-an`

### Video Rate Control
- `-b <bitrate>k` (legacy — should be `-b:v`)
- `-crf`
- `-minrate`, `-maxrate`, `-bufsize`
- `-bt`
- `-qmin`, `-qmax`, `-qcomp`, `-qdiff`
- `-pass`, `-passlogfile`, `-fastfirstpass`

### Video Settings
- `-s <WxH>`
- `-r <fps>`
- `-g <gop>`
- `-aspect`
- `-pix_fmt` (yuv420p, yuv422p, yuv422p10le)
- `-vf`
- `-frames:v` / `-vframes`
- `-bf`
- `-sc_threshold`
- `-force_key_frames` (expr, source)
- `-tag:v`
- `-noautorotate`
- `-profile:v`
- `-level`

### Audio Settings
- `-ab <bitrate>k` (legacy — should be `-b:a`)
- `-b:a`
- `-ar <sample_rate>`
- `-ac <channels>`
- `-vol`

### Timing / Seeking
- `-ss`
- `-t`
- `-to`
- `-copyts`
- `-itsoffset`

### Sync
- `-vsync` (0/passthrough, 1/cfr, 2/vfr, -1/auto)
- `-async` (deprecated — converted to aresample filter)

### Filters
- `-filter_complex`

### Muxer-Specific Options
- `-movflags +faststart`
- `-movflags +frag_keyframe`
- `-min_frag_duration`
- `-write_btrt 0`
- `-hls_time`
- `-hls_list_size`
- `-segment_time`
- `-segment_format`
- `-segment_frames`
- `-segment_list`
- `-segment_start_number`
- `-mpegts_copyts`

### Codec-Specific Params
- `-x264opts <key:val:...>` (deprecated — use `-x264-params`)
- `-x265-params <key=val:...>`
- `-flags +loop+mv4`
- `-coder`
- `-refs`
- `-subq`
- `-sws`
- `-me_range`
- `-keyint_min`

### Stream Mapping
- `-map`
- `-map_channel` (deprecated in FFmpeg 6+)
- `-bsf:v`
- `-bsf:a`

### Threading / Buffering
- `-threads`
- `-probesize`
- `-analyzeduration`

### Network / Protocol
- `-protocol_whitelist`
- `-safe`
- `ffmpeg_reconnect_params` (runtime-injected, contents vary)

### Encryption
- `-decryption_key`
- `-encryption_key`
- `-encryption_kid`
- `-encryption_scheme`

### Misc
- `-initial_offset`
- `-target` (ntsc-dv, pal-dv)

## 8. FFprobe Invocation Patterns

### Primary (JSON output)
```
ffprobe -i <file> -show_streams -show_format -show_programs -v quiet -show_data -print_format json
```

### Frame analysis (CSV)
```
ffprobe -show_frames -select_streams v -of csv \
  -show_entries frame=pkt_pts_time,pts_time,pkt_duration_time,pkt_pos,pkt_size,pict_type,coded_picture_number,interlaced_frame \
  -v quiet
```

### Frame analysis (JSON)
```
ffprobe <file> -show_frames -select_streams v -v quiet -of json \
  -show_entries frame=pkt_pts_time,pts_time,key_frame,coded_picture_number
```

### Frame analysis (default format)
```
ffprobe -show_frames -select_streams v -of default=nk=1:nw=1 \
  -f lavfi "movie=<file>,select=gt(scene,.4)" \
  -show_entries frame=pkt_pts_time,pts_time
```

### Audio loudness (lavfi)
```
ffprobe -f lavfi -i "amovie=<file>,astats=metadata=1:reset=<N>" \
  -show_entries frame=pkt_pts_time,pts_time:frame_tags=lavfi.astats.Overall.RMS_level \
  -of csv=p=0 -v quiet
```

### Interlace detection (piped)
```
ffmpeg ... -f matroska -y -v quiet - | \
  ffprobe -show_frames -select_streams v - -of csv \
  -show_entries frame=interlaced_frame,pkt_pts_time,pts_time,top_field_first | head -10
```

## 9. FFprobe Fields Parsed

### Stream-level (from -show_streams JSON)
- codec_name
- codec_type
- codec_tag_string
- profile
- level
- width, height
- pix_fmt
- display_aspect_ratio
- r_frame_rate
- avg_frame_rate
- duration
- bit_rate
- sample_rate
- channels
- channel_layout
- bits_per_sample
- color_space
- color_transfer
- color_primaries
- side_data_list
- extradata
- tags (incl. rotate/rotation)

### Format-level (from -show_format JSON)
- format_name
- duration
- size
- bit_rate

### Frame-level (from -show_frames)
- pkt_pts_time
- pts_time
- pkt_duration_time
- pkt_pos
- pkt_size
- pict_type
- coded_picture_number
- interlaced_frame
- top_field_first
- key_frame

## 10. Implicit Defaults Relied On (Not Explicitly Set)

| Area | What's missing | Risk on upgrade |
|------|---------------|-----------------|
| Color | No `-color_range` set | Default changed in FFmpeg 7+ for some codecs |
| Threads | Some paths don't set `-threads` | Default thread count algo changes between versions |
| Pixel format | Not always explicit | Auto-negotiation may pick different format |
| GOP | Falls back to `DefaultGOP = 60` constant | If not passed, ffmpeg's own default applies |
| Vsync | Numeric values (0,1,2,-1) | Numeric deprecated since FFmpeg 6; already mitigated in code |
| Bitrate syntax | `-b` without stream specifier | Ambiguous — may warn or error |
| Audio bitrate | `-ab` instead of `-b:a` | Legacy alias — may be removed |
| Reconnect | Runtime config injection | Unknown params, could conflict with new defaults |
| Concat | Raw mpegts concat for H264/H265 | Assumes consistent NAL packaging across versions |

## 11. Already-Mitigated Deprecations (in KDLOperatorFfmpeg6_0)

- `-deinterlace` → `-vf yadif`
- `-vsync <number>` → `-vsync <name>` (passthrough/cfr/vfr/auto)
- `-async` → `aresample=async=1:min_hard_comp=0.1:first_pts=0`
- filter_complex stream mapping ambiguity → named outputs `[vout]`/`[aout]` + explicit `-map`
- `-write_btrt 0` added for mp4/mov outputs

## 12. Chunked Encode Specifics

- Supported codecs: libx264, libx265, h264, h264b, h264m, h264h, h265, libvpx-vp9, vp9, libaom-av1, av1
- VP9/AV1 chunks: mp4 format + demuxer concat
- H264/H265 chunks: mpegts format + raw concat
- Enforces `-vsync cfr` (required for chunked)
- Thread control: decode 5-7 threads, encode 2-4 threads (AV1 gets 2)
- Multi-pass: supported (x264opts zones, x265-params zones)
- Max duration inaccuracy: 100ms
