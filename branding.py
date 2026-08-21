"""
وحدة مشتركة لعرض شعار NxN وتطبيق ألوان الهوية البصرية داخل صفحات Streamlit.
"""
import streamlit as st

BRAND_LIME = "#44D62C"
BRAND_BLUE = "#1E22AA"
BRAND_PURPLE = "#963CBD"


def render_logo(size: str = "large"):
    """يعرض شعار NxN (نص مصمم) أعلى الصفحة."""
    font_size = "64px" if size == "large" else "36px"
    tagline_size = "16px" if size == "large" else "12px"

    st.markdown(
        f"""
        <div style="text-align:center; padding: 8px 0 18px 0;">
            <div style="
                font-family: Arial, sans-serif;
                font-weight: 800;
                font-style: italic;
                font-size: {font_size};
                color: {BRAND_LIME};
                letter-spacing: -3px;
                line-height: 1;
            ">nxn</div>
            <div style="
                font-family: Arial, sans-serif;
                font-weight: 600;
                font-size: {tagline_size};
                color: {BRAND_LIME};
                letter-spacing: 1px;
                margin-top: 6px;
            ">National x Network</div>
            <div style="
                font-family: Arial, sans-serif;
                font-weight: 600;
                font-size: {tagline_size};
                color: {BRAND_LIME};
                margin-top: 2px;
            ">الشبكة الوطنية</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_theme():
    """يطبّق تنسيقات إضافية (اتجاه RTL + لمسات من ألوان الهوية) على الصفحة الحالية."""
    st.markdown(
        f"""
        <style>
        .block-container {{ direction: rtl; }}
        h1, h2, h3 {{ color: {BRAND_BLUE}; }}
        .stButton>button {{
            background-color: {BRAND_LIME};
            color: white;
            border: none;
        }}
        .stButton>button:hover {{
            background-color: {BRAND_PURPLE};
            color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
