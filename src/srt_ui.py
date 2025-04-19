import os

import pandas as pd

import streamlit as st
from src.dub import SPEAKERS, dub_single_segment, get_lang_codes
from src.srt_utils import convert_time, convert_to_srt


def subtitle_editor():
    st.markdown("""
    <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 16px;
        }
        .delete-button {
            background-color: transparent;
            border: none;
            color: red;
            font-size: 20px;
        }
        .delete-button:hover {
            color: darkred;
        }
    </style>
    """, unsafe_allow_html=True)
    if "subtitles" not in st.session_state:
        if os.path.exists(st.session_state.srt_df_path):
            try:
                st.session_state.subtitles = pd.read_csv(st.session_state.srt_df_path).to_dict(orient="records")
            except pd.errors.EmptyDataError:
                st.session_state.subtitles = []
        else:
            st.session_state.subtitles = []

    def save_srt():
        try:
            st.session_state.subtitles = convert_to_srt(st.session_state)[1]
            return True
        except Exception as e:
            st.warning(f"{e}")
            return False
        
    def save_row(i):
        st.session_state.subtitles[i] = {
            "start": st.session_state[f"start_{i}"],
            "end": st.session_state[f"end_{i}"],
            "text": st.session_state[f"text_{i}"],
            "speaker": st.session_state[f"speaker_{i}"]
        }

    def dub_segment(i):
        if not save_srt():
            return
        text = st.session_state[f"text_{i}"]
        speaker = st.session_state[f"speaker_{i}"]
        lang_code = st.session_state.get("target_language_selectbox")
        if not lang_code:
            st.error("Please select a target language first!")
            return
            
        with st.spinner(f"Dubbing segment {i+1}..."):
            try:
                st.session_state[f"segment_audio_{i}"] = dub_single_segment(
                    text, 
                    get_lang_codes()[lang_code], 
                    speaker=speaker,
                    gtts_creds=dict(st.secrets["GOOGLE_CREDENTIALS"]),
                    start_time=convert_time(st.session_state[f"start_{i}"], to_ms=True, segment=i+1),
                    end_time=convert_time(st.session_state[f"end_{i}"], to_ms=True, segment=i+1)
                )
                st.success(f"Segment {i+1} dubbed 🎉")
            except Exception as e:
                st.error(f"Error dubbing segment {i+1}: {str(e)}")

    for i, row in enumerate(st.session_state.subtitles):
        st.markdown(f"##### Segment {i+1}")
        cols = st.columns([1, 1, 2, 0.5, 0.6, 0.2])
        with cols[0]:
            st.text_input("Start Time (seconds or MM:SS,MS)", key=f"start_{i}", value=row["start"], on_change=save_row, args=(i,))
        with cols[1]:
            st.text_input("End Time (seconds or MM:SS,MS)", key=f"end_{i}", value=row["end"], on_change=save_row, args=(i,))
        with cols[2]:
            st.text_area("Translated Text", key=f"text_{i}", value=row["text"], height=80, on_change=save_row, args=(i,))
        with cols[3]:
            st.selectbox("Speaker", SPEAKERS, key=f"speaker_{i}", index=SPEAKERS.index(row.get("speaker", "AP")), on_change=save_row, args=(i,))
        with cols[4]:
            if st.button("Generate Audio", key=f"dub_{i}", use_container_width=True):
                dub_segment(i)
        with cols[5]:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.subtitles.pop(i)
                st.rerun()  
        
        if f"segment_audio_{i}" in st.session_state:
            st.audio(st.session_state[f"segment_audio_{i}"])

    save_srt()
    if st.button("➕ Add New Segment", use_container_width=True):
        st.session_state.subtitles.append({"start": "", "end": "", "text": "", "speaker": "AP"})
        st.rerun()
    
    st.write("##### Saved SRT")
    df = pd.DataFrame(st.session_state.subtitles)
    st.dataframe(df, use_container_width=True, hide_index=True)