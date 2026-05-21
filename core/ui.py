from __future__ import annotations

import streamlit as st


def apply_app_style(max_width_px: int = 1280, top_padding_rem: float = 1.4) -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: #f6f7fb;
            color: #111827;
        }}
        [data-testid="stHeader"] {{
            background: rgba(246, 247, 251, 0.9);
        }}
        .block-container {{
            padding-top: {top_padding_rem}rem;
            max-width: {max_width_px}px;
        }}
        .block-container h1 {{
            margin-bottom: 0.2rem;
        }}
        .block-container h2,
        .block-container h3 {{
            margin-top: 1.15rem;
        }}
        .block-container,
        .block-container h1,
        .block-container h2,
        .block-container h3,
        .block-container p,
        .block-container li,
        .block-container label,
        .block-container span {{
            color: #111827;
        }}
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] * {{
            color: #475467 !important;
        }}
        div[data-testid="stMetric"] {{
            background: #ffffff;
            border: 1px solid #d0d5dd;
            padding: 0.65rem 0.8rem;
            border-radius: 0.45rem;
            color: #111827;
        }}
        div[data-testid="stMetric"] * {{
            color: #111827;
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid #d0d5dd;
            border-radius: 0.45rem;
            overflow: hidden;
            background: #ffffff;
        }}
        div[data-testid="stDataFrame"] * {{
            color: #111827;
        }}
        button[data-baseweb="tab"] {{
            color: #374151 !important;
            font-weight: 650 !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: #064d26 !important;
            border-bottom-color: #075e2d !important;
        }}
        div[data-testid="stProgress"] * {{
            color: #111827 !important;
        }}
        div[data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {{
            background: #f8fafc;
            color: #111827;
        }}
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] small {{
            color: #111827 !important;
        }}
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea,
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
        section[data-testid="stSidebar"] div[data-baseweb="base-input"] {{
            background: #ffffff !important;
            color: #111827 !important;
            border-color: #cbd5e1 !important;
        }}
        section[data-testid="stSidebar"] input::placeholder {{
            color: #667085 !important;
        }}
        section[data-testid="stSidebar"] svg {{
            color: #344054;
            fill: #344054;
        }}
        div[data-testid="stExpander"] details summary {{
            background: #075e2d !important;
            border: 1px solid #064d26 !important;
            border-radius: 0.45rem !important;
        }}
        div[data-testid="stExpander"] details summary,
        div[data-testid="stExpander"] details summary * {{
            color: #ffffff !important;
            font-weight: 650 !important;
        }}
        div[data-testid="stExpander"] details summary:hover {{
            background: #05431f !important;
        }}
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stPageLink"] a {{
            background: #075e2d !important;
            color: #ffffff !important;
            border: 1px solid #064d26 !important;
            border-radius: 0.45rem !important;
            font-weight: 650 !important;
            text-decoration: none !important;
            box-shadow: none !important;
        }}
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stPageLink"] a:hover {{
            background: #05431f !important;
            color: #ffffff !important;
            border-color: #043619 !important;
        }}
        div[data-testid="stButton"] > button:focus,
        div[data-testid="stDownloadButton"] > button:focus,
        div[data-testid="stFormSubmitButton"] > button:focus,
        div[data-testid="stPageLink"] a:focus {{
            color: #ffffff !important;
            border-color: #ffffff !important;
            box-shadow: 0 0 0 0.16rem rgba(7, 94, 45, 0.35) !important;
        }}
        div[data-testid="stButton"] > button:disabled,
        div[data-testid="stDownloadButton"] > button:disabled,
        div[data-testid="stFormSubmitButton"] > button:disabled {{
            background: #f3f4f6 !important;
            color: #374151 !important;
            border-color: #9ca3af !important;
        }}
        .home-note,
        .wizard-panel {{
            background: #ffffff;
            border: 1px solid #d0d5dd;
            border-radius: 0.45rem;
            padding: 0.85rem 1rem;
            margin: 0.5rem 0 1rem;
        }}
        .home-note strong,
        .wizard-panel strong {{
            color: #111827;
        }}
        .auto-recalc-banner {{
            margin: 0.4rem 0 1.1rem;
            padding: 0.7rem 0.85rem;
            border: 1px solid #b7e4c7;
            background: #ecfdf3;
            border-radius: 0.45rem;
            color: #054f31;
            font-weight: 650;
        }}
        .auto-recalc-banner span {{
            color: #054f31;
            font-weight: 500;
        }}
        .status-badge {{
            display: inline-block;
            padding: 0.18rem 0.5rem;
            border-radius: 999px;
            color: #ffffff !important;
            font-size: 0.78rem;
            font-weight: 650;
            line-height: 1.25;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
