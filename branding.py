"""
وحدة مشتركة لعرض شعار NxN وتطبيق ألوان الهوية البصرية داخل صفحات Streamlit.
الألوان مأخوذة من دليل الهوية البصرية الرسمي لشركة NxN:
- Bright Lime Green : #44D62C
- Cerulean Blue      : #1E22AA
- Amethyst Purple    : #963CBD
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


def apply_theme(direction: str = "rtl"):
    """يطبّق تنسيقات إضافية (اتجاه الصفحة + لمسات من ألوان الهوية) على الصفحة الحالية."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Cairo:wght@400;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', 'Cairo', sans-serif;
        }}
        .block-container {{ direction: {direction}; }}
        h1, h2, h3 {{ color: {BRAND_BLUE}; font-weight: 800; }}

        [data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid #ECECF4;
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: 0 2px 8px rgba(30, 34, 170, 0.06);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(30, 34, 170, 0.12);
        }}

        .stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {{
            background-color: {BRAND_LIME};
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            transition: background-color 0.15s ease, transform 0.1s ease;
        }}
        .stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover {{
            background-color: {BRAND_PURPLE};
            color: white;
            transform: translateY(-1px);
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FAFAFF 0%, #F3F3FC 100%);
        }}

        div[data-testid="stDataFrame"] thead tr th {{
            background-color: {BRAND_BLUE} !important;
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
