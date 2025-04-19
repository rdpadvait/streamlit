from elevenlabs import ElevenLabs

from src.utils import write

CLIENT = ElevenLabs()
def transcribe_audio(audio_path, model_id='scribe_v1', language_code=None):
    with open(audio_path, 'rb') as f:
        audio = f.read()
    
    params = {
        'model_id': model_id,
        'file': audio,
        'tag_audio_events': False,
        'diarize': True,
        'num_speakers': 4,
        'timestamps_granularity': 'word'
    }
    
    if language_code is not None:
        params['language_code'] = language_code
        
    return CLIENT.speech_to_text.convert(**params)

def identify_segments(transcription, pause_threshold=0.5):
    segments = []
    current_segment = []
    last_end_time = 0
    
    for word in transcription.words:
        if word.type == "spacing":
            continue
            
        if word.type == "word":
            if not current_segment or (word.start - last_end_time > pause_threshold):
                if current_segment:
                    segments.append(current_segment)
                current_segment = [word]
            else:
                current_segment.append(word)
                
            last_end_time = word.end
    
    if current_segment:
        segments.append(current_segment)
        
    return segments

def convert_segments_to_dict(segments):
    result = []
    
    for i, segment in enumerate(segments):
        segment_text = " ".join([word.text for word in segment])
        start_time = segment[0].start
        end_time = segment[-1].end
        
        speaker_counts = {}
        for word in segment:
            try:
                speaker = word.speaker_id
            except AttributeError:
                try:
                    speaker = word.speaker
                except AttributeError:
                    speaker = "unknown"
                    
            if speaker in speaker_counts:
                speaker_counts[speaker] += 1
            else:
                speaker_counts[speaker] = 1
                
        dominant_speaker = max(speaker_counts.items(), key=lambda x: x[1])[0] if speaker_counts else "unknown"
        
        segment_dict = {
            "id": i + 1,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "text": segment_text,
            "speaker": dominant_speaker
        }
        
        result.append(segment_dict)
    
    return result

def display_transcription(transcription):
    print("\nSegmented output based on pauses:")
    segments = identify_segments(transcription)
    
    for i, segment in enumerate(segments):
        segment_text = " ".join([word.text for word in segment])
        start_time = segment[0].start
        end_time = segment[-1].end
        
        print(f"Segment {i+1}:")
        print(f"  Start: {start_time:.2f}s, End: {end_time:.2f}s")
        print(f"  Text: {segment_text}")
        print()
    
    return segments

def main():
    audio_path = "tmp/t/t_missing.mp3"
    transcription = transcribe_audio(audio_path)
    print("Transcription completed.")
    
    raw_text = " ".join([word.text for word in transcription.words if word.type == "word"])
    write(f'{audio_path.replace(".mp3", "_transcript.txt")}', raw_text)
    # return
    segments = display_transcription(transcription)
    serializable_segments = convert_segments_to_dict(segments)
    
    speaker_transcript = []
    current_speaker = None
    
    for segment in serializable_segments:
        if segment["speaker"] != current_speaker:
            if speaker_transcript:
                speaker_transcript.append("\n")
            speaker_transcript.append(f"{segment['speaker']}: {segment['text'].strip()}")
            current_speaker = segment["speaker"]
        else:
            speaker_transcript.append(f" {segment['text'].strip()}")
    
    write(f'{audio_path.replace(".mp3", "_speaker_transcript.txt")}', "\n".join(speaker_transcript))
    
    write(f'{audio_path.replace(".mp3", "_segments.json")}', serializable_segments)
        
if __name__ == '__main__':
    main()