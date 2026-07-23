# FFmpeg/FFprobe 4.4 to 6.0 Migration Guide

## 1. Command Line Changes

### Changed Option Names/Syntax

#### Video Encoding/Decoding
- `-vcodec` is now fully deprecated in favor of `-c:v`
- `-preset veryslow` has been removed from x264/x265, use `slower` instead
- `-profile:v` now requires explicit codec prefix for H.264/HEVC (e.g., `-profile:v high` → `-profile:v h264_high`)
- New syntax for HDR metadata: `-color_primaries`, `-color_trc`, `-color_space` replace older variants
- GOP size options now use frames instead of seconds by default

#### Audio Processing
- `-acodec` is fully deprecated in favor of `-c:a`
- Channel layout specification changed:
  - Old: `-ac 6 -channel_layout 5.1`
  - New: `-ch_layout 5.1` or `-ch_layout surround(side)`
- Filter options requiring channel counts now use new syntax:
  ```
  # Old
  -af "pan=stereo|c0=FL|c1=FR"
  
  # New
  -af "pan=stereo|FL=c0|FR=c1"
  ```

#### Hardware Acceleration
- CUDA options unified under `-hwaccel cuda`:
  ```
  # Old
  -c:v h264_cuvid -c:v h264_nvenc
  
  # New
  -hwaccel cuda -c:v h264_nvenc
  ```
- VA-API options now require explicit device selection:
  ```
  # Old
  -vaapi_device /dev/dri/renderD128
  
  # New
  -init_hw_device vaapi=va:/dev/dri/renderD128
  ```
- AMF encoder options reorganized:
  - Quality presets renamed (`quality` → `preset_quality`)
  - Rate control modes consolidated

#### Container Formats
- MOV/MP4 fast start option changed:
  ```
  # Old
  -movflags faststart
  
  # New
  -movflags +faststart
  ```
- Segment format options now require explicit initialization:
  ```
  # Old
  -f segment -segment_time 10
  
  # New
  -f segment -segment_time 10 -segment_format_options reset_timestamps=1
  ```

#### Metadata Handling
- Global metadata now requires explicit target:
  ```
  # Old
  -metadata title="My Video"
  
  # New
  -metadata:g title="My Video"
  ```
- Stream-specific metadata syntax changed:
  ```
  # Old
  -metadata:s:v:0 language=eng
  
  # New
  -metadata:s:v:0:language eng
  ```

#### Stream Mapping
- Complex filter map syntax changed:
  ```
  # Old
  -filter_complex "[0:v][1:v]overlay[out]" -map "[out]"
  
  # New
  -filter_complex "[0:v][1:v]overlay,split[out]" -map "[out]"
  ```
- Stream selection behavior changed:
  - Default stream selection is more strict
  - Automatic stream mapping requires explicit `-map 0`

### New Default Behaviors
- Thread count now defaults to logical CPU cores instead of physical cores
- Pixel format selection prefers higher bit depth
- Audio sample format defaults to float for processing
- Buffer sizes automatically adjusted based on input
- Error resilience enabled by default for network sources

## 2. FFprobe Output Changes

### JSON Format Structure

#### Channel Layout Changes
```json
// Old Format
{
  "channels": 6,
  "channel_layout": "5.1"
}

// New Format
{
  "channels": 6,
  "channel_layout": {
    "type": "surround",
    "layout": "5.1",
    "channels": [
      {"type": "FL", "index": 0},
      {"type": "FR", "index": 1},
      {"type": "FC", "index": 2},
      {"type": "LFE", "index": 3},
      {"type": "SL", "index": 4},
      {"type": "SR", "index": 5}
    ]
  }
}
```

#### Color Space Information
```json
// Old Format
{
  "color_space": "bt709",
  "color_transfer": "bt709",
  "color_primaries": "bt709"
}

// New Format
{
  "color_space": {
    "name": "bt709",
    "details": {
      "primaries": "bt709",
      "transfer": "bt709",
      "matrix": "bt709",
      "range": "tv",
      "location": "left"
    }
  }
}
```

#### Frame Rate Reporting
```json
// Old Format
{
  "r_frame_rate": "30000/1001",
  "avg_frame_rate": "30000/1001"
}

// New Format
{
  "frame_rate": {
    "raw": "30000/1001",
    "calculated": 29.97,
    "mode": "cfr",
    "variation": 0.0001
  }
}
```

### Changed Field Formats/Types
- Duration now includes microsecond precision
- Timestamps use nanosecond resolution
- Bitrates reported in bits/second instead of kilobits
- Packet sizes include padding information
- Frame types include more detailed information

### Stream Side Data
New fields added:
- Display matrix
- Mastering display metadata
- Content light level
- Ambient viewing environment
- Dynamic HDR information

## 3. Behavioral Changes

### Thread Management
- Default thread count calculation changed
- Thread type selection more aggressive
- Frame-threading preferred over slice-threading
- Hardware decoder threading isolated

### Memory Handling
- Buffer sizes dynamically adjusted
- Memory pools implemented for hardware operations
- Cached frame management improved
- Memory alignment requirements stricter

### Error Reporting
- More detailed error messages
- Warning levels adjustable
- Performance warnings added
- Hardware acceleration errors more specific

### Hardware Acceleration
- CUDA:
  ```
  # Old behavior
  - Single GPU context
  - Limited memory management
  
  # New behavior
  - Multi-GPU support
  - Intelligent memory pooling
  - Dynamic load balancing
  ```

- VA-API:
  ```
  # Old behavior
  - Limited HDR support
  - Single device context
  
  # New behavior
  - Full HDR pipeline
  - Multi-device support
  - Surface sharing
  ```

## 4. Required Migration Actions

### Command Line Updates
1. Review and update all hardware acceleration parameters
2. Modify channel layout specifications
3. Update metadata handling syntax
4. Revise stream mapping logic
5. Update filter graphs for new syntax

### Script Modifications
1. Parse FFprobe JSON with new structure handling
2. Update thread count calculations
3. Modify error handling logic
4. Revise memory management code
5. Update progress parsing

### Testing Scenarios
1. Verify hardware acceleration paths:
   ```bash
   # Test CUDA pipeline
   ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i input.mp4 -c:v h264_nvenc output.mp4
   
   # Test VA-API pipeline
   ffmpeg -hwaccel vaapi -hwaccel_output_format vaapi -i input.mp4 -c:v h264_vaapi output.mp4
   ```

2. Test channel layout handling:
   ```bash
   # Test surround sound processing
   ffmpeg -i input.mkv -ch_layout 5.1 -c:a aac -b:a 384k output.mkv
   ```

3. Verify metadata handling:
   ```bash
   # Test metadata preservation
   ffmpeg -i input.mp4 -map_metadata 0 -metadata:g title="New Title" output.mp4
   ```

### Backward Compatibility
- Maintain parallel 4.4 installation for legacy workflows
- Document version-specific command lines
- Implement version detection in scripts
- Create compatibility wrappers where needed
- Test with both versions during transition

## Critical Breaking Changes

1. Channel Layout Specification
   - All channel layout parameters must be updated
   - No automatic fallback to old syntax

2. Hardware Acceleration
   - CUDA context handling changed
   - VA-API device specification mandatory

3. Filter Graph Syntax
   - Some filter options renamed
   - Stricter validation of filter chains

4. Stream Selection
   - Default stream mapping more restrictive
   - Explicit mapping often required

5. Metadata Handling
   - Global metadata requires explicit target
   - Stream-specific metadata format changed

## Implementation Timeline

1. Immediate Actions
   - Update hardware acceleration parameters
   - Modify channel layout specifications
   - Revise metadata handling

2. Short-term Changes
   - Update filter graphs
   - Modify stream mapping
   - Revise thread handling

3. Long-term Updates
   - Implement new features
   - Optimize for new defaults
   - Remove deprecated syntax

## Testing and Verification

Create test cases for:
1. Hardware acceleration paths
2. Audio channel layouts
3. Metadata preservation
4. Stream mapping
5. Filter graphs
6. Error handling
7. Performance metrics

Document all test results and maintain version-specific command lines for reference.
