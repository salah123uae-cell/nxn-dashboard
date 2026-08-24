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
    """يطبّق هوية بصرية شاملة ومبتكرة على كل صفحات النظام: تدرجات لونية، بطاقات
    عصرية بظلال ناعمة، أزرار متحركة، تبويبات على شكل كبسولات، حقول إدخال أنعم،
    وجداول أنيقة — كل هذا مبني على ألوان هوية NxN الرسمية."""
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Tahoma, Arial, "Noto Sans Arabic", sans-serif;
        }}
        .block-container {{
            direction: {direction};
            padding-top: 2.2rem;
            max-width: 1200px;
        }}

        /* ---------- خلفية المحتوى: تدرّج خفيف جدًا بدل الأبيض المسطّح ---------- */
        [data-testid="stAppViewContainer"] > .main {{
            background: linear-gradient(180deg, #FAFBFF 0%, #F4F5FC 60%, #F0F1FA 100%);
        }}

        /* ---------- العناوين ---------- */
        h1, h2, h3 {{ color: {BRAND_BLUE}; font-weight: 800; }}

        /* ---------- بطاقات المقاييس (Metrics) ---------- */
        [data-testid="stMetric"] {{
            background: #FFFFFF;
            border: none;
            border-top: 3px solid {BRAND_LIME};
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: 0 4px 18px rgba(30, 34, 170, 0.08);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(30, 34, 170, 0.16);
        }}
        [data-testid="stMetricValue"] {{ color: {BRAND_BLUE}; font-weight: 800; }}

        /* ---------- الأزرار: تدرّج لوني مع ظل وحركة رفع عند التحويم ---------- */
        .stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {{
            background: linear-gradient(135deg, {BRAND_LIME} 0%, #2FA81D 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            padding: 0.55rem 1.3rem;
            box-shadow: 0 4px 14px rgba(68, 214, 44, 0.28);
            transition: all 0.2s ease;
        }}
        .stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover {{
            background: linear-gradient(135deg, {BRAND_PURPLE} 0%, {BRAND_BLUE} 100%);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 10px 22px rgba(150, 60, 189, 0.32);
        }}
        .stButton>button:active, .stFormSubmitButton>button:active {{
            transform: translateY(0);
        }}

        /* ---------- التبويبات (st.tabs): شكل كبسولة عصري بدل الخط السفلي التقليدي ---------- */
        [data-baseweb="tab-list"] {{
            gap: 6px;
            background: #EEF0FB;
            padding: 6px;
            border-radius: 14px;
        }}
        [data-baseweb="tab"] {{
            border-radius: 10px !important;
            font-weight: 600;
            color: {BRAND_BLUE} !important;
            transition: all 0.2s ease;
        }}
        [data-baseweb="tab-highlight"] {{ background: transparent !important; }}
        [aria-selected="true"][data-baseweb="tab"] {{
            background: white !important;
            box-shadow: 0 3px 10px rgba(30,34,170,0.14);
            color: {BRAND_PURPLE} !important;
        }}

        /* ---------- الحقول النصية وحقول الأرقام والتاريخ ---------- */
        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {{
            border-radius: 12px !important;
            border: 1.5px solid #E3E4F6 !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {{
            border-color: {BRAND_PURPLE} !important;
            box-shadow: 0 0 0 3px rgba(150,60,189,0.12) !important;
        }}

        /* ---------- القوائم المنسدلة ---------- */
        [data-baseweb="select"] > div {{
            border-radius: 12px !important;
            border: 1.5px solid #E3E4F6 !important;
        }}

        /* ---------- الحاويات ذات الحدود (st.container(border=True)) ---------- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px !important;
            transition: box-shadow 0.2s ease;
        }}

        /* ---------- التنبيهات (info/success/warning/error) ---------- */
        [data-testid="stAlert"] {{
            border-radius: 14px;
            border: none;
        }}

        /* ---------- الفواصل والجداول ---------- */
        hr {{ border-color: #E3E4F6; }}
        div[data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 4px 18px rgba(30,34,170,0.07);
        }}
        div[data-testid="stDataFrame"] thead tr th {{
            background: linear-gradient(90deg, {BRAND_BLUE}, {BRAND_PURPLE}) !important;
            color: white !important;
            font-weight: 700;
        }}

        /* ---------- الشريط الجانبي: كحلي داكن متدرّج، مطابق لهوية NxN الرسمية ---------- */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #1E1B4B 0%, #14123A 100%);
        }}
        /* إعادة ترتيب بصري: الشعار المخصّص يظهر أولًا (فوق)، ثم قائمة التنقّل الرسمية تحته مباشرة */
        [data-testid="stSidebarContent"] {{
            display: flex;
            flex-direction: column;
        }}
        [data-testid="stSidebarNav"] {{
            order: 2;
        }}
        [data-testid="stSidebarUserContent"] {{
            order: 1;
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
            background: {BRAND_LIME};
            color: #14123A;
            font-weight: 700;
            box-shadow: none;
        }}
        [data-testid="stSidebar"] .stButton>button:hover {{
            background: {BRAND_PURPLE};
            color: white;
        }}
        /* قائمة تبديل اللغة المنسدلة بالشريط الجانبي — مندمجة مع الخلفية الداكنة */
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background: rgba(255,255,255,0.08) !important;
            border: 1.5px solid rgba(255,255,255,0.18) !important;
            color: white !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] * {{
            color: white !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] svg {{
            fill: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_card(content_html: str, accent: str = None):
    """بطاقة عامة بحواف مدورة وظل ناعم — لتغليف أي محتوى HTML مخصص بمظهر موحّد."""
    accent = accent or BRAND_LIME
    st.markdown(
        f"""
        <div style="
            background: white; border-radius: 16px; padding: 20px 22px;
            box-shadow: 0 4px 16px rgba(30,34,170,0.07);
            border-right: 4px solid {accent};
            margin-bottom: 14px;
        ">
            {content_html}
        </div>
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

