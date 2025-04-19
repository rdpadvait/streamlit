import pandas as pd

from logger import logger


def convert_time(time_str: str, to_ms: bool = False, segment: int | None = None) -> str | int | None:
    if not time_str:
        raise ValueError(f"Segment {segment}: Enter time")
    if ':' in time_str:
        # Format: MM:SS,MS or HH:MM:SS,MS
        parts = time_str.replace(',', '.').split(':')
        if len(parts) == 2:
            minutes, seconds = parts
            total_seconds = float(minutes) * 60 + float(seconds)
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            total_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        else:
            raise ValueError(f"Segment {segment}: Invalid time format")
    else:
        # Format: seconds
        total_seconds = float(time_str)
        
    if to_ms:
        return int(total_seconds * 1000)
    else:
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int((total_seconds - int(total_seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def convert_to_srt(session_state) -> tuple[str, list[dict]]:
    srt_content = []
    df_data = []
    for i, subtitle in enumerate(session_state.subtitles, start=1):
        start_time = convert_time(subtitle['start'], to_ms=False, segment=i)
        end_time = convert_time(subtitle['end'], to_ms=False, segment=i)
        
        if not subtitle['text']:
            raise ValueError(f"Segment {i}: Enter text")
        
        entry = f"{i}\n{start_time} --> {end_time}\n[{subtitle['speaker']}] {subtitle['text']}\n"
        srt_content.append(entry)
        
        df_data.append({
            'start': start_time,
            'end': end_time,
            'text': subtitle['text'],
            'speaker': subtitle['speaker'],
        })
    srt_string = "\n".join(srt_content)
    pd.DataFrame(df_data).to_csv(session_state.srt_df_path, index=False)
    with open(session_state.srt_path, "w") as f:
        f.write(srt_string)
    logger.info(f"SRT length {len(srt_content)} written to {session_state.srt_path}") if len(srt_content) > 0 else None
    return srt_string, df_data

if __name__ == "__main__":
    subtitles = [
        {'start': 0, 'end': 5.5, 'text': 'Hello world'},
        {'start': '00:00:06', 'end': '00:00:10', 'text': 'This is a test'},
        {'start': '00:00:11.500', 'end': 16, 'text': 'Multiline\nsubtitle example'},
        {'start': '0:17', 'end': '0:20.500', 'text': 'Different format example'},
    ]
    
    srt_output = convert_to_srt({'subtitles': subtitles, 'folder_name': '/tmp/session_test'})
    print(srt_output)