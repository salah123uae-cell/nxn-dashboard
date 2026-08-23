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


def render_sidebar_logo():
    """يعرض شعار NxN مصغّر أعلى الشريط الجانبي الداكن (نفس أسلوب لوحة nxn الرسمية)."""
    st.sidebar.markdown(
        f"""
        <div style="text-align:center; padding: 18px 0 14px 0;">
            <div style="
                font-family: Arial, sans-serif;
                font-weight: 800;
                font-style: italic;
                font-size: 34px;
                color: {BRAND_LIME};
                letter-spacing: -2px;
                line-height: 1;
            ">nxn</div>
            <div style="
                font-family: Arial, sans-serif;
                font-weight: 600;
                font-size: 11px;
                color: #C7C9F5;
                letter-spacing: 1px;
                margin-top: 8px;
            ">منظومة الجودة المركزية</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_theme(direction: str = "rtl"):
    """يطبّق تنسيقات إضافية (اتجاه الصفحة + ألوان الهوية) على الصفحة الحالية.
    الشريط الجانبي بلون كحلي داكن متدرّج (مطابق للوحة تحكم NxN الرسمية)."""
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Tahoma, Arial, "Noto Sans Arabic", sans-serif;
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

        /* ---------- الشريط الجانبي: كحلي داكن متدرّج، مطابق لهوية NxN الرسمية ---------- */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #1E1B4B 0%, #14123A 100%);
        }}
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption {{
            color: #C7C9F5 !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,0.12) !important;
        }}
        /* روابط التنقّل بالقائمة الجانبية */
        [data-testid="stSidebar"] a,
        [data-testid="stSidebarNav"] a {{
            color: #DADCFF !important;
            border-radius: 10px !important;
        }}
        [data-testid="stSidebar"] a:hover,
        [data-testid="stSidebarNav"] a:hover {{
            background: rgba(255,255,255,0.08) !important;
            color: #FFFFFF !important;
        }}
        [data-testid="stSidebar"] a[aria-current="page"],
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: {BRAND_LIME} !important;
            color: #14123A !important;
            font-weight: 700 !important;
        }}
        /* أزرار تبديل اللغة وتسجيل الخروج بالشريط الجانبي تبقى بألوان الهوية الزاهية */
        [data-testid="stSidebar"] .stButton>button {{
            background-color: {BRAND_LIME};
            color: #14123A;
            font-weight: 700;
        }}
        [data-testid="stSidebar"] .stButton>button:hover {{
            background-color: {BRAND_PURPLE};
            color: white;
        }}

        div[data-testid="stDataFrame"] thead tr th {{
            background-color: {BRAND_BLUE} !important;
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero_banner(title: str, subtitle: str = ""):
    """بطاقة ترحيبية بتدرّج بنفسجي-أزرق (نفس أسلوب لوحة nxn الرسمية) — للاستخدام أعلى الصفحة الرئيسية."""
    subtitle_html = f'<div style="font-size:15px; color:#EDEBFF; margin-top:8px; line-height:1.6;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(120deg, {BRAND_PURPLE} 0%, {BRAND_BLUE} 100%);
            border-radius: 20px; padding: 32px 36px; margin: 12px 0 24px 0;
            box-shadow: 0 8px 24px rgba(30, 34, 170, 0.18);
        ">
            <div style="font-size:12px; font-weight:700; letter-spacing:2px; color:{BRAND_LIME}; text-transform:uppercase;">NXN Quality Control</div>
            <div style="font-size:26px; font-weight:800; color:white; margin-top:8px;">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

