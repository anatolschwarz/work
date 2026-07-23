#!/usr/bin/env python3
import re
import csv
import os
import sys
from collections import defaultdict

# Field names as they appear in the log file
KNOWN_FIELDS = {
    'fileSize', 'containerDuration', 'videoDuration', 'audioDuration',
    'videoBitRate', 'containerBitRate', 'audioBitRate', 'containerId',
    'containerFormat', 'videoFrameRate', 'videoDar', 'videoWidth', 'videoHeight'
}

def find_new_fields(raw_differences):
    """
    Extract field names from diff sections and identify unknown ones
    
    Args:
        raw_differences (str): Raw difference string from log entry
        
    Returns:
        set: Set of field names not present in KNOWN_FIELDS
    """
    if not raw_differences:
        return set()
    all_fields = set(re.findall(r'diff<([^:]+):', raw_differences))
    return all_fields - KNOWN_FIELDS

def find_all_diff_fields(raw_differences):
    """
    Extract all field names from diff sections
    
    Args:
        raw_differences (str): Raw difference string from log entry
        
    Returns:
        set: Set of all field names found in diff<field:value> patterns
    """
    if not raw_differences:
        return set()
    return set(re.findall(r'diff<([^:]+):', raw_differences))

def generate_ffm8_report(log_file_path, start_index=0, end_index=None):
    """
    Generate CSV report from FFM8 log file with parsed SourceCompare data
    
    Args:
        log_file_path (str): Path to FFM8 log file
        start_index (int): Starting entry index (0-based), defaults to 0
        end_index (int): Ending entry index, defaults to None (all entries)
        
    Returns:
        list: Rows of CSV data, including header row
        
    Note:
        Extracts and parses multiple fields from log entries including:
        - File information
        - SourceCompare results
        - Duration differences
        - Bitrate differences
        - Container format differences
    """
    # Read the log file
    with open(log_file_path, 'r') as f:
        log_entries = f.read().strip().split('\n')
    
    # Select entries based on indices
    if end_index:
        entries_to_use = log_entries[start_index:end_index]
    else:
        entries_to_use = log_entries[start_index:]
    
    # Update header and initialize CSV data
    header = [
        "Session", "Result", "Severity", "Severity Details", "CPU_Score", "CPU_Values",
        "VMAF_Score", "VMAF_Values",  # Add new VMAF columns
        "SC_Overall", "SC_1stRes", "SC_2ndRes",
        "SC_2ndContDur", "SC_2ndVidDur", "SC_2ndAudDur",
        "SC_1stContDur", "SC_1stVidDur", "SC_1stAudDur",
        "fSize", "contDur", "vidDur", "audDur", 
        "vidBitR", "contBitR", "audBitR", 
        "contId", "contFmt", "vidFps", "vidDar",
        "vidWidth", "vidHeight"
    ]
    csv_data = [header]
    
    # Process each log entry
    for entry in entries_to_use:
        # Extract session ID and result
        session_id = ""
        result = ""
        session_match = re.search(r'RESULT:(?:Success|Failure|BAD==>)!!!\s*session:([^;]+)', entry)
        if session_match:
            result = "Success" if "Success" in entry else "Failure"
            session_id = session_match.group(1).strip()

        # Extract raw differences
        raw_differences = ""
        if result == "Success":
            raw_differences = "anlys:;"
        elif result == "Failure":
            result_match = re.search(r'RESULT:(?:Failure|BAD==>)!!!(?:session:[^;]*;)?(?:anlys:)?(.*?)(?:;PSNR|;CPU:|$)', entry)
            if result_match:
                raw_differences = result_match.group(1).replace(',', '~')
        
        # Extract files
        files_match = re.search(r'files\(([^)]+)\)', entry)
        source_file = ""
        target_file = ""
        
        if files_match:
            file_paths = files_match.group(1).split(',')
            source_file = file_paths[0].strip() if len(file_paths) > 0 else ""
            target_file = file_paths[1].strip() if len(file_paths) > 1 else ""
            
            # Extract just the filenames without paths
            source_file = os.path.basename(source_file)
            target_file = os.path.basename(target_file)
        
        # Extract the complete SourceCompare section correctly
        source_compare_raw = ""
        source_compare_match = re.search(r'SourceCompare:(.*?)(?:files\(|$)', entry)
        if source_compare_match:
            source_compare_raw = source_compare_match.group(1).strip().rstrip(';').replace(',', '~')
        
        # Parse Source Compare components
        source_compare_overall = ""
        source_compare_1st_result = ""
        source_compare_2nd_result = ""
        source_compare_1st_container_duration = ""
        source_compare_1st_video_duration = ""
        source_compare_1st_audio_duration = ""
        source_compare_2nd_container_duration = ""
        source_compare_2nd_video_duration = ""
        source_compare_2nd_audio_duration = ""
        
        # Overall result
        overall_result_match = re.search(r'SourceCompare:(\w+)', entry)
        if overall_result_match:
            source_compare_overall = overall_result_match.group(1)
        
        # First rendition
        first_rendition_match = re.search(r'1st:(\w+)', entry)
        if first_rendition_match:
            source_compare_1st_result = first_rendition_match.group(1)
            
            # If first rendition is BAD, extract its differences
            if source_compare_1st_result == "BAD":
                first_diffs_match = re.search(r'1st:BAD\(([^)]+)\)', entry)
                if first_diffs_match:
                    first_diffs = first_diffs_match.group(1)
                    
                    # Extract specific differences
                    container_duration_match = re.search(r'diff<containerDuration:([^>]+)>', first_diffs)
                    if container_duration_match:
                        source_compare_1st_container_duration = container_duration_match.group(1).replace(',', '~')
                    
                    video_duration_match = re.search(r'diff<videoDuration:([^>]+)>', first_diffs)
                    if video_duration_match:
                        source_compare_1st_video_duration = video_duration_match.group(1).replace(',', '~')
                    
                    audio_duration_match = re.search(r'diff<audioDuration:([^>]+)>', first_diffs)
                    if audio_duration_match:
                        source_compare_1st_audio_duration = audio_duration_match.group(1).replace(',', '~')
        
        # Second rendition
        second_rendition_match = re.search(r'2nd:(\w+)', entry)
        if second_rendition_match:
            source_compare_2nd_result = second_rendition_match.group(1)
            
            # If second rendition is BAD, extract its differences
            if source_compare_2nd_result == "BAD":
                second_diffs_match = re.search(r'2nd:BAD\(([^)]+)\)', entry)
                if second_diffs_match:
                    second_diffs = second_diffs_match.group(1)
                    
                    # Extract specific differences
                    container_duration_match = re.search(r'diff<containerDuration:([^>]+)>', second_diffs)
                    if container_duration_match:
                        source_compare_2nd_container_duration = container_duration_match.group(1).replace(',', '~')
                    
                    video_duration_match = re.search(r'diff<videoDuration:([^>]+)>', second_diffs)
                    if video_duration_match:
                        source_compare_2nd_video_duration = video_duration_match.group(1).replace(',', '~')
                    
                    audio_duration_match = re.search(r'diff<audioDuration:([^>]+)>', second_diffs)
                    if audio_duration_match:
                        source_compare_2nd_audio_duration = audio_duration_match.group(1).replace(',', '~')
        
        # Extract specific issue values
        fileSize = ""
        containerDuration = ""
        videoDuration = ""
        audioDuration = ""
        videoBitRate = ""
        containerBitRate = ""
        audioBitRate = ""
        containerId = ""
        containerFormat = ""
        videoFrameRate = ""
        videoDar = ""
        videoWidth = ""
        videoHeight = ""
        
        # Extract fileSize
        file_size_match = re.search(r'diff<fileSize:([^>]+)>', raw_differences)
        if file_size_match:
            fileSize = file_size_match.group(1).replace(',', '~')
        
        # Extract containerDuration
        container_duration_match = re.search(r'diff<containerDuration:([^>]+)>', raw_differences)
        if container_duration_match:
            containerDuration = container_duration_match.group(1).replace(',', '~')
        
        # Extract videoDuration
        video_duration_match = re.search(r'diff<videoDuration:([^>]+)>', raw_differences)
        if video_duration_match:
            videoDuration = video_duration_match.group(1).replace(',', '~')
        
        # Extract audioDuration
        audio_duration_match = re.search(r'diff<audioDuration:([^>]+)>', raw_differences)
        if audio_duration_match:
            audioDuration = audio_duration_match.group(1).replace(',', '~')
        
        # Extract videoBitRate
        video_bit_rate_match = re.search(r'diff<videoBitRate:([^>]+)>', raw_differences)
        if video_bit_rate_match:
            videoBitRate = video_bit_rate_match.group(1).replace(',', '~')
        
        # Extract containerBitRate
        container_bit_rate_match = re.search(r'diff<containerBitRate:([^>]+)>', raw_differences)
        if container_bit_rate_match:
            containerBitRate = container_bit_rate_match.group(1).replace(',', '~')
        
        # Extract audioBitRate
        audio_bit_rate_match = re.search(r'diff<audioBitRate:([^>]+)>', raw_differences)
        if audio_bit_rate_match:
            audioBitRate = audio_bit_rate_match.group(1).replace(',', '~')
        
        # Extract containerId
        container_id_match = re.search(r'diff<containerId:([^>]+)>', raw_differences)
        if container_id_match:
            containerId = container_id_match.group(1).replace(',', '~')
        
        # Extract containerFormat
        container_format_match = re.search(r'diff<containerFormat:([^>]+)>', raw_differences)
        if container_format_match:
            containerFormat = container_format_match.group(1).replace(',', '~')
        
        # Extract videoFrameRate
        video_frame_rate_match = re.search(r'diff<videoFrameRate:([^>]+)>', raw_differences)
        if video_frame_rate_match:
            videoFrameRate = video_frame_rate_match.group(1).replace(',', '~')
        
        # Extract videoDar
        video_dar_match = re.search(r'diff<videoDar:([^>]+)>', raw_differences)
        if video_dar_match:
            videoDar = video_dar_match.group(1).replace(',', '~')
        
        # Extract videoWidth
        video_width_match = re.search(r'diff<videoWidth:([^>]+)>', raw_differences)
        if video_width_match:
            videoWidth = video_width_match.group(1).replace(',', '~')
        
        # Extract videoHeight
        video_height_match = re.search(r'diff<videoHeight:([^>]+)>', raw_differences)
        if video_height_match:
            videoHeight = video_height_match.group(1).replace(',', '~')
        
        # Extract CPU information
        cpu_type_delta = ""
        cpu_values = ""
        cpu_match = re.search(r';CPU:([^,]+),([^,]+),([^;]+)', entry)
        if cpu_match:
            try:
                cpu_type = cpu_match.group(1)
                cpu1_str = cpu_match.group(2)
                cpu2_str = cpu_match.group(3)
                
                # Handle 'na' values
                if cpu1_str.lower() == 'na' or cpu2_str.lower() == 'na':
                    cpu_type_delta = cpu_type
                    cpu_values = f"{cpu1_str}-{cpu2_str}"
                else:
                    cpu1 = float(cpu1_str)
                    cpu2 = float(cpu2_str)
                    cpu_type_delta = f"{cpu_type}/{cpu2-cpu1:.2f}"
                    cpu_values = f"{cpu1}-{cpu2}"
            except (ValueError, TypeError):
                # Handle any conversion errors gracefully
                cpu_type_delta = cpu_match.group(1)
                cpu_values = f"{cpu_match.group(2)}-{cpu_match.group(3)}"

        # Extract VMAF information
        vmaf_score = ""
        vmaf_values = ""
        vmaf_match = re.search(r'VMAF:(\w+)\(([^:]+):(\w+);([^:]+):(\w+)(?:[,;]([^)]+))?\)', entry)
        if vmaf_match:
            result_type = vmaf_match.group(1)
            val1 = vmaf_match.group(2)
            level1 = vmaf_match.group(3).replace('EXEL', 'EX').replace('GOOD', 'GD').replace('SUFF', 'SF').replace('LOW', 'LO').replace('ERR', 'ER')
            val2 = vmaf_match.group(4)
            level2 = vmaf_match.group(5).replace('EXEL', 'EX').replace('GOOD', 'GD').replace('SUFF', 'SF').replace('LOW', 'LO').replace('ERR', 'ER')
            better = ""
            if vmaf_match.group(6):
                better = vmaf_match.group(6).replace('+','')
            
            try:
                v1 = float(val1)
                v2 = float(val2)
                delta = v2 - v1
                # Determine betterness based on value difference
                if abs(delta) < 1:
                    better = ""
                elif delta >= 6:
                    better = "2nd+"
                elif delta >= 1:
                    better = "2nd"
                elif -delta >= 6:  # v1-v2 >= 6
                    better = "1st+"
                elif -delta >= 1:  # v1-v2 >= 1
                    better = "1st"
                vmaf_score = f"{result_type}/{level1}-{level2}/{better}".rstrip('/')
                vmaf_values = f"{val1}-{val2}/{delta:.3f}"
            except (ValueError, TypeError):
                vmaf_score = f"{result_type}/{level1}-{level2}"
                vmaf_values = f"{val1}-{val2}/na"

        # Create row with updated column order
        row = [
            session_id, result, "", "", cpu_type_delta, cpu_values,
            vmaf_score, vmaf_values,  # Add new VMAF columns
            source_compare_overall, source_compare_1st_result, source_compare_2nd_result,
            source_compare_2nd_container_duration.replace('~', '-'), 
            source_compare_2nd_video_duration.replace('~', '-'),
            source_compare_2nd_audio_duration.replace('~', '-'),
            source_compare_1st_container_duration.replace('~', '-'), 
            source_compare_1st_video_duration.replace('~', '-'),
            source_compare_1st_audio_duration.replace('~', '-'),
            fileSize.replace('~', '-'),
            containerDuration.replace('~', '-'),
            videoDuration.replace('~', '-'),
            audioDuration.replace('~', '-'),
            videoBitRate.replace('~', '-'),
            containerBitRate.replace('~', '-'),
            audioBitRate.replace('~', '-'),
            containerId, containerFormat,
            videoFrameRate.replace('~', '-'),
            videoDar.replace('~', '-'),
            videoWidth.replace('~', '-'),
            videoHeight.replace('~', '-')
        ]
        
        csv_data.append(row)
    
    return csv_data

def assess_row_severity(row_dict):
    """Analyze row and determine compatibility issue severity"""
    result = row_dict.get("Result", "")
    
    if result == "Success":
        return "None", "Success - No differences"
        
    # Handle Failure cases
    overall = row_dict.get("SC_Overall", "")
    first = row_dict.get("SC_1stRes", "")
    second = row_dict.get("SC_2ndRes", "")
    
    # Video dimension issues (highest priority)
    if row_dict.get("vidWidth", "") or row_dict.get("vidHeight", ""):
        width_msg = ""
        height_msg = ""
        
        if row_dict.get("vidWidth", ""):
            orig, new = map(float, row_dict["vidWidth"].split("-"))
            width_msg = f"width {orig:.0f}->{new:.0f}"
            
        if row_dict.get("vidHeight", ""):
            orig, new = map(float, row_dict["vidHeight"].split("-"))
            height_msg = f"height {orig:.0f}->{new:.0f}"
            
        if width_msg and height_msg:
            return "Severe", f"Video dimensions mismatch: {width_msg}, {height_msg}"
        return "Severe", f"Video {width_msg or height_msg}"
    
    # Frame rate issues (high priority)
    if row_dict.get("vidFps", ""):
        return "Severe", "Frame rate mismatch"
    
    # Duration issues
    if row_dict.get("contDur", "") or row_dict.get("vidDur", "") or row_dict.get("audDur", ""):
        if row_dict.get("contDur", ""):
            orig, new = map(float, row_dict["contDur"].split("-"))
            if abs(orig - new) > 1000:
                return "Severe", "Major duration mismatch (>1s)"
    
    # Video bitrate differences
    if row_dict.get("vidBitR", ""):
        orig, new = map(float, row_dict["vidBitR"].split("-"))
        abs_diff = abs(orig - new)
        pct_diff = (abs_diff / orig) * 100 if orig else 100.0
        
        # Quality impact assessment based on original bitrate
        if orig > 1500:  # High quality content
            if abs_diff > 200:  # Noticeable quality drop for high bitrate
                return "Severe", f"Major quality impact {orig:.0f}->{new:.0f} kbps"
            if abs_diff > 100:
                return "Moderate", f"Visible quality change {orig:.0f}->{new:.0f} kbps"
        elif orig > 500:  # Medium quality content
            if abs_diff > 150:  # Significant for medium quality
                return "Severe", f"Major quality impact {orig:.0f}->{new:.0f} kbps"
            if abs_diff > 75:
                return "Moderate", f"Noticeable quality change {orig:.0f}->{new:.0f} kbps"
        else:  # Low quality content
            if abs_diff > 50 and pct_diff > 40:  # Only severe if huge relative change
                return "Severe", f"Large quality change {orig:.0f}->{new:.0f} kbps"
            
        return "Minor", f"Small quality impact {orig:.0f}->{new:.0f} kbps"
    
    # VMAF quality regression (a Failure can be VMAF-driven with no field diffs)
    vmaf = row_dict.get("VMAF_Score", "")
    if vmaf:
        parts = vmaf.split("/")
        grade = parts[0]
        levels = parts[1] if len(parts) > 1 else ""
        if grade == "BAD" or "ER" in levels:
            return "Severe", f"VMAF quality regression ({vmaf})"
        if "LO" in levels:
            return "Moderate", f"Low VMAF ({vmaf})"

    # Audio bitrate differences
    if row_dict.get("audBitR", ""):
        return "Moderate", f"Audio bitrate change {row_dict['audBitR'].replace('-', '->')}"

    # Basic differences
    if overall == "OK" and first == "OK" and second == "OK":
        if row_dict.get("contId", "") or row_dict.get("contFmt", ""):
            return "Minor", "Container format/ID differences only"
    
    if overall == "BAD":
        return "Unknown", "Marked BAD but no clear severity indicator"
        
    return "None", "No significant differences"

def add_severity_assessment(report_data):
    """Add severity assessment columns to report data"""
    # Update header
    header = report_data[0]
    new_header = ["Session", "Result", "Severity", "Severity Details", 
                 "CPU_Score", "CPU_Values", "VMAF_Score", "VMAF_Values"] + header[8:]
    
    # Process rows
    new_rows = [new_header]
    
    for row in report_data[1:]:
        # Convert row to dict for severity assessment
        row_dict = dict(zip(header, row))
        severity, details = assess_row_severity(row_dict)
        
        new_row = [
            row[0],  # Session
            row[1],  # Result
            severity,
            details,
            row[4],  # CPU_Score
            row[5],  # CPU_Values
            row[6],  # VMAF_Score - keep existing parsed value
            row[7],  # VMAF_Values - keep existing parsed value
        ]
        new_row.extend(row[8:])  # Add remaining fields
        new_rows.append(new_row)
    
    return new_rows

def process_and_save_report(log_file, output_file):
    """Process FFM8 log file and save report with severity assessment"""
    unknown_fields = set()
    all_fields = set()
    
    # Extract fields from raw differences in the log file
    with open(log_file, 'r') as f:
        for line in f:
            # Look for diff<field:value> patterns in the log lines
            fields = re.findall(r'diff<([^:]+):', line)
            if fields:
                all_fields.update(fields)
                unknown_fields.update(set(fields) - KNOWN_FIELDS)
    
    # Generate report using v1
    report_data = generate_ffm8_report(log_file)
    
    # Apply severity assessment
    full_report = add_severity_assessment(report_data)
    
    # Save report
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(full_report)
    
    print(f"\nCreated report: {output_file}")
    print(f"Processed {len(full_report)-1} entries")
    
    # Print field analysis
    if all_fields:
        print("\nAll difference fields found:")
        for field in sorted(all_fields):
            status = "Known" if field in KNOWN_FIELDS else "Unknown"
            print(f"- {field} ({status})")
    
    if unknown_fields:
        print("\nWARNING: Unknown difference fields detected:")
        for field in sorted(unknown_fields):
            print(f"- {field}")
        print("\nConsider adding these fields to KNOWN_FIELDS if they are valid.")

def is_numeric(value):
    """
    Check if a string value can be converted to a float number
    
    Args:
        value (str): String to check
        
    Returns:
        bool: True if value can be converted to float, False otherwise
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def values_are_similar(val1, val2, tolerance=0.1):
    """
    Compare two values with configurable tolerance
    
    Args:
        val1 (str): First value to compare
        val2 (str): Second value to compare
        tolerance (float): Relative difference tolerance (default: 0.1 or 10%)
        
    Returns:
        bool: True if values are similar within tolerance or identical strings
    """
    if not val1 and not val2:  # Both empty
        return True
    if not val1 or not val2:  # One empty
        return False
    
    # Handle tilde-separated values
    if '~' in val1 and '~' in val2:
        val1_parts = val1.split('~')
        val2_parts = val2.split('~')
        if len(val1_parts) != len(val2_parts):
            return False
        # Compare each part
        return all(values_are_similar(p1, p2, tolerance) for p1, p2 in zip(val1_parts, val2_parts))
        
    # Try numeric comparison
    if is_numeric(val1) and is_numeric(val2):
        num1, num2 = float(val1), float(val2)
        if num1 == 0:  # Avoid division by zero
            return abs(num2) < tolerance
        return abs((num1 - num2) / num1) <= tolerance
        
    # String comparison
    return val1 == val2

def compare_sample_rows(row1, row2):
    """
    Compare two sample rows and identify fields with significant differences
    
    Args:
        row1 (list): First row data
        row2 (list): Second row data
        
    Returns:
        list: Indices of fields where values differ significantly
        
    Note:
        Excludes Session, RawDiffs and SC_Raw columns from comparison
    """
    differences = []
    
    # Skip first column (Session) and last 2 columns (RawDiffs, SC_Raw)
    for i in range(1, len(row1)):  # compare all data columns (no trailing raw cols in this format)
        if not values_are_similar(row1[i], row2[i]):
            differences.append(i)
    return differences

def compare_reports(report1_path, report2_path, output_path):
    """
    Compare two FFM8 reports and generate consolidated comparison
    
    Args:
        report1_path (str): Path to first report CSV
        report2_path (str): Path to second report CSV
        output_path (str): Path for output CSV file
        
    Output Format:
        1. Samples unique to each report
        2. Common samples with differences (grouped by field)
        3. Similar common samples
        4. Empty rows between sections
        
    Note:
        - Maintains BuildNotes CSV format
        - Groups samples by compatibility type
        - Adds severity assessment columns
        - Preserves all original data fields
    """
    # Read both reports
    with open(report1_path, 'r', newline='') as f1, open(report2_path, 'r', newline='') as f2:
        report1 = list(csv.reader(f1))
        report2 = list(csv.reader(f2))
        
    header = report1[0]  # Assuming both reports have same header
    
    # Create dictionaries of rows keyed by Session
    report1_dict = {row[0]: row for row in report1[1:]}
    report2_dict = {row[0]: row for row in report2[1:]}
    
    # Find unique and common samples
    sessions_in_report1 = set(report1_dict.keys())
    sessions_in_report2 = set(report2_dict.keys())
    
    only_in_report1 = sessions_in_report1 - sessions_in_report2
    only_in_report2 = sessions_in_report2 - sessions_in_report1
    in_both = sessions_in_report1 & sessions_in_report2
    
    # Analyze common samples
    different_samples = []
    similar_samples = []
    
    for session in sorted(in_both):
        row1 = report1_dict[session]
        row2 = report2_dict[session]
        differences = compare_sample_rows(row1, row2)
        
        if differences:
            # Add both versions of the sample
            different_samples.append((session, differences, row1, row2))
        else:
            similar_samples.append(row1)  # Use version from report1
    
    # Prepare output data
    new_header = list(header)  # header already carries Severity / Severity Details at idx 2,3
    output_rows = [new_header]
    
    # Add samples unique to report1
    if only_in_report1:
        output_rows.append(['CATEGORY: Incompatible FFM6 rendition, compatible FFM8'] + [""] * (len(new_header) - 1))
        for session in sorted(only_in_report1):
            row = report1_dict[session]
            row_dict = dict(zip(header, row))
            severity, details = assess_row_severity(row_dict)
            output_rows.append(row[:2] + [severity, details] + row[4:])
        output_rows.append([""] * len(new_header))
    
    # Add samples unique to report2
    if only_in_report2:
        output_rows.append(['CATEGORY: Incompatible FFM8 rendition, compatible FFM6'] + [""] * (len(new_header) - 1))
        for session in sorted(only_in_report2):
            row = report2_dict[session]
            row_dict = dict(zip(header, row))
            severity, details = assess_row_severity(row_dict)
            output_rows.append(row[:2] + [severity, details] + row[4:])
        output_rows.append([""] * len(new_header))
    
    # Add different common samples
    if different_samples:
        output_rows.append(["CATEGORY: Common samples with differences"] + [""] * (len(new_header) - 1))
        
        # Group by differences for better organization
        diff_groups = defaultdict(list)
        for session, differences, row1, row2 in different_samples:
            diff_fields = sorted([header[i] for i in differences])
            key = "DETAILS: Different in " + ",".join(diff_fields)
            diff_groups[key].extend([row1, row2])
        
        # Output each group
        for detail, rows in diff_groups.items():
            output_rows.append([detail] + [""] * (len(new_header) - 1))
            for row in rows:
                row_dict = dict(zip(header, row))
                severity, details = assess_row_severity(row_dict)
                output_rows.append(row[:2] + [severity, details] + row[4:])
            output_rows.append([""] * len(new_header))
        
        output_rows.append([""] * len(new_header))
    
    # Add similar common samples
    if similar_samples:
        output_rows.append(["CATEGORY: Common samples (similar)"] + [""] * (len(new_header) - 1))
        for row in similar_samples:
            row_dict = dict(zip(header, row))
            severity, details = assess_row_severity(row_dict)
            output_rows.append(row[:2] + [severity, details] + row[4:])
    
    # Write output
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output_rows)
    
    # Print summary
    print(f"\nComparison report created: {output_path}")
    print(f"Samples only in report 1: {len(only_in_report1)}")
    print(f"Samples only in report 2: {len(only_in_report2)}")
    print(f"Common samples with differences: {len(different_samples)}")
    print(f"Common samples (similar): {len(similar_samples)}")

if __name__ == "__main__":
    if len(sys.argv) != 3 and len(sys.argv) != 5:
        print("Usage: python ffm8_report.py <log_file> <output_file>")
        print("For comparison: python ffm8_report.py --compare <report1> <report2> <output_file>")
        sys.exit(1)
    
    if sys.argv[1] == "--compare" and len(sys.argv) == 5:
        report1 = sys.argv[2]
        report2 = sys.argv[3]
        output_file = sys.argv[4]
        compare_reports(report1, report2, output_file)
    else:
        log_file = sys.argv[1]
        output_file = sys.argv[2]
        process_and_save_report(log_file, output_file)