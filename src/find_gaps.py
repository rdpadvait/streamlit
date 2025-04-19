import json
import sys
from pathlib import Path


def find_large_gaps(json_file, threshold=3.0):
    """
    Find gaps between segments that are larger than the specified threshold.
    
    Args:
        json_file (str): Path to the JSON file containing segments
        threshold (float): Minimum gap size in seconds to report (default: 3.0)
        
    Returns:
        list: List of dictionaries containing gap information
    """
    # Load the JSON data
    with open(json_file, 'r') as f:
        segments = json.load(f)
    
    # Sort segments by start_time to ensure proper order
    segments.sort(key=lambda x: x['start_time'])
    
    # Find gaps
    gaps = []
    for i in range(1, len(segments)):
        prev_segment = segments[i-1]
        curr_segment = segments[i]
        
        gap_size = curr_segment['start_time'] - prev_segment['end_time']
        
        if gap_size > threshold:
            gap_info = {
                'gap_size': round(gap_size, 2),
                'prev_segment_id': prev_segment['id'],
                'prev_segment_end': prev_segment['end_time'],
                'prev_segment_text': prev_segment['text'],
                'next_segment_id': curr_segment['id'],
                'next_segment_start': curr_segment['start_time'],
                'next_segment_text': curr_segment['text']
            }
            gaps.append(gap_info)
    
    return gaps


def find_large_segments(json_file, threshold=20.0):
    """
    Find segments that are longer than the specified threshold.
    
    Args:
        json_file (str): Path to the JSON file containing segments
        threshold (float): Minimum segment duration in seconds to report (default: 20.0)
        
    Returns:
        list: List of dictionaries containing large segment information
    """
    # Load the JSON data
    with open(json_file, 'r') as f:
        segments = json.load(f)
    
    # Find large segments
    large_segments = []
    for segment in segments:
        duration = segment['duration']
        
        if duration > threshold:
            segment_info = {
                'segment_id': segment['id'],
                'duration': round(duration, 2),
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'text': segment['text'],
                'speaker': segment.get('speaker', 'unknown')
            }
            large_segments.append(segment_info)
    
    # Sort by duration (largest first)
    large_segments.sort(key=lambda x: x['duration'], reverse=True)
    
    return large_segments


def main():
    if len(sys.argv) < 2:
        print("Usage: python find_gaps.py <json_file> [gap_threshold] [segment_threshold]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    gap_threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 30
    segment_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    if not Path(json_file).exists():
        print(f"Error: File '{json_file}' not found.")
        sys.exit(1)
    
    try:
        # Find and report gaps
        gaps = find_large_gaps(json_file, gap_threshold)
        
        if not gaps:
            print(f"No gaps larger than {gap_threshold} seconds found.")
        else:
            print(f"Found {len(gaps)} gaps larger than {gap_threshold} seconds:")
            print('-' * 80)
            
            for i, gap in enumerate(gaps, 1):
                print(f"Gap #{i}: {gap['gap_size']} seconds")
                print(f"Between segment {gap['prev_segment_id']} (ends at {gap['prev_segment_end']}s)")
                print(f"  Text: \"{gap['prev_segment_text']}\"")
                print(f"And segment {gap['next_segment_id']} (starts at {gap['next_segment_start']}s)")
                print(f"  Text: \"{gap['next_segment_text']}\"")
                print('-' * 80)
        
        # Find and report large segments
        large_segments = find_large_segments(json_file, segment_threshold)
        
        if not large_segments:
            print(f"\nNo segments longer than {segment_threshold} seconds found.")
        else:
            print(f"\nFound {len(large_segments)} segments longer than {segment_threshold} seconds:")
            print('-' * 80)
            
            for i, segment in enumerate(large_segments, 1):
                print(f"Large Segment #{i}: {segment['duration']} seconds (ID: {segment['segment_id']})")
                print(f"  Time Range: {segment['start_time']}s - {segment['end_time']}s")
                print(f"  Speaker: {segment['speaker']}")
                print(f"  Text: \"{segment['text']}\"")
                print('-' * 80)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 