import json
import os
import time
from typing import List

import streamlit as st
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from src.logger import logger
from src.cmd_utils import (
    convert_audio,
    download_video,
    extract_audio,
)
from src.dub import (
    SPEAKERS,
    create_dubbed_video,
    dub_single_segment,
    get_lang_codes,
    process_srt_and_join,
)
from src.oai import OpenAIHandler
from src.pages.base_page import BasePage
from src.srt_ui import subtitle_editor
from src.srt_utils import convert_to_srt


def ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT time format (HH:MM:SS,ms)."""
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def srt_time_to_ms(time_str: str) -> int:
    """Convert SRT time format (HH:MM:SS,ms) to milliseconds."""
    time_parts = time_str.split(',')
    hms_part = time_parts[0]
    ms_part = time_parts[1]
    
    h, m, s = map(int, hms_part.split(':'))
    ms = int(ms_part)
    
    return (h * 3600 + m * 60 + s) * 1000 + ms


class DubberPage(BasePage):
    DEFAULT_WIDTH = 60
    SIDE = max((100 - DEFAULT_WIDTH) / 2, 0.01)
    
    def __init__(self):
        self.workdir = os.environ.get("WORKDIR", "/tmp")
        self.init_session()
    
    def init_session(self):
        if "folder_name" not in st.session_state:
            st.session_state.folder_name = f"{self.workdir}/session_{int(time.time())}"
            os.makedirs(st.session_state.folder_name, exist_ok=True)
            logger.info(f"Created folder: {st.session_state.folder_name}")
            
        self.rootdir = st.session_state.folder_name
        self.input_path = os.path.join(self.rootdir, "input.mp4")
        self.audio_path = os.path.join(self.rootdir, "input_audio.mp3")
        self.output_path = os.path.join(self.rootdir, "output.mp4")
        st.session_state["srt_path"] = os.path.join(self.rootdir, "subtitles.srt")
        st.session_state["srt_df_path"] = os.path.join(self.rootdir, "subtitles_df.csv")
        
        segments_file = os.path.join(self.rootdir, "segments.json")
        if "segments" not in st.session_state and os.path.exists(segments_file):
            with open(segments_file, "r") as f:
                st.session_state["segments"] = json.load(f)
    
    def save_segments(self):
        """Saves the current segments to a JSON file."""
        if "segments" in st.session_state:
            segments_file = os.path.join(self.rootdir, "segments.json")
            with open(segments_file, "w") as f:
                json.dump(st.session_state["segments"], f, indent=2)
            logger.info("Segments saved to file.")

    def add_segment(self, index: int):
        """Adds a new segment at a specific index."""
        new_segment = {
            "start": 0,
            "end": 1000,
            "transcript": "",
            "translation": "",
            "speaker": "AP",
            "path": ""
        }
        
        if index > 0 and index <= len(st.session_state["segments"]):
            prev_segment = st.session_state["segments"][index - 1]
            new_segment["start"] = prev_segment["end"]
            new_segment["end"] = prev_segment["end"] + 1000
        
        st.session_state["segments"].insert(index, new_segment)
        self.save_segments()
        st.rerun()

    def setup_session_management(self):
        st.sidebar.title("Session Management")
        new_session_id = st.sidebar.text_input("Enter Session ID to load:", key="session_id_input")
        
        if new_session_id and new_session_id.startswith("session_"):
            session_path = f"{self.workdir}/{new_session_id}"
            if os.path.exists(session_path):
                st.session_state.folder_name = session_path
                st.sidebar.success(f"Successfully loaded session: {new_session_id}")
                for file in os.listdir(session_path):
                    if file == "input.mp4":
                        st.session_state["src_vid"] = f"{session_path}/input.mp4"
                        break
            else:
                st.sidebar.error("Session not found!")
        
        st.sidebar.markdown("Current Session ID (Copy and save):")
        st.sidebar.code(os.path.basename(st.session_state.folder_name), language="text")
    
    def chunk_audio_at_silence(self, audio_path: str, max_chunk_duration_ms: int = 180000) -> List[dict]:
        """
        Split audio into chunks at silence points, with maximum chunk duration.
        
        Args:
            audio_path: Path to the audio file
            max_chunk_duration_ms: Maximum chunk duration in milliseconds (default: 3 minutes)
            
        Returns:
            List of dictionaries, each containing start, end, and path of a chunk.
        """
        audio = AudioSegment.from_file(audio_path)
        
        # Detect non-silent parts
        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=2500,
            silence_thresh=-40,
        )
        
        # Further split chunks that are too long
        final_ranges = []
        for start_ms, end_ms in nonsilent_ranges:
            duration = end_ms - start_ms
            if duration < 1000:  # Skip chunks shorter than 1 second
                continue
            if duration <= max_chunk_duration_ms:
                final_ranges.append((start_ms, end_ms))
            else:
                # Split long chunks into smaller pieces
                num_splits = (duration + max_chunk_duration_ms - 1) // max_chunk_duration_ms
                chunk_size = duration // num_splits
                
                for i in range(num_splits):
                    chunk_start = start_ms + i * chunk_size
                    chunk_end = chunk_start + chunk_size if i < num_splits - 1 else end_ms
                    final_ranges.append((chunk_start, chunk_end))
        
        # Save chunks to files and create details list
        chunk_details = []
        chunks_dir = os.path.join(self.rootdir, "audio_chunks")
        os.makedirs(chunks_dir, exist_ok=True)
        
        for i, (start_ms, end_ms) in enumerate(final_ranges):
            chunk = audio[start_ms:end_ms]
            chunk_path = os.path.join(chunks_dir, f"chunk_{i:03d}.mp3")
            chunk.export(chunk_path, format="mp3")
            chunk_details.append({
                "start": start_ms,
                "end": end_ms,
                "path": chunk_path,
            })
            
        logger.info(f"Split audio into {len(chunk_details)} chunks")
        return chunk_details

    def upload_media_section(self):
        st.subheader("1. Upload Media File")

        # Disable uploaders if a file has already been processed for the session
        file_processed = os.path.exists(self.audio_path) and os.path.getsize(self.audio_path) > 0

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Option A: Upload Short Video (Upto 3min)")
            uploaded_video = st.file_uploader(
                "Download MP4 Video with Audio from https://www.clipto.com/media-downloader/youtube-downloader and upload here",
                type=["mp4"],
                key="video_uploader",
                disabled=file_processed
            )
            if uploaded_video and not file_processed:
                with open(self.input_path, "wb") as f:
                    f.write(uploaded_video.getbuffer())
                if extract_audio(self.input_path, self.audio_path):
                    st.success("Video uploaded and audio extracted!")
                    st.session_state["src_vid"] = self.input_path
                    st.rerun()
                else:
                    logger.error("Error extracting audio.")
                    st.error("Error extracting audio.")

        with col2:
            st.markdown("##### Option B: Upload Audio")
            uploaded_audio = st.file_uploader(
                "Upload an audio file directly.",
                type=["mp3", "wav", "m4a"],
                key="audio_uploader",
                disabled=file_processed
            )
            if uploaded_audio and not file_processed:
                # Save to a temporary file with original name
                temp_audio_path = os.path.join(self.rootdir, uploaded_audio.name)
                with open(temp_audio_path, "wb") as f:
                    f.write(uploaded_audio.getbuffer())

                # Convert to standard mp3 format
                if convert_audio(temp_audio_path, self.audio_path):
                    st.success("Audio uploaded and converted successfully!")
                    st.rerun()
                else:
                    logger.error("Error converting audio.")
                    st.error("Error converting audio.")

    @staticmethod
    @st.cache_data
    def load_video_data(video_path: str):
        with open(video_path, "rb") as f:
            return f.read()
        
    @staticmethod
    @st.cache_resource
    def get_openai_handler():
        return OpenAIHandler(configs_dir="configs")

    def transcribe_audio_chunks(self, chunk_details: List[dict]) -> List[dict]:
        """
        Transcribe audio chunks.
        
        Args:
            chunk_details: List of dictionaries with chunk information.
            
        Returns:
            List of dictionaries with transcriptions added.
        """
        openai_handler = self.get_openai_handler()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, chunk_info in enumerate(chunk_details):
            status_text.text(f"Transcribing chunk {i+1}/{len(chunk_details)}...")
            
            try:
                # Transcribe chunk
                transcript = openai_handler.transcribe(chunk_info["path"])
                chunk_info["transcript"] = transcript
                chunk_info["speaker"] = "AP"  # Default speaker
            except Exception as e:
                logger.error(f"Failed to transcribe chunk {i+1} due to server error: {e}")
                chunk_info["transcript"] = "[Transcription failed due to server error]"
                chunk_info["speaker"] = "AP"
            
            progress_bar.progress((i + 1) / len(chunk_details))
        
        status_text.empty()
        return chunk_details

    def segments_section(self, target_lang):
        st.subheader("2. Segmentation")

        if st.button("Generate Segments"):
            with st.spinner("Chunking and transcribing audio..."):
                chunk_details = self.chunk_audio_at_silence(self.audio_path)
                segments = self.transcribe_audio_chunks(chunk_details)
                st.session_state["segments"] = segments
                
                # Save to file
                segments_file = os.path.join(self.rootdir, "segments.json")
                with open(segments_file, "w") as f:
                    json.dump(segments, f)
                    
                st.success(f"Generated {len(segments)} segments.")

        if "segments" in st.session_state:
            if st.button("Translate All Segments"):
                if not target_lang:
                    st.error("Please select a target language first!")
                else:
                    with st.spinner("Translating all segments..."):
                        # Sync all transcripts from widgets to session state before translating
                        for i, seg in enumerate(st.session_state["segments"]):
                            if f"transcript_text_{i}" in st.session_state:
                                st.session_state["segments"][i]["transcript"] = st.session_state[f"transcript_text_{i}"]

                        openai_handler = self.get_openai_handler()
                        for i, segment in enumerate(st.session_state["segments"]):
                            if segment.get("transcript"):
                                translation = openai_handler.translate(segment["transcript"], language=target_lang)
                                segment["translation"] = translation
                        self.save_segments()
                        st.success("All segments translated.")
                        st.rerun()

            # Header for the segments table
            cols = st.columns([1.2, 3.6, 3.6, 0.8, 1.8])
            cols[0].markdown("**Time**")
            cols[1].markdown("**Transcribed Text**")
            cols[2].markdown("**Translated Text**")
            cols[3].markdown("**Speaker**")
            cols[4].markdown("**Actions**")
            st.divider()

            if st.button("＋", key="add_at_start", help="Add segment at start"):
                self.add_segment(0)

            for i, segment in enumerate(st.session_state["segments"]):
                col1, col2, col3, col4, col5 = st.columns([1.2, 3.6, 3.6, 0.8, 1.8])

                with col1:
                    def update_segment_time(idx=i):
                        try:
                            start_ms = srt_time_to_ms(st.session_state[f"start_time_{idx}"])
                            end_ms = srt_time_to_ms(st.session_state[f"end_time_{idx}"])
                            st.session_state["segments"][idx]["start"] = start_ms
                            st.session_state["segments"][idx]["end"] = end_ms
                            self.save_segments()
                        except Exception as e:
                            st.error(f"Invalid time format for segment {idx+1}. Use HH:MM:SS,ms. Error: {e}")

                    st.text_input(
                        "Start Time",
                        value=ms_to_srt_time(segment['start']),
                        key=f"start_time_{i}",
                        on_change=update_segment_time,
                        label_visibility="collapsed"
                    )
                    st.text_input(
                        "End Time",
                        value=ms_to_srt_time(segment['end']),
                        key=f"end_time_{i}",
                        on_change=update_segment_time,
                        label_visibility="collapsed"
                    )

                with col2:
                    def update_segment_text(idx=i):
                        st.session_state["segments"][idx]["transcript"] = st.session_state[f"transcript_text_{idx}"]
                        self.save_segments()
                    st.text_area(
                        "Transcribed Text",
                        value=segment.get("transcript", ""),
                        key=f"transcript_text_{i}",
                        on_change=update_segment_text,
                        label_visibility="collapsed",
                        height=120
                    )

                with col3:
                    def update_segment_translation(idx=i):
                        st.session_state["segments"][idx]["translation"] = st.session_state[f"translation_text_{idx}"]
                        self.save_segments()
                    st.text_area(
                        "Translated Text",
                        value=segment.get("translation", ""),
                        key=f"translation_text_{i}",
                        on_change=update_segment_translation,
                        label_visibility="collapsed",
                        height=120
                    )

                with col4:
                    def update_segment_speaker(idx=i):
                        st.session_state["segments"][idx]["speaker"] = st.session_state[f"speaker_{idx}"]
                        self.save_segments()
                    st.selectbox(
                        "Speaker",
                        options=SPEAKERS,
                        index=SPEAKERS.index(segment.get("speaker", "AP")),
                        key=f"speaker_{i}",
                        on_change=update_segment_speaker,
                        label_visibility="collapsed"
                    )

                with col5:
                    if st.button("Translate", key=f"translate_seg_{i}"):
                        if not target_lang:
                            st.error("Please select a target language first!")
                        else:
                            with st.spinner("Translating..."):
                                transcript_to_translate = st.session_state[f"transcript_text_{i}"]
                                st.session_state["segments"][i]["transcript"] = transcript_to_translate
                                openai_handler = self.get_openai_handler()
                                translation = openai_handler.translate(transcript_to_translate, language=target_lang)
                                st.session_state["segments"][i]["translation"] = translation
                                self.save_segments()
                                st.toast("Translated.")
                                st.rerun()

                    if st.button("Audio", key=f"regen_audio_{i}"):
                        if not target_lang:
                            st.error("Please select a target language first!")
                        else:
                            with st.spinner("Generating audio..."):
                                text_to_dub = st.session_state.get(f"translation_text_{i}") or st.session_state.get(f"transcript_text_{i}")
                                st.session_state["segments"][i]["translation"] = st.session_state.get(f"translation_text_{i}", "")
                                st.session_state["segments"][i]["transcript"] = st.session_state.get(f"transcript_text_{i}", "")
                                
                                lang_code = get_lang_codes()[target_lang]
                                speaker = st.session_state[f"speaker_{i}"]
                                
                                audio_file_path = dub_single_segment(
                                    text=text_to_dub,
                                    lang_code=lang_code,
                                    speaker=speaker,
                                    gtts_creds=dict(st.secrets["GOOGLE_CREDENTIALS"]),
                                    start_time=segment["start"],
                                    end_time=segment["end"],
                                )
                                
                                if audio_file_path:
                                    st.session_state[f"preview_audio_{i}"] = audio_file_path
                                else:
                                    st.error("Failed to generate audio.")
                    
                    if st.session_state.get(f"preview_audio_{i}"):
                        st.audio(st.session_state[f"preview_audio_{i}"])
                    
                    if st.session_state.get('confirm_delete_segment') == i:
                        st.warning("Do you want to proceed?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("Yes", key=f"confirm_delete_{i}"):
                                del st.session_state["segments"][i]
                                st.session_state['confirm_delete_segment'] = None
                                self.save_segments()
                                st.rerun()
                        with col_no:
                            if st.button("No", key=f"cancel_delete_{i}"):
                                st.session_state['confirm_delete_segment'] = None
                                st.rerun()
                    else:
                        if st.button("🗑️", key=f"delete_seg_{i}", help="Delete segment"):
                            st.session_state['confirm_delete_segment'] = i
                            st.rerun()

                st.divider()

                if st.button("＋", key=f"add_after_{i}", help="Add segment after"):
                    self.add_segment(i + 1)


    def dubbing_section(self, target_lang):
        is_video_input = "src_vid" in st.session_state

        st.subheader(f"3. Get Dubbed {'Video' if is_video_input else 'Audio'}")

        if st.button(f"Generate Dubbed {'Video' if is_video_input else 'Audio'}"):
            if not target_lang:
                st.error("Select a target language!")
                return

            srt_content = None
            if "segments" in st.session_state:
                # Sync all widget states to session state before dubbing
                for i, seg in enumerate(st.session_state["segments"]):
                    if f"speaker_{i}" in st.session_state:
                        st.session_state["segments"][i]["speaker"] = st.session_state[f"speaker_{i}"]
                    if f"transcript_text_{i}" in st.session_state:
                        st.session_state["segments"][i]["transcript"] = st.session_state[f"transcript_text_{i}"]
                    if f"translation_text_{i}" in st.session_state:
                        st.session_state["segments"][i]["translation"] = st.session_state[f"translation_text_{i}"]
                self.save_segments()

                srt_segments = []
                for i, segment in enumerate(st.session_state["segments"]):
                    start_time = ms_to_srt_time(segment["start"])
                    end_time = ms_to_srt_time(segment["end"])
                    text = " ".join(
                        segment.get("translation", segment.get("transcript", "")).split()
                    )
                    speaker = segment.get("speaker", "AP")
                    text_with_speaker = f"[SPEAKER: {speaker}]\n{text}"
                    srt_segments.append(
                        f"{i+1}\n{start_time} --> {end_time}\n{text_with_speaker}\n"
                    )
                srt_content = "\n".join(srt_segments)

            if not srt_content:
                st.error("No content to dub. Please use Segmentation to generate segments.")
                return

            if is_video_input:
                with st.spinner(
                    f"Generating {target_lang} video from segments..."
                ):
                    create_dubbed_video(
                        input_video_path=st.session_state["src_vid"],
                        text=None,
                        srt_content=srt_content,
                        lang_code=get_lang_codes()[target_lang],
                        output_video_path=self.output_path,
                        input_audio_path=self.audio_path,
                        gtts_creds=dict(st.secrets["GOOGLE_CREDENTIALS"]),
                    )
            else:  # Audio input
                final_audio_path = os.path.join(self.rootdir, "final_audio.mp3")
                with st.spinner(f"Generating {target_lang} audio from segments..."):
                    process_srt_and_join(
                        srt_content=srt_content,
                        language_code=get_lang_codes()[target_lang],
                        final_output=final_audio_path,
                        credentials=dict(st.secrets["GOOGLE_CREDENTIALS"]),
                    )
                st.session_state["final_audio_path"] = final_audio_path
                st.rerun()

        if is_video_input:
            if os.path.exists(self.output_path):
                _, container, _ = st.columns(
                    [self.SIDE, self.DEFAULT_WIDTH // 2, self.SIDE]
                )
                video_data = self.load_video_data(self.output_path)
                container.video(video_data)
                st.download_button(
                    label="Download Dubbed Video",
                    data=video_data,
                    file_name="dubbed_video.mp4",
                    mime="video/mp4",
                )
        else:  # Audio input
            final_audio_path = st.session_state.get("final_audio_path")
            if final_audio_path and os.path.exists(final_audio_path):
                _, container, _ = st.columns(
                    [self.SIDE, self.DEFAULT_WIDTH // 2, self.SIDE]
                )
                audio_data = self.load_video_data(final_audio_path)
                container.audio(audio_data)
                st.download_button(
                    label="Download Dubbed Audio",
                    data=audio_data,
                    file_name="dubbed_audio.mp3",
                    mime="audio/mp3",
                )
    
    def render(self):
        _, container, _ = st.columns([self.SIDE, self.DEFAULT_WIDTH // 2, self.SIDE])
        with container:
            st.title("Video/Audio Dubbing")
        
        self.setup_session_management()
        
        self.upload_media_section()

        if os.path.exists(self.audio_path) and os.path.getsize(self.audio_path) > 0:
            _, container, _ = st.columns([self.SIDE, self.DEFAULT_WIDTH // 2, self.SIDE])
            if st.session_state.get("src_vid") and os.path.exists(
                st.session_state["src_vid"]
            ):
                video_data = self.load_video_data(st.session_state["src_vid"])
                container.video(video_data)
            else:
                audio_data = self.load_video_data(self.audio_path)
                container.audio(audio_data)

            target_lang = st.selectbox(
                "Select Target Language for Translation",
                list(get_lang_codes().keys()),
                index=None,
                key="target_language_selectbox"
            )

            self.segments_section(target_lang)
            self.dubbing_section(target_lang)


def render_page():
    DubberPage.render_page() 
