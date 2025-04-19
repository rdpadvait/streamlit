import streamlit as st
from src.pages.base_page import BasePage
from src.replier import ReplierAssistant, ReplierChat


class ReplierPage(BasePage):
    def __init__(self):
        self.assistant = self.get_assistant()
        self.chat = self.get_chat()
    
    @staticmethod
    @st.cache_resource
    def get_assistant():
        return ReplierAssistant(
            "asst_jx8UcIoFjYfZhWdVvAxuNVfu", mapping_file="data/articles_relevant_keys.json"
        )
    
    @staticmethod
    @st.cache_resource
    def get_chat():
        return ReplierChat("configs/replier.yaml")
    
    def render(self):
        st.title("Replier")
        
        post = st.text_area(
            "Enter post to reply to:",
            height=200,
            key="post_input",
            placeholder="Enter post here...",
        )
        
        if st.button("Generate Reply"):
            if not post:
                st.error("Please enter a post first!")
                return
            
            with st.spinner("Generating reply..."):
                st.markdown(f"### {self.chat.reply(post)}", unsafe_allow_html=True)


def render_page():
    """Entry point for the Replier page."""
    ReplierPage.render_page() 