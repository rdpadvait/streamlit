import importlib
from pathlib import Path

import streamlit as st
from logger import logger

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

@st.cache_data
def load_css(css_path: Path = Path("src/styles/main.css")):
    if css_path.exists():
        with open(css_path) as f:
            return f"<style>{f.read()}</style>"
    else:
        logger.error(f"CSS file not found at {css_path}")
        st.error(f"CSS file not found at {css_path}")
        return ""

PAGE_MODULES = {
    "Dubber": "src.pages.dubber_page",
    "Ask AP": "src.pages.ask_ap_page",
}

def load_page(page_name):
    try:
        module_path = PAGE_MODULES[page_name]
        module = importlib.import_module(module_path)
        render_func = getattr(module, "render_page")
        render_func()
    except (ImportError, AttributeError) as e:
        logger.error(f"Error loading page {page_name}: {str(e)}")
        st.error(f"Error loading page {page_name}: {str(e)}")

def main():
    style = load_css()
    st.markdown(style, unsafe_allow_html=True)
    
    _, col = st.columns([0.8, 0.2])
    with col:
        page = st.selectbox("Select Page", list(PAGE_MODULES.keys()), index=0)
    
    load_page(page)

if __name__ == "__main__":
    main()