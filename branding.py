"""Header and footer banners matching the Snow Analytics brand (navy #00113D).

Both are fixed to the full browser viewport width, top and bottom, sized to
sit outside the app's own content flow. Matches Product Inventory and
Sales's branding.py pattern.
"""

import base64
from datetime import datetime
from pathlib import Path

import streamlit as st

BRAND_NAVY = "#00113D"
LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"
HEADER_HEIGHT_PX = 72
FOOTER_HEIGHT_PX = 44


def render_header() -> None:
    logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    st.markdown(
        f"""
        <style>
        .app-header {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: {HEADER_HEIGHT_PX}px;
            z-index: 999999;
            background-color: {BRAND_NAVY};
            padding: 0 1.5rem;
            display: flex;
            align-items: center;
            box-sizing: border-box;
        }}
        .app-header img {{
            height: 44px;
            display: block;
        }}
        [data-testid="stSidebar"] {{
            top: {HEADER_HEIGHT_PX}px !important;
            height: calc(100vh - {HEADER_HEIGHT_PX}px - {FOOTER_HEIGHT_PX}px) !important;
        }}
        [data-testid="stExpandSidebarButton"] {{
            position: fixed !important;
            top: {HEADER_HEIGHT_PX + 12}px !important;
            left: 18px !important;
            z-index: 999998 !important;
        }}
        [data-testid="stMainBlockContainer"] {{
            padding-top: calc({HEADER_HEIGHT_PX}px + 2rem) !important;
            padding-bottom: calc({FOOTER_HEIGHT_PX}px + 2rem) !important;
        }}
        </style>
        <div class="app-header"><img src="data:image/png;base64,{logo_b64}" alt="Snow Analytics"></div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    year = datetime.now().year
    st.markdown(
        f"""
        <style>
        .app-footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100vw;
            height: {FOOTER_HEIGHT_PX}px;
            z-index: 999999;
            background-color: {BRAND_NAVY};
            color: #E5E9F0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            box-sizing: border-box;
        }}
        </style>
        <div class="app-footer">© {year} Snow Analytics, LLC</div>
        """,
        unsafe_allow_html=True,
    )
