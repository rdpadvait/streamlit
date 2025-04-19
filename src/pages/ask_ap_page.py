import random

import streamlit as st
from logger import logger
from src.answer import AssistantInteraction as AskAPAssistant
from src.pages.base_page import BasePage
from src.process import convert_to_embed_url_with_time
from src.utils import read


class AskAPPage(BasePage):
    DEFAULT_WIDTH = 60
    SIDE = max((100 - DEFAULT_WIDTH) / 2, 0.01)
    
    def __init__(self):
        self.assistant = self.get_assistant()
        self.example_questions = self.get_example_questions()        
        if "placeholder_question" not in st.session_state:
            st.session_state.placeholder_question = random.choice(self.example_questions)
        
        with open("src/styles/ask_ap.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    @staticmethod
    @st.cache_resource
    def get_assistant():
        return AskAPAssistant(
            "asst_P9VqwgPjaxFvTGsePZcmnGcB", "data/articles_relevant_keys.json"
        )
    
    @staticmethod
    @st.cache_data
    def get_example_questions() -> list:
        return read("data/search_bar.txt")
    
    def render(self):
        st.title("Ask AP")
        
        question = st.text_input(
            "Dummy",
            placeholder=st.session_state.placeholder_question,
            label_visibility="collapsed",
        ).strip()
        
        if question:
            st.markdown(
                f'<div class="question-container">{question}</div>', unsafe_allow_html=True
            )
            with st.spinner("Loading..."):
                try:
                    data = self.assistant.interact(question)
                    
                    header = data.get("header", "No header available.")
                    st.markdown(f"## {header}")
                    
                    insights = data.get("insights", [])
                    for idx, insight in enumerate(insights, start=1):
                        st.markdown(
                            f"## {idx}. {insight.get('quote', 'No quote available.')}"
                        )
                        if insight.get("article_url"):
                            _, container, _ = st.columns([self.SIDE, self.DEFAULT_WIDTH, self.SIDE])
                            container.markdown(
                                f"""
                                <div style="text-align: center; margin-bottom: 15px;">
                                    <a href="{insight['article_url']}" target="_blank" style="font-size: 28px; font-weight: bold; color: #80cbc4;">
                                        {insight['article_title']}
                                    </a>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        if insight.get("video_url"):
                            _, container, _ = st.columns([self.SIDE, self.DEFAULT_WIDTH, self.SIDE])
                            container.markdown(
                                f"""
                                <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin-bottom: 20px;">
                                    <iframe
                                        src="{convert_to_embed_url_with_time(insight['video_url'])}"
                                        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                                        frameborder="0"
                                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                        allowfullscreen
                                    ></iframe>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                except Exception as e:
                    logger.error(f"An error occurred: {e}")
                    st.error(f"An error occurred: {e}")


def render_page():
    AskAPPage.render_page()