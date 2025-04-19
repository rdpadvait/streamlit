import hashlib
import os
import re
from math import sqrt
from typing import Dict

import pysrt
from pydub import AudioSegment

import streamlit as st
from logger import logger
from src.cmd_utils import change_audio_speed, merge_audio_video
from src.elevenlabs_api import sts
from src.elevenlabs_api import tts as eleven_tts
from src.gtts import tts as gtts


@st.cache_data
def get_lang_codes() -> Dict[str, str]:
    return {
        "Telugu": "te-IN",
        "Kannada": "kn-IN",
        "Malayalam": "ml-IN",
        "Punjabi": "pa-IN",
        "Gujarati": "gu-IN",
        "Marathi": "mr-IN",
        "Bengali": "bn-IN",
        # ELEVENLABS SUPPORTS BELOW LANGUAGES
        "Tamil": "ta",
        "Hindi": "hi",
        "English": "en",
    }
    
SPEAKERS = ["AP", "MALE", "FEMALE"]
SPEED_MIN = 0.5
SPEED_MAX = 5.0

def process_srt_and_join(
    srt_content, language_code, final_output, credentials=None
):
    subtitles = pysrt.from_string(srt_content)
    logger.info(f"Dubbing subtitles:\n```{subtitles}```")
    audio = AudioSegment.empty()

    gen_len = 0
    first_start = subtitles[0].start.ordinal
    if first_start > 0:
        audio += AudioSegment.silent(duration=int(first_start))
        gen_len += first_start
    for i, sub in enumerate(subtitles):
        text = sub.text.strip()
        speaker = "AP"
        if speaker_match := re.search(r"\[(.*?)\]", text):
            if (s := speaker_match.group(1)) in SPEAKERS:
                speaker = s
            else:
                logger.warning(f"Invalid speaker: {s}")
        text = re.sub(r"\[(.*)\]", "", text).strip()        
        logger.info(f"Dubbing segment {i}")
        seg_audio = AudioSegment.from_mp3(dub_single_segment(
            text, 
            language_code, 
            speaker=speaker,
            gtts_creds=credentials,
            start_time=sub.start.ordinal,
            end_time=sub.end.ordinal
        ))
        
        gen_len += len(seg_audio)
        audio += seg_audio
        
        if i < len(subtitles) - 1:
            gap = subtitles[i + 1].start.ordinal - (sub.start.ordinal + len(seg_audio))
            if gap > 0:
                audio += AudioSegment.silent(duration=gap)
            elif gap < 0:
                logger.warning(f"Negative gap ({gap}ms) detected between subtitles {i+1} and {i+2}. Audio segments may overlap due to subtitle timing overlap or generated audio being too long.")
    audio.export(final_output, format="mp3")
    print(f'Final audio written to "{final_output}"')
    return gen_len

def tts_sts(text, lang_code, final_output, tts_output=None, gtts_creds=None, **kwargs) -> AudioSegment:
    if lang_code in ["ta", "hi", "en"]:
        eleven_tts(text, output_file=final_output, **kwargs)
    else:
        if not tts_output:
            tts_output = final_output.replace(".mp3", "_tts.mp3")
        gtts(
            text, lang_code, output_file=tts_output, credentials=gtts_creds, **kwargs
        )
        sts(tts_output, final_output, speaker = kwargs.get("speaker", "AP"))
    return AudioSegment.from_mp3(final_output)

def create_dubbed_video(
    input_video_path: str,
    lang_code: str,
    output_video_path: str,
    input_audio_path: str,
    text=None,
    srt_content=None,
    gtts_creds=None,
):
    if not text and not srt_content:
        st.error("Please upload a valid SRT or translated text.")
        return
    logger.info(f"Creating dubbed video for: {input_video_path}")
    final_audio_path = os.path.dirname(output_video_path) + "/final_audio.mp3"
    if not srt_content:
        audio_duration = len(AudioSegment.from_file(input_audio_path)) / 1000
        audio_duration = f"{int(audio_duration/3600):02}:{int((audio_duration%3600)/60):02}:{int(audio_duration%60):02},000"
        srt_content = f"1\n00:00:00,000 --> {audio_duration}\n{text}"
    gen_len = process_srt_and_join(srt_content, lang_code, final_audio_path, credentials=gtts_creds)
    input_len = len(AudioSegment.from_file(input_audio_path))
    final_len = len(AudioSegment.from_file(final_audio_path))
    if abs(input_len - final_len) > 1000:
        logger.warning(f"Audio length mismatch: {input_len} != {final_len}")
    merge_audio_video(input_video_path, final_audio_path, output_video_path)
    st.success("Dubbed video created!")
    logger.info("!Dubbed video created successfully!")  

def dub_single_segment(text, lang_code, speaker="AP", gtts_creds=None, start_time=None, end_time=None) -> str:
    os.makedirs(st.session_state.folder_name, exist_ok=True)
    segment_hash = hashlib.sha256(f"{start_time}-{end_time}-{speaker}-{text.replace('\n', ' ')}".encode()).hexdigest()
    segment_file = f"{st.session_state.folder_name}/{segment_hash}.mp3"
    speed_segment_file = f"{st.session_state.folder_name}/speed_{segment_hash}.mp3"
    if os.path.exists(speed_segment_file):
        return speed_segment_file
    audio = tts_sts(text, lang_code, segment_file, gtts_creds=gtts_creds, speaker=speaker)
    if start_time is not None and end_time is not None:
        target_duration = end_time - start_time
        natural_duration = len(audio)
        speed = natural_duration / target_duration
        
        if speed > SPEED_MAX or speed < SPEED_MIN:
            speed = max(SPEED_MIN, min(SPEED_MAX, speed))
            warn = f"Time for segment is too off. Natural time={natural_duration}, segment time={target_duration}"
            logger.warning(warn)
            st.warning(warn)
        change_audio_speed(segment_file, speed_segment_file, speed)
    return speed_segment_file

if __name__ == "__main__":
    data = "/tmp/session_1/"
    input_audio = f"{data}input_audio.mp3"
    output_audio = f"{data}tts_output.mp3"
    final_output_path = f"{data}final_audio.mp3"