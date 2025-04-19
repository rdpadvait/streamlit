import os
import time

import streamlit as st
from logger import logger
from src.cmd_utils import download_video, extract_audio
from src.dub import create_dubbed_video, get_lang_codes
from src.oai import OpenAIHandler
from src.pages.base_page import BasePage
from src.srt_ui import subtitle_editor
from src.srt_utils import convert_to_srt


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
        
        transcript_file = os.path.join(self.rootdir, "transcript.txt")
        translation_file = os.path.join(self.rootdir, "translation.txt")
        
        if os.path.exists(transcript_file):
            with open(transcript_file, "r") as f:
                st.session_state["transcript_text"] = f.read()
                
        if os.path.exists(translation_file):
            with open(translation_file, "r") as f:
                st.session_state["translated_text"] = f.read()
    
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
    
    def upload_video_section(self):
        st.subheader("1. Upload MP4 Video (up to 3 mins)")
        uploaded_file = st.file_uploader(
            "Download MP4 Video with Audio from https://www.clipto.com/media-downloader/youtube-downloader and upload here", 
            type=["mp4"], 
            key="video_uploader"
        )
        
        if "src_vid" not in st.session_state:
            if os.environ.get("LOCAL", False):
                st.info("Running in local mode")
                st.text_input("Enter video URL", key="video_url")
                if st.session_state.get("video_url"):
                    with st.spinner("Downloading video..."):
                        download_video(st.session_state["video_url"], self.input_path)
                        if extract_audio(self.input_path, self.audio_path):
                            st.success("Video downloaded successfully!")
                            st.session_state["src_vid"] = self.input_path
                        else:
                            logger.error("Error extracting audio.")
                            st.error("Error extracting audio.")
            if uploaded_file:
                with open(self.input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                if extract_audio(self.input_path, self.audio_path):
                    st.success("Video downloaded successfully!")
                    st.session_state["src_vid"] = self.input_path
                else:    
                    logger.error("Error extracting audio.")
                    st.error("Error extracting audio.")

    @staticmethod
    @st.cache_data
    def load_video_data(video_path: str):
        with open(video_path, "rb") as f:
            return f.read()
        
    @staticmethod
    @st.cache_resource
    def get_openai_handler():
        return OpenAIHandler(configs_dir="configs")
            
    def transcript_section(self):
        st.subheader("2. Edit Transcript (Optional)")
        
        if st.button("Transcribe"):
            with st.spinner("Transcribing audio..."):
                st.session_state["transcript_text"] = self.get_openai_handler().transcribe(
                    self.audio_path, 
                )
                transcript_file = os.path.join(self.rootdir, "transcript.txt")
                with open(transcript_file, "w") as f:
                    f.write(st.session_state["transcript_text"])
                    
        if "transcript_text" in st.session_state:
            st.text_area(
                "Transcript:",
                height=200,
                key="transcript_editor",
                value=st.session_state["transcript_text"],
                on_change=lambda: st.session_state.update(
                    {"transcript_text": st.session_state["transcript_editor"]}
                ),
            )
    
    def translation_section(self):
        st.subheader("3. Translation")
        
        target_lang = st.selectbox(
            "Select Target Language", 
            list(get_lang_codes().keys()), 
            index=None,
            key="target_language_selectbox"
        )
        
        if st.button("Translate"):
            if "transcript_text" not in st.session_state:
                st.error("Transcribe the audio first!")
            else:
                if not target_lang:
                    st.error("Select a target language!")
                    return
                with st.spinner(f"Translating to {target_lang}..."):
                    st.session_state["translated_text"] = self.get_openai_handler().translate(
                        st.session_state["transcript_text"], 
                        language=target_lang
                    )
                    st.session_state["hindi_retranslation"] = self.get_openai_handler().translate(
                        st.session_state["translated_text"], 
                        language="Hindi"
                    )

        def update_translation():
            st.session_state.update({"translated_text": st.session_state["translation_editor"]})
            translation_file = os.path.join(self.rootdir, "translation.txt")
            with open(translation_file, "w") as f:
                f.write(st.session_state["translation_editor"])

        st.text_area(
            "Translation:",
            height=200,
            key="translation_editor",
            value=st.session_state.get("translated_text", ""),
            on_change=update_translation,
        )
        
        if "hindi_retranslation" in st.session_state:
            if st.button("Translate back to Hindi"):
                with st.spinner("Retranslating to Hindi..."):
                    st.session_state["hindi_retranslation"] = translate(
                        st.session_state["translated_text"], 
                        language="Hindi"
                    )
            st.text_area(
                "Hindi Retranslation:",
                value=st.session_state["hindi_retranslation"],
                height=100,
                key="hindi_retranslation_display",
                disabled=True,
            )
    
    def subtitles_section(self):
        st.markdown("### OR")
        st.divider()
        st.markdown("### Edit SRT")
        
        subtitle_editor()
        
        if st.button("Upload SRT"):       
            try:
                out = convert_to_srt(st.session_state)
                st.session_state["srt_content"] = out[0]
                logger.info(f"SRT uploaded:\n```{st.session_state['srt_content']}```")
                st.success("Valid SRT uploaded!")
            except Exception as e:
                logger.error(f"Error: {e}")
                st.error(f"Error: {e}")
                
        if "srt_content" in st.session_state:
            st.text_area("**Check SRT:**", st.session_state["srt_content"], height=200, disabled=True)
            
        st.divider()
    
    def dubbing_section(self, target_lang):
        st.subheader("4. Get Dubbed Video")
        
        if st.button("Generate Dubbed Video"):
            if not target_lang:
                st.error("Select a target language!")
                return
                
            with st.spinner(f"Generating {target_lang} video from {'SRT' if 'srt_content' in st.session_state else 'translated text'}..."):
                create_dubbed_video(
                    input_video_path=st.session_state["src_vid"],
                    text=st.session_state.get("translated_text"),
                    srt_content=st.session_state.get("srt_content"),
                    lang_code=get_lang_codes()[target_lang],
                    output_video_path=self.output_path,
                    input_audio_path=self.audio_path,
                    gtts_creds=dict(st.secrets["GOOGLE_CREDENTIALS"]),
                )
            
        if os.path.exists(self.output_path):
            _, container, _ = st.columns([self.SIDE, self.DEFAULT_WIDTH // 2, self.SIDE])
            video_data = self.load_video_data(self.output_path)
            container.video(video_data)
            st.download_button(
                label="Download Dubbed Video",
                data=video_data,
                file_name="dubbed_video.mp4",
                mime="video/mp4",
            )
    
    def render(self):
        _, container, _ = st.columns([self.SIDE, self.DEFAULT_WIDTH // 2, self.SIDE])
        with container:
            st.title("Short Video Dubbing")
        
        self.setup_session_management()
        
        self.upload_video_section()
        
        if st.session_state.get("src_vid") and os.path.exists(st.session_state["src_vid"]):
            _, container, _ = st.columns([self.SIDE, self.DEFAULT_WIDTH // 2, self.SIDE])
            video_data = self.load_video_data(st.session_state["src_vid"])
            container.video(video_data)
            
            self.transcript_section()
            
            self.translation_section()
            
            target_lang = st.session_state.get("target_language_selectbox", None)
            
            self.subtitles_section()
            
            self.dubbing_section(target_lang)


def render_page():
    DubberPage.render_page() 