import html
import json
import os

import requests
import streamlit as st
from markdown_it import MarkdownIt
from streamlit.components.v1 import html as component_html

API_URL = os.environ.get("API_URL", "http://localhost:8000")
PUBLIC_API_URL = os.environ.get("PUBLIC_API_URL", API_URL)

# Markdown renderer for assistant messages. html=False keeps raw HTML inside
# the model's reply escaped (we don't trust the LLM to emit safe HTML); linkify
# turns plain URLs into clickable links.
_MD = MarkdownIt("commonmark", {"html": False, "linkify": True, "breaks": True})

_FAVICON_PATH = os.path.join(os.path.dirname(__file__), "favicon.svg")
st.set_page_config(
    page_title="AI Agent with RAG",
    page_icon=_FAVICON_PATH,
    layout="wide",
)

# ── CSS (Liquid Glass) ───────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --blue: #0A84FF;
        --blue-hover: #0066CC;
        --blue-soft: rgba(10,132,255,0.10);
        --blue-tint: rgba(10,132,255,0.06);
        --ink: #081936;
        --ink-2: #52627F;
        --muted: #6D7B99;
        /* Glass tokens */
        --glass-bg: rgba(255, 255, 255, 0.38);
        --glass-bg-strong: rgba(255, 255, 255, 0.56);
        --glass-bg-soft: rgba(255, 255, 255, 0.24);
        --glass-border: rgba(255, 255, 255, 0.92);
        --glass-border-2: rgba(159, 184, 222, 0.28);
        --glass-line: rgba(95, 116, 150, 0.16);
        --line: rgba(140,166,206,0.26);
        --shadow-sm: 0 1px 2px rgba(26,44,82,0.06), 0 8px 24px -18px rgba(26,44,82,0.28);
        --shadow-md: 0 20px 60px -34px rgba(33,57,98,0.36), 0 8px 24px -18px rgba(33,57,98,0.28);
        --shadow-lg: 0 34px 90px -46px rgba(35,58,95,0.44), 0 12px 32px -24px rgba(35,58,95,0.34);
        --inner-hl: inset 0 1px 0 rgba(255,255,255,0.96), inset 0 -1px 0 rgba(255,255,255,0.72), inset 0 0 0 1px rgba(255,255,255,0.42);
        --glass-sheen: linear-gradient(135deg, rgba(255,255,255,0.88) 0%, rgba(255,255,255,0.28) 36%, rgba(255,255,255,0.04) 58%);
        --radius: 24px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
        color: var(--ink);
        -webkit-font-smoothing: antialiased;
    }

    #MainMenu, footer, .stDeployButton, [data-testid="stDecoration"],
    .stAppToolbar, [data-testid="stHeader"] { display: none !important; }

    /* ── Liquid Glass background: frosted white surface ── */
    .stApp {
        background:
            radial-gradient(ellipse 68% 62% at 55% 13%, rgba(255,255,255,0.96), transparent 58%),
            radial-gradient(ellipse 58% 52% at 10% 4%, rgba(188,216,255,0.32), transparent 60%),
            radial-gradient(ellipse 62% 58% at 100% 0%, rgba(211,226,255,0.36), transparent 60%),
            linear-gradient(135deg, #F8FBFF 0%, #EFF5FE 48%, #F8FAFF 100%) !important;
        background-attachment: fixed !important;
        color: var(--ink);
    }
    .stApp::before {
        content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
        background:
            radial-gradient(circle at 35% 25%, rgba(12,102,255,0.22) 0 1px, transparent 2px),
            radial-gradient(circle at 87% 26%, rgba(12,102,255,0.18) 0 1px, transparent 2px),
            radial-gradient(circle at 36% 32%, rgba(12,102,255,0.18) 0 1px, transparent 2px),
            radial-gradient(circle at 90% 34%, rgba(12,102,255,0.16) 0 1px, transparent 2px);
        opacity: 0.9;
    }
    .stApp::after {
        content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
        background:
            url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1400 520' preserveAspectRatio='none'><defs><filter id='b'><feGaussianBlur stdDeviation='8'/></filter><linearGradient id='g' x1='0' x2='1'><stop offset='0' stop-color='%23ffffff' stop-opacity='0'/><stop offset='0.5' stop-color='%23ffffff' stop-opacity='0.92'/><stop offset='1' stop-color='%23ffffff' stop-opacity='0'/></linearGradient></defs><path d='M0 250 C210 360 390 175 575 112 C800 36 940 95 1098 205 C1225 294 1335 270 1400 235' fill='none' stroke='%23c9d9f4' stroke-opacity='0.28' stroke-width='18' filter='url(%23b)'/><path d='M0 246 C220 352 390 168 575 106 C798 30 948 90 1106 198 C1230 284 1336 262 1400 227' fill='none' stroke='url(%23g)' stroke-width='5'/><path d='M0 330 C210 390 370 250 540 240 C760 226 835 350 1010 342 C1170 334 1232 238 1400 300' fill='none' stroke='%23ffffff' stroke-opacity='0.68' stroke-width='3' filter='url(%23b)'/><path d='M0 334 C210 392 370 252 540 242 C760 228 835 352 1010 344 C1170 336 1232 240 1400 302' fill='none' stroke='%23d4e2fb' stroke-opacity='0.46' stroke-width='1.5'/></svg>"),
            linear-gradient(115deg, transparent 0 36%, rgba(255,255,255,0.28) 48%, transparent 60% 100%);
        background-size: 100% 54vh, 100% 100%;
        background-repeat: no-repeat;
        background-position: top 56px center, center;
    }
    [data-testid="stAppViewContainer"] { background: transparent !important; }
    [data-testid="stMain"] { background: transparent !important; }
    .main .block-container { padding-top: 30px !important; padding-bottom: 150px !important; max-width: 1240px; position: relative; z-index: 1; }

    /* ── Hide sidebar collapse arrow ──────────── */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"],
    [data-testid="stLogoSpacer"],
    [data-testid="stSidebarHeader"] button {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* ── Sidebar: liquid glass card ──────────── */
    [data-testid="stSidebar"] {
        background: transparent !important;
        border-right: none !important;
        padding: 12px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background: rgba(255,255,255,0.30) !important;
        backdrop-filter: blur(42px) saturate(180%) brightness(1.06) !important;
        -webkit-backdrop-filter: blur(42px) saturate(180%) brightness(1.06) !important;
        border: 1px solid rgba(255,255,255,0.82) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--inner-hl), 0 26px 80px -46px rgba(31,59,101,0.46), 0 1px 0 rgba(255,255,255,0.82) !important;
        padding: 16px 16px !important;
        height: calc(100vh - 24px);
        overflow-y: auto;
    }
    section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 0; }
    [data-testid="stSidebarUserContent"] { padding-top: 0 !important; }

    /* ── Logo ────────────────────────────────── */
    .logo-row { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
    .logo-icon svg { width: 26px; height: 26px; }
    .logo-text { font-size: 17px; font-weight: 700; color: var(--ink); letter-spacing: -0.02em; }

    /* ── Sidebar section labels ──────────────── */
    .sidebar-label {
        font-size: 10px; font-weight: 700; color: #657796;
        text-transform: uppercase; letter-spacing: 0.08em;
        margin-bottom: 8px; margin-top: 12px;
    }

    /* ── File uploader (Apple light card) ────── */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] { margin-bottom: 12px; }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] label { display: none !important; }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"],
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        background: rgba(255,255,255,0.20) !important;
        backdrop-filter: blur(26px) saturate(170%) !important;
        -webkit-backdrop-filter: blur(26px) saturate(170%) !important;
        border: 1px dashed rgba(36,109,245,0.28) !important;
        border-radius: 14px !important;
        padding: 10px 12px 10px !important;
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        color: var(--ink) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.84), inset 0 0 32px rgba(255,255,255,0.30), var(--shadow-sm) !important;
        max-width: 100% !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] > span {
        order: 4 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {
        color: var(--ink) !important;
        margin-bottom: 8px !important;
        display: flex !important; flex-direction: column !important;
        align-items: center !important; text-align: center !important;
        width: 100% !important;
        max-width: 100% !important;
        overflow: hidden !important;
        order: 1 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] > div {
        display: flex !important; flex-direction: column !important;
        align-items: center !important; text-align: center !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"]::before {
        display: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] > div > svg:first-child { display: none !important; }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] > div > span,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] small {
        display: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"]::after {
        content: "Drag and drop file here\\A Limit 200MB per file\\A PDF, CSV, MD, TXT, HTML, HTM, JSON, DOCX";
        display: block;
        max-width: 170px;
        margin: 0 auto;
        color: var(--muted);
        font-size: 10px;
        line-height: 1.45;
        white-space: pre-line;
    }
    /* Browse files: glass pill with blue text + folder icon */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
        background: rgba(255,255,255,0.36) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        color: var(--blue) !important;
        border: 1px solid rgba(128,162,220,0.30) !important;
        border-radius: 12px !important;
        font-size: 12px !important; font-weight: 600 !important;
        padding: 7px 14px !important;
        box-shadow: var(--inner-hl), 0 8px 24px -16px rgba(15,30,60,0.24) !important;
        display: inline-flex !important; align-items: center !important; gap: 6px !important;
        order: 4 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
        background: rgba(255,255,255,0.9) !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button p { color: transparent !important; margin: 0 !important; font-size: 0 !important; }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button p::after {
        content: "Browse files";
        color: var(--blue);
        font-size: 12px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button::before {
        display: none !important;
    }

    /* ── Status card (Indexed: N chunks) ─────── */
    .status-card {
        display: flex; align-items: center; gap: 10px;
        background: rgba(255,255,255,0.28);
        backdrop-filter: blur(28px) saturate(180%);
        -webkit-backdrop-filter: blur(28px) saturate(180%);
        border: 1px solid rgba(255,255,255,0.72); border-radius: 14px;
        padding: 9px 12px; margin-bottom: 12px;
        box-shadow: var(--inner-hl), var(--shadow-sm);
        cursor: pointer;
    }
    .status-card .db-icon svg { width: 18px; height: 18px; color: var(--blue); }
    .status-card .status-text { flex: 1; }
    .status-card .status-text .status-main { font-size: 12px; font-weight: 650; color: var(--ink); }
    .status-card .status-text .status-sub { font-size: 10px; color: var(--muted); }
    .status-card .status-chevron { color: #C7C7CC; font-size: 14px; }

    /* ── File list ──────────────────────────── */
    .file-list {
        margin-bottom: 12px;
        background: rgba(255,255,255,0.26);
        border: 1px solid rgba(255,255,255,0.66);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: var(--inner-hl), var(--shadow-sm);
    }
    .file-row {
        display: flex; align-items: center; gap: 10px;
        padding: 7px 16px;
        border-radius: 0;
        border-bottom: 1px solid rgba(112,134,170,0.16);
        transition: background 0.15s ease;
    }
    .file-row:hover { background: var(--blue-tint); }
    .file-row:last-child { border-bottom: none; }
    .file-row .file-icon svg { width: 16px; height: 16px; color: var(--muted); flex-shrink: 0; }
    .file-row .file-info { flex: 1; min-width: 0; }
    .file-row .file-info .file-name {
        font-size: 13px; font-weight: 500; color: var(--ink);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .file-row .file-info .file-size { font-size: 11px; color: var(--muted); }
    .file-row .file-more { color: #C7C7CC; font-size: 16px; letter-spacing: 1px; flex-shrink: 0; }
    .doc-row-native {
        display: flex; align-items: center; gap: 10px;
        min-height: 46px;
        padding: 0 0 0 10px;
    }
    .doc-row-native .file-icon svg { width: 16px; height: 16px; color: var(--muted); }
    .doc-row-native .file-name {
        font-size: 13px; font-weight: 600; color: var(--ink);
        max-width: 132px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .doc-row-native .file-size { font-size: 11px; color: #60749A; margin-top: 2px; }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button {
        width: 28px !important;
        min-width: 28px !important;
        height: 30px !important;
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        color: #A5B0C4 !important;
        box-shadow: none !important;
        font-size: 20px !important;
        line-height: 1 !important;
        justify-content: center !important;
        align-items: center !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button p {
        margin: 0 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button svg {
        display: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {
        color: var(--blue) !important;
        background: rgba(10,132,255,0.08) !important;
    }
    .doc-menu-name {
        font-size: 12px;
        font-weight: 600;
        color: var(--ink);
        max-width: 210px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 8px;
    }
    .delete-doc-btn .stButton > button {
        color: #B42318 !important;
        border-color: rgba(180,35,24,0.22) !important;
        background: rgba(255,255,255,0.68) !important;
    }
    .doc-inline-menu {
        background: rgba(255,255,255,0.34);
        border: 1px solid rgba(255,255,255,0.62);
        border-radius: 12px;
        padding: 8px;
        margin: -2px 0 8px 34px;
        box-shadow: var(--inner-hl), var(--shadow-sm);
    }
    /* ── Sidebar utility buttons ── */
    .util-btn-row { margin-bottom: 8px; }
    .util-btn-row .stButton > button {
        display: flex !important; align-items: center !important; gap: 8px !important;
        background: rgba(255,255,255,0.28) !important;
        backdrop-filter: blur(28px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
        color: var(--ink) !important;
        border: 1px solid rgba(255,255,255,0.70) !important; border-radius: 12px !important;
        font-size: 13px !important; font-weight: 500 !important;
        height: 38px !important;
        min-height: 38px !important;
        padding: 7px 12px !important; width: 100% !important;
        justify-content: flex-start !important;
        box-shadow: var(--inner-hl), var(--shadow-sm) !important;
    }
    .util-btn-row .stButton > button:hover {
        background: rgba(255,255,255,0.7) !important;
    }
    .util-btn-row .stButton > button p { font-size: 13px !important; font-weight: 500 !important; margin: 0 !important; }
    .settings-btn .stButton > button::after {
        content: "›"; margin-left: auto; color: #C7C7CC; font-size: 18px;
    }
    .settings-btn.is-open .stButton > button::after {
        transform: rotate(90deg);
    }

    .sidebar-rule { height: 1px; background: var(--line); margin-top: 16px; }

    /* ── Top bar (Deploy + ⋮) ────────────────── */
    .top-bar { min-height: 42px; padding: 0 0 34px 0; }

    /* ── Hero ────────────────────────────────── */
    .hero-section {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center;
        padding: 92px 0 48px 0;
        position: relative;
        animation: floatIn 520ms ease-out both;
    }
    .hero-pill {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(255,255,255,0.34);
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        color: var(--blue); font-size: 13px; font-weight: 600;
        padding: 8px 18px; border-radius: 999px;
        margin-bottom: 24px;
        border: 1px solid rgba(255,255,255,0.78);
        box-shadow: var(--inner-hl), 0 10px 28px -18px rgba(42,70,118,0.34);
    }
    .hero-pill svg { width: 14px; height: 14px; }
    .hero-title {
        font-size: 64px; font-weight: 800; color: var(--ink);
        letter-spacing: -0.04em; line-height: 1.05; margin-bottom: 16px;
    }
    .hero-subtitle { font-size: 19px; font-weight: 400; color: #5F6F90; }

    @keyframes floatIn {
        from { opacity: 0; transform: translateY(14px) scale(0.99); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* ── Feature cards ───────────────────────── */
    .features-row {
        display: flex; gap: 34px; justify-content: center;
        padding: 10px 0 80px 0;
    }
    .feature-card {
        flex: 1; max-width: 286px; min-height: 230px;
        background: rgba(255,255,255,0.26);
        backdrop-filter: blur(34px) saturate(185%) brightness(1.06);
        -webkit-backdrop-filter: blur(34px) saturate(185%) brightness(1.06);
        border: 1px solid rgba(255,255,255,0.78); border-radius: 24px;
        padding: 36px 34px 30px;
        box-shadow: var(--inner-hl), var(--shadow-md);
        position: relative;
        overflow: hidden;
        transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
    }
    .feature-card::before {
        content: "";
        position: absolute;
        inset: 1px;
        border-radius: 23px;
        background: var(--glass-sheen);
        opacity: 0.52;
        pointer-events: none;
    }
    .feature-card::after {
        content: "";
        position: absolute;
        right: -40px; top: -30px;
        width: 190px; height: 190px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,0.54), transparent 64%);
        pointer-events: none;
    }
    .feature-card:hover { transform: translateY(-3px); background: var(--glass-bg-strong); box-shadow: var(--inner-hl), var(--shadow-lg); }
    .feature-card > * { position: relative; z-index: 1; }
    .feature-card .feat-icon {
        width: 84px; height: 84px;
        background: rgba(255,255,255,0.26); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 28px;
        box-shadow: var(--inner-hl), 0 12px 26px -18px rgba(37,70,118,0.50);
    }
    .feature-card .feat-icon svg {
        width: 40px; height: 40px;
        color: var(--blue);
        position: relative; z-index: 1;
        filter:
            drop-shadow(0 2px 3px rgba(10,132,255,0.25))
            drop-shadow(0 0 0.5px rgba(10,132,255,0.30));
    }
    .feature-card:hover .feat-icon svg {
        transform: scale(1.04);
        transition: transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    .feature-card .feat-title {
        font-size: 20px; font-weight: 700; color: var(--ink);
        margin-bottom: 10px; letter-spacing: -0.01em;
    }
    .feature-card .feat-underline {
        width: 28px; height: 2px; background: var(--blue);
        border-radius: 2px; margin-bottom: 20px; opacity: 0.76;
    }
    .feature-card .feat-desc {
        font-size: 13px; color: #6F7E9D; line-height: 1.75;
    }

    /* ── Chat bubbles ───────────────────────── */
    .chat-bubble {
        margin-bottom: 18px;
        background: var(--glass-bg);
        backdrop-filter: blur(30px) saturate(180%);
        -webkit-backdrop-filter: blur(30px) saturate(180%);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: var(--inner-hl), var(--shadow-sm);
        animation: floatIn 260ms ease-out both;
    }
    .chat-bubble .bubble-role {
        font-size: 12px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.06em; margin-bottom: 6px; color: var(--blue);
    }
    .chat-bubble .bubble-text { font-size: 15px; line-height: 1.65; color: var(--ink); }
    .chat-bubble .bubble-text > *:first-child { margin-top: 0; }
    .chat-bubble .bubble-text > *:last-child { margin-bottom: 0; }
    .chat-bubble .bubble-text p { margin: 0 0 10px 0; }
    .chat-bubble .bubble-text ul,
    .chat-bubble .bubble-text ol { margin: 6px 0 10px 0; padding-left: 22px; }
    .chat-bubble .bubble-text li { margin: 2px 0; }
    .chat-bubble .bubble-text li > p { margin: 0; }
    .chat-bubble .bubble-text h1,
    .chat-bubble .bubble-text h2,
    .chat-bubble .bubble-text h3,
    .chat-bubble .bubble-text h4 { margin: 12px 0 6px 0; line-height: 1.3; }
    .chat-bubble .bubble-text h1 { font-size: 20px; }
    .chat-bubble .bubble-text h2 { font-size: 18px; }
    .chat-bubble .bubble-text h3 { font-size: 16px; }
    .chat-bubble .bubble-text h4 { font-size: 15px; }
    .chat-bubble .bubble-text code {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.9em;
        background: rgba(10, 132, 255, 0.08);
        padding: 1px 5px; border-radius: 5px;
    }
    .chat-bubble .bubble-text pre {
        background: rgba(15, 23, 42, 0.04);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 10px;
        padding: 10px 12px; margin: 8px 0;
        overflow-x: auto;
    }
    .chat-bubble .bubble-text pre code {
        background: transparent; padding: 0; border-radius: 0;
        font-size: 13px; line-height: 1.5;
    }
    .chat-bubble .bubble-text blockquote {
        margin: 6px 0; padding: 4px 12px;
        border-left: 3px solid rgba(10, 132, 255, 0.4);
        color: rgba(15, 23, 42, 0.75);
    }
    .chat-bubble .bubble-text a { color: var(--blue); text-decoration: none; }
    .chat-bubble .bubble-text a:hover { text-decoration: underline; }
    .chat-bubble .bubble-text strong { font-weight: 600; }
    .chat-bubble .bubble-text table {
        border-collapse: collapse; margin: 8px 0; font-size: 14px;
    }
    .chat-bubble .bubble-text th,
    .chat-bubble .bubble-text td {
        border: 1px solid rgba(15, 23, 42, 0.12);
        padding: 6px 10px; text-align: left;
    }
    .chat-bubble .bubble-text th { background: rgba(10, 132, 255, 0.06); font-weight: 600; }

    /* ── Feedback buttons ───────────────────── */
    /* Feedback buttons are now rendered via st.html with inline styles */

    /* ── Chat input (Apple style: pill, sparkles, blue send) ── */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }
    [data-testid="stBottomBlockContainer"] {
        padding-bottom: 36px !important;
        max-width: 1200px;
        margin: 0 auto;
    }
    [data-testid="stChatInput"] { background: transparent !important; padding: 0 !important; }
    [data-testid="stChatInput"] > div {
        background: rgba(255,255,255,0.36) !important;
        backdrop-filter: blur(36px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(36px) saturate(190%) !important;
        border: 1px solid rgba(255,255,255,0.76) !important;
        border-radius: 24px !important;
        padding: 12px 12px 12px 26px !important;
        display: flex !important;
        align-items: center !important;
        flex-wrap: nowrap !important;
        box-shadow: var(--inner-hl), 0 22px 60px -36px rgba(31,55,92,0.48) !important;
        overflow: hidden !important;
        position: relative !important;
    }
    [data-testid="stChatInput"] > div::before {
        display: none !important;
    }
    [data-testid="stChatInput"] > div > div:first-child { flex: 1 !important; min-width: 0 !important; }
    /* strip borders/outlines/shadows from every inner div Streamlit nests
       around the textarea — recent versions ship a dark focus ring there */
    [data-testid="stChatInput"] > div > div,
    [data-testid="stChatInput"] > div > div > div,
    [data-testid="stChatInput"] > div > div > div > div {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    [data-testid="stChatInput"] > div > div:focus,
    [data-testid="stChatInput"] > div > div:focus-within,
    [data-testid="stChatInput"] > div > div:focus-visible,
    [data-testid="stChatInput"] > div > div > div:focus,
    [data-testid="stChatInput"] > div > div > div:focus-within,
    [data-testid="stChatInput"] > div > div > div:focus-visible {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea {
        border: none !important; outline: none !important;
        background: transparent !important;
        font-size: 15px !important; font-family: 'Inter', sans-serif !important;
        padding: 8px 8px !important; color: var(--ink) !important;
        min-height: 36px !important; max-height: 120px !important;
        line-height: 20px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; font-style: normal !important; }
    [data-testid="stChatInput"] textarea:focus { box-shadow: none !important; border: none !important; outline: none !important; }
    /* kill the focus ring on the chat-input wrapper itself */
    [data-testid="stChatInput"] > div:focus,
    [data-testid="stChatInput"] > div:focus-within,
    [data-testid="stChatInput"] > div:focus-visible {
        outline: none !important;
        box-shadow: var(--inner-hl), 0 22px 60px -36px rgba(31,55,92,0.48) !important;
        border: 1px solid rgba(255,255,255,0.76) !important;
    }
    [data-testid="stChatInput"] *:focus,
    [data-testid="stChatInput"] *:focus-visible { outline: none !important; }
    [data-testid="stChatInput"] button,
    [data-testid="stChatInput"] button[kind="primary"],
    [data-testid="stChatInput"] [data-testid="stChatInputSubmitButton"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important; border-radius: 10px !important;
        width: 54px !important; height: 54px !important;
        min-width: 54px !important; min-height: 54px !important;
        max-width: 54px !important; max-height: 54px !important;
        padding: 0 !important; margin: 0 !important;
        flex-shrink: 0 !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        position: static !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] button:hover { background: transparent !important; background-color: transparent !important; }
    [data-testid="stChatInput"] button svg { display: none !important; }
    [data-testid="stChatInput"] button::after {
        content: "";
        display: block;
        width: 28px; height: 28px;
        transform: translateY(-3px);
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%230A84FF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14'/%3E%3Cpath d='M12 5l7 7-7 7'/%3E%3C/svg%3E");
        mask-size: contain;
        mask-repeat: no-repeat;
        mask-position: center;
        background: #0A84FF;
    }

    /* ── Disclaimer (under chat input) ─────── */
    .disclaimer-fixed {
        position: fixed; left: 0; right: 0; bottom: 10px;
        display: flex; align-items: center; justify-content: center;
        gap: 6px; font-size: 12px; color: var(--muted);
        pointer-events: none; z-index: 11;
        padding-left: 280px;
        padding-right: 24px;
    }
    .disclaimer-fixed svg { width: 13px; height: 13px; flex-shrink: 0; }

    /* ── Streamlit chat message component ──── */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        font-size: 15px !important; line-height: 1.65 !important;
    }
    @media (max-width: 900px) {
        .main .block-container { padding-left: 18px !important; padding-right: 18px !important; }
        [data-testid="stSidebar"] > div:first-child { border-radius: 18px !important; height: auto; }
        .top-bar { padding-bottom: 14px; }
        .hero-section { padding: 26px 0 22px 0; }
        .hero-title { font-size: 42px; line-height: 1.08; }
        .hero-subtitle { font-size: 16px; }
        .features-row { flex-direction: column; gap: 12px; padding-bottom: 24px; }
        .feature-card { max-width: none; padding: 22px 20px; }
        .disclaimer-fixed { padding-left: 18px; padding-right: 18px; font-size: 11px; }
        [data-testid="stChatInput"] > div { padding: 8px !important; border-radius: 16px !important; }
        [data-testid="stChatInput"] > div::before { display: none; }
        [data-testid="stChatInput"] textarea {
            min-height: 44px !important;
            padding: 11px 8px !important;
            font-size: 14px !important;
            line-height: 18px !important;
        }
        [data-testid="stChatInput"] button,
        [data-testid="stChatInput"] button[kind="primary"],
        [data-testid="stChatInput"] [data-testid="stChatInputSubmitButton"] {
            width: 40px !important;
            height: 40px !important;
            min-width: 40px !important;
            min-height: 40px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ── SVG icons ────────────────────────────────────────────────────────────
ICON_HEX = '<svg viewBox="0 0 28 28" fill="none"><path d="M14 2L4 7.5V20.5L14 26L24 20.5V7.5L14 2Z" stroke="#0A84FF" stroke-width="2" stroke-linejoin="round"/><path d="M14 14L4 7.5" stroke="#0A84FF" stroke-width="2"/><path d="M14 14L24 7.5" stroke="#0A84FF" stroke-width="2"/><path d="M4 20.5L14 26V14" stroke="#0A84FF" stroke-width="2"/></svg>'
ICON_DB = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>'
ICON_FILE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
ICON_PAPERPLANE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>'
ICON_LOCK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
ICON_SHIELD = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
ICON_LIGHTNING = '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'

# ── Welcome-screen feature icons ─────────────────────────────────────────
# Filled, gradient-stroked, Apple-style. All gradients use currentColor so
# the brand blue from CSS (var(--blue)) flows through; opacity stops give
# the depth without hardcoding any color.

# Cited: filled bookmark with a gloss highlight + precise marker dot.
ICON_BOOKMARK = (
    '<svg viewBox="0 0 24 24" fill="none">'
    '<defs>'
    '<linearGradient id="g_cite" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0%" stop-color="currentColor" stop-opacity="0.55"/>'
    '<stop offset="100%" stop-color="currentColor" stop-opacity="1"/>'
    '</linearGradient>'
    '<linearGradient id="g_cite_gloss" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0%" stop-color="white" stop-opacity="0.55"/>'
    '<stop offset="100%" stop-color="white" stop-opacity="0"/>'
    '</linearGradient>'
    '</defs>'
    '<path d="M18.5 21 12 16.7 5.5 21V5.5A2.5 2.5 0 0 1 8 3h8a2.5 2.5 0 0 1 2.5 2.5z" fill="url(#g_cite)"/>'
    '<path d="M16 4.5H8A1.5 1.5 0 0 0 6.5 6v3.2C8 8 10 7.4 12 7.4s4 .6 5.5 1.8V6A1.5 1.5 0 0 0 16 4.5z" fill="url(#g_cite_gloss)"/>'
    '<circle cx="12" cy="9.4" r="1.5" fill="white" fill-opacity="0.92"/>'
    '</svg>'
)

# Hybrid: two overlapping translucent circles — overlap darkens naturally
# where they meet, giving a real Venn feel without masks or extra paths.
ICON_VENN = (
    '<svg viewBox="0 0 24 24" fill="none">'
    '<defs>'
    '<linearGradient id="g_venL" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0%" stop-color="currentColor" stop-opacity="0.85"/>'
    '<stop offset="100%" stop-color="currentColor" stop-opacity="0.40"/>'
    '</linearGradient>'
    '<linearGradient id="g_venR" x1="1" y1="0" x2="0" y2="1">'
    '<stop offset="0%" stop-color="currentColor" stop-opacity="0.85"/>'
    '<stop offset="100%" stop-color="currentColor" stop-opacity="0.40"/>'
    '</linearGradient>'
    '</defs>'
    '<circle cx="9" cy="12" r="5.8" fill="url(#g_venL)"/>'
    '<circle cx="15" cy="12" r="5.8" fill="url(#g_venR)"/>'
    '<circle cx="9" cy="10" r="1.1" fill="white" fill-opacity="0.55"/>'
    '<circle cx="15" cy="10" r="1.1" fill="white" fill-opacity="0.55"/>'
    '</svg>'
)

# Honest: filled speech bubble with three white "asking back" dots.
ICON_QUESTION_BUBBLE = (
    '<svg viewBox="0 0 24 24" fill="none">'
    '<defs>'
    '<linearGradient id="g_hon" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0%" stop-color="currentColor" stop-opacity="0.55"/>'
    '<stop offset="100%" stop-color="currentColor" stop-opacity="1"/>'
    '</linearGradient>'
    '<linearGradient id="g_hon_gloss" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0%" stop-color="white" stop-opacity="0.45"/>'
    '<stop offset="100%" stop-color="white" stop-opacity="0"/>'
    '</linearGradient>'
    '</defs>'
    '<path d="M20.5 6.5A2.5 2.5 0 0 0 18 4H6a2.5 2.5 0 0 0-2.5 2.5v8A2.5 2.5 0 0 0 6 17h2v3.2L13 17h5a2.5 2.5 0 0 0 2.5-2.5z" fill="url(#g_hon)"/>'
    '<path d="M18 5H6a1.5 1.5 0 0 0-1.5 1.5v2c2.5-.6 5-.9 7.5-.9s5 .3 7.5.9v-2A1.5 1.5 0 0 0 18 5z" fill="url(#g_hon_gloss)"/>'
    '<circle cx="8.5" cy="10.6" r="1.05" fill="white" fill-opacity="0.95"/>'
    '<circle cx="12" cy="10.6" r="1.05" fill="white" fill-opacity="0.95"/>'
    '<circle cx="15.5" cy="10.6" r="1.05" fill="white" fill-opacity="0.95"/>'
    '</svg>'
)
ICON_SPARKLES = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.5L19 10l-5.1 1.5L12 17l-1.9-5.5L5 10l5.1-1.5z"/><path d="M19 3l.7 2 2 .7-2 .7L19 9l-.7-2L16.3 6l2-.7z" opacity=".6"/></svg>'

def _fmt_size(bytes_val: int) -> str:
    if bytes_val < 1024:
        return f"{bytes_val} B"
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    return f"{bytes_val / (1024 * 1024):.1f} MB"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _render_documents_list(docs: list[dict]) -> str:
    rows = []
    for doc in docs:
        raw_name = str(doc["name"])
        safe_name = _esc(raw_name)
        size_str = _fmt_size(doc["size_bytes"])
        js_name = json.dumps(raw_name)
        rows.append(f"""
        <div class="doc-row">
            <div class="doc-main">
                <div class="doc-icon">{ICON_FILE}</div>
                <div class="doc-copy">
                    <div class="doc-name" title="{safe_name}">{safe_name}</div>
                    <div class="doc-size">{size_str}</div>
                </div>
            </div>
            <button class="doc-delete-btn" onclick='deleteDocument({js_name})' aria-label="Delete document">✕</button>
        </div>
        """)
    return f"""
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
            overflow: visible;
        }}
        * {{ box-sizing: border-box; }}
        .doc-list {{
            margin: 0;
            border-radius: 14px;
            background: rgba(255,255,255,0.28);
            border: 1px solid rgba(255,255,255,0.66);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.92),
                inset 0 -1px 0 rgba(255,255,255,0.55),
                0 1px 2px rgba(26,44,82,0.05),
                0 12px 28px -24px rgba(26,44,82,0.30);
            overflow: visible;
        }}
        .doc-row {{
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 44px;
            padding: 5px 8px 5px 12px;
            border-bottom: 1px solid rgba(112,134,170,0.14);
        }}
        .doc-row:last-child {{ border-bottom: none; }}
        .doc-main {{
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
        }}
        .doc-icon {{
            width: 15px;
            height: 15px;
            color: #6D7B99;
            flex: 0 0 auto;
        }}
        .doc-icon svg {{ width: 15px; height: 15px; }}
        .doc-copy {{ min-width: 0; }}
        .doc-name {{
            max-width: 134px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: #081936;
            font-size: 12px;
            line-height: 15px;
            font-weight: 650;
        }}
        .doc-size {{
            margin-top: 1px;
            color: #60749A;
            font-size: 10px;
            line-height: 13px;
            font-weight: 500;
        }}
        .doc-delete-btn {{
            width: 28px;
            height: 28px;
            border: none;
            border-radius: 9px;
            background: transparent;
            color: #B42318;
            font-size: 14px;
            line-height: 1;
            cursor: pointer;
            box-shadow: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .doc-delete-btn:hover {{
            background: rgba(180,35,24,0.08);
        }}
    </style>
    <div class="doc-list">{"".join(rows)}</div>
    <script>
        const API_URL = {json.dumps(PUBLIC_API_URL)};
        async function deleteDocument(name) {{
            const ok = window.confirm(`Delete ${{name}}?`);
            if (!ok) return;
            const response = await fetch(`${{API_URL}}/api/documents/${{encodeURIComponent(name)}}`, {{
                method: 'DELETE',
            }});
            if (!response.ok) {{
                const text = await response.text();
                window.alert(text || 'Delete failed');
                return;
            }}
            window.parent.location.reload();
        }}
    </script>
    """


def _render_settings_panel(store: str) -> str:
    return f"""
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
            overflow: hidden;
        }}
        * {{ box-sizing: border-box; }}
        .settings-card {{
            width: 100%;
            border-radius: 14px;
            background: rgba(255,255,255,0.28);
            border: 1px solid rgba(255,255,255,0.66);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.92),
                inset 0 -1px 0 rgba(255,255,255,0.52),
                0 1px 2px rgba(26,44,82,0.05),
                0 12px 28px -24px rgba(26,44,82,0.30);
            padding: 8px 10px;
            color: #081936;
        }}
        .setting-action {{
            width: 100%;
            height: 32px;
            border: 1px solid rgba(128,162,220,0.26);
            border-radius: 10px;
            background: rgba(255,255,255,0.34);
            color: #0A84FF;
            font-size: 12px;
            font-weight: 650;
            cursor: pointer;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.82);
            margin-bottom: 8px;
        }}
        .setting-action:hover {{ background: rgba(255,255,255,0.56); }}
        .setting-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            min-height: 24px;
            border-bottom: 1px solid rgba(112,134,170,0.14);
            color: #6D7B99;
            font-size: 10px;
            line-height: 13px;
        }}
        .setting-row:last-child {{ border-bottom: none; }}
        .setting-value {{
            max-width: 130px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: #081936;
            font-weight: 650;
            text-align: right;
        }}
    </style>
    <div class="settings-card">
        <button class="setting-action" onclick="reindex()">↻ Re-index</button>
        <div class="setting-row"><span>API</span><span class="setting-value" title="{_esc(API_URL)}">{_esc(API_URL)}</span></div>
        <div class="setting-row"><span>Store</span><span class="setting-value">{_esc(store)}</span></div>
        <div class="setting-row"><span>Top K</span><span class="setting-value">5</span></div>
        <div class="setting-row"><span>RRF K</span><span class="setting-value">60</span></div>
    </div>
    <script>
        const API_URL = {json.dumps(PUBLIC_API_URL)};
        async function reindex() {{
            const button = document.querySelector('.setting-action');
            button.disabled = true;
            button.textContent = 'Re-indexing...';
            const response = await fetch(`${{API_URL}}/api/ingest`, {{ method: 'POST' }});
            if (!response.ok) {{
                button.disabled = false;
                button.textContent = '↻ Re-index';
                window.alert(await response.text() || 'Indexing failed');
                return;
            }}
            window.parent.location.reload();
        }}
    </script>
    """

if "history" not in st.session_state:
    st.session_state.history = []
if "ingesting" not in st.session_state:
    st.session_state.ingesting = False
if "auto_reindex" not in st.session_state:
    st.session_state.auto_reindex = True
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False


def _feedback(rating: int, msg: dict) -> None:
    try:
        requests.post(f"{API_URL}/api/feedback", json={
            "query": msg.get("query", ""), "answer": msg.get("content", ""),
            "sources": msg.get("sources", []), "rating": rating,
        }, timeout=5)
    except Exception:
        pass


# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="logo-row">
        <span class="logo-text">AI Agent with RAG</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Document Sources</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drag and drop file here",
        type=["pdf", "csv", "md", "txt", "html", "htm", "json", "docx"],
        accept_multiple_files=False, label_visibility="collapsed",
    )

    if uploaded is not None:
        if uploaded.size > 200 * 1024 * 1024:
            st.error("File exceeds 200 MB limit.")
        else:
            try:
                r = requests.post(
                    f"{API_URL}/api/upload",
                    files={"file": (uploaded.name, uploaded.getvalue())},
                    timeout=120,
                )
                if r.status_code == 200:
                    st.success(f"Uploaded: {uploaded.name}")
                    if st.session_state.auto_reindex:
                        st.session_state.ingesting = True
                else:
                    st.error(r.json().get("detail", "Upload failed"))
            except Exception as e:
                st.error(f"Upload error: {e}")

    try:
        docs_resp = requests.get(f"{API_URL}/api/documents", timeout=5)
        docs_data = docs_resp.json() if docs_resp.status_code == 200 else {"indexed_count": 0, "store": "chroma", "documents": []}
    except Exception:
        docs_data = {"indexed_count": 0, "store": "chroma", "documents": []}

    indexed = docs_data["indexed_count"]
    store = docs_data["store"]
    st.markdown(f"""
    <div class="status-card">
        <div class="db-icon">{ICON_DB}</div>
        <div class="status-text">
            <div class="status-main">Indexed: {indexed} chunks</div>
            <div class="status-sub">Store: {store}</div>
        </div>
        <div class="status-chevron">›</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Documents</div>', unsafe_allow_html=True)
    docs = docs_data.get("documents", [])
    if docs:
        component_html(
            _render_documents_list(docs),
            height=min(300, max(64, len(docs) * 44 + 10)),
        )
    else:
        st.html('<div class="file-list"><div style="font-size:12px;color:#86868B;padding:12px 16px;">No documents indexed</div></div>')

    if st.session_state.ingesting:
        with st.spinner("Re-indexing..."):
            try:
                r = requests.post(f"{API_URL}/api/ingest", timeout=300)
                if r.status_code == 200:
                    st.success(f"Indexed {r.json().get('indexed_count', 0)} chunks")
                else:
                    st.error("Indexing failed")
            except Exception as e:
                st.error(f"Indexing error: {e}")
            st.session_state.ingesting = False
            st.rerun()

    settings_btn_class = "util-btn-row settings-btn is-open" if st.session_state.show_settings else "util-btn-row settings-btn"
    st.markdown(f'<div class="{settings_btn_class}">', unsafe_allow_html=True)
    if st.button("⚙   Settings", key="settings_btn", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.show_settings:
        component_html(_render_settings_panel(store), height=138)

    st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)

# ── Main content ─────────────────────────────────────────────────────────
st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)

if len(st.session_state.history) == 0:
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-title">AI Agent with RAG</div>
        <div class="hero-subtitle">Talk to your documents. Get cited answers, page by page.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="features-row">
        <div class="feature-card">
            <div class="feat-icon">{ICON_BOOKMARK}</div>
            <div class="feat-title">Cited</div>
            <div class="feat-underline"></div>
            <div class="feat-desc">Every answer is anchored to the page it came from. Click the source and verify in 5 seconds.</div>
        </div>
        <div class="feature-card">
            <div class="feat-icon">{ICON_VENN}</div>
            <div class="feat-title">Hybrid</div>
            <div class="feat-underline"></div>
            <div class="feat-desc">Semantic + keyword retrieval finds exact names, IDs, and part numbers that embeddings alone miss.</div>
        </div>
        <div class="feature-card">
            <div class="feat-icon">{ICON_QUESTION_BUBBLE}</div>
            <div class="feat-title">Honest</div>
            <div class="feat-underline"></div>
            <div class="feat-desc">Ambiguous query? It asks for clarification. Bad retrieval? It re-searches. No silent confabulation.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    for i, msg in enumerate(st.session_state.history):
        role_label = "You" if msg["role"] == "user" else "AI Agent"
        if msg["role"] == "user":
            content = _esc(msg["content"]).replace("\n", "<br>")
        else:
            # Render assistant replies as Markdown. MarkdownIt with html=False
            # escapes any raw HTML in the LLM output, so this is safe even if
            # the model returns angle brackets or script-like text.
            content = _MD.render(str(msg["content"]))
        st.markdown(f"""
        <div class="chat-bubble">
            <div class="bubble-role">{role_label}</div>
            <div class="bubble-text">{content}</div>
        </div>
        """, unsafe_allow_html=True)

        if msg["role"] == "assistant":
            safe_query = json.dumps(msg["query"])
            safe_answer = json.dumps(msg["content"])
            safe_sources = json.dumps(msg.get("sources", []))
            st.html(f"""
            <style>
                .fb-actions {{ display: flex; gap: 8px; margin: -4px 0 14px 0; }}
                .fb-btn {{
                    width: 36px; height: 36px; border-radius: 999px;
                    border: 1px solid rgba(210,216,228,0.62);
                    background: rgba(255,255,255,0.38) center/18px 18px no-repeat;
                    backdrop-filter: blur(18px) saturate(180%);
                    -webkit-backdrop-filter: blur(18px) saturate(180%);
                    box-shadow: inset 0 1px 0 rgba(255,255,255,0.82), 0 1px 2px rgba(26,44,82,0.05);
                    cursor: pointer; padding: 0; color: transparent; font-size: 0;
                }}
                .fb-btn:hover {{ background-color: rgba(10,132,255,0.08); border-color: rgba(10,132,255,0.32); }}
                .fb-btn.up {{
                    background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238A94A6' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3'/%3E%3C/svg%3E");
                }}
                .fb-btn.down {{
                    background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238A94A6' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4.28v7a2.31 2.31 0 0 1-2.33 2H17'/%3E%3C/svg%3E");
                }}
            </style>
            <div class="fb-actions">
                <button class="fb-btn up" title="Helpful" onclick='sendFeedback(1, {safe_query}, {safe_answer}, {safe_sources}, this)'>&nbsp;</button>
                <button class="fb-btn down" title="Not helpful" onclick='sendFeedback(-1, {safe_query}, {safe_answer}, {safe_sources}, this)'>&nbsp;</button>
            </div>
            """)
            _seen_feedback_script = getattr(st.session_state, "_feedback_script_rendered", False)
            if not _seen_feedback_script:
                st.session_state._feedback_script_rendered = True
                st.html(f"""
            <script>
                var _fb_url = {json.dumps(PUBLIC_API_URL)};
                function sendFeedback(rating, query, answer, sources, btn) {{
                    if (btn.disabled) return;
                    btn.disabled = true;
                    btn.style.opacity = '0.4';
                    fetch(_fb_url + '/api/feedback', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{query: query, answer: answer, sources: sources, rating: rating}}),
                    }}).finally(function() {{
                        btn.disabled = false;
                        btn.style.opacity = '1';
                    }});
                }}
            </script>
            """)

# ── Chat input ──
prompt = st.chat_input("Ask anything about your documents...")
if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.spinner("Retrieving and analyzing..."):
        # Continuation: if the previous reply was a clarification, the server
        # gave us a session_id. Echo it back so the API can splice the
        # original query with the user's clarifying answer.
        body = {"query": prompt}
        pending_sid = st.session_state.get("pending_session_id")
        if pending_sid:
            body["session_id"] = pending_sid
        try:
            resp = requests.post(f"{API_URL}/api/query", json=body, timeout=120)
            data = resp.json() if resp.status_code == 200 else {"answer": f"Error: {resp.status_code}", "citations": []}
        except Exception as e:
            data = {"answer": f"Service unavailable ({e})", "citations": []}

    # Store / clear pending session for the next turn.
    if data.get("needs_clarification") and data.get("session_id"):
        st.session_state["pending_session_id"] = data["session_id"]
    else:
        st.session_state.pop("pending_session_id", None)

    answer = data.get("clarification_question") if data.get("needs_clarification") else data.get("answer", "(empty)")
    st.session_state.history.append({
        "role": "assistant", "content": answer,
        "sources": data.get("citations", []), "query": prompt,
    })
    st.rerun()

st.markdown(f"""
<div class="disclaimer-fixed">
    {ICON_LOCK} Responses may contain inaccuracies. Verify important information.
</div>
""", unsafe_allow_html=True)
