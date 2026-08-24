from __future__ import annotations

from html import escape

import streamlit as st

from src.config import ASSET_DIR, BRAND, TAGLINE


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bcc-green: #0b6654;
          --bcc-deep: #073d35;
          --bcc-gold: #f2bf40;
          --bcc-paper: #f6f7f2;
          --bcc-ink: #17201c;
        }
        .stApp { background:
          radial-gradient(circle at 95% 2%, rgba(242,191,64,.10), transparent 24rem),
          linear-gradient(180deg, #f8faf6 0%, #f4f6f1 100%); }
        [data-testid="stSidebar"] { border-right: 1px solid rgba(11,102,84,.14); }
        [data-testid="stSidebarNav"] span { font-weight: 590; }
        .bcc-hero { padding: .25rem 0 1.2rem; max-width: 920px; }
        .bcc-eyebrow { color: var(--bcc-green); text-transform: uppercase; letter-spacing: .13em;
          font-size: .76rem; font-weight: 750; margin-bottom: .45rem; }
        .bcc-hero h1 { color: var(--bcc-ink); letter-spacing: -.035em; margin: 0 0 .4rem;
          font-size: clamp(2rem, 4.2vw, 3.55rem); line-height: 1.02; }
        .bcc-hero p { color: #4b5d55; font-size: 1.02rem; max-width: 780px; margin: 0; }
        .bcc-note { border-left: 4px solid var(--bcc-gold); padding: .7rem 1rem;
          background: rgba(242,191,64,.09); border-radius: 0 12px 12px 0; color: #3c4d46; }
        .bcc-card { border: 1px solid rgba(11,102,84,.14); border-radius: 18px;
          padding: 1rem 1.05rem; background: rgba(255,255,255,.72); min-height: 132px; }
        .bcc-card h3 { margin: 0 0 .25rem; font-size: 1.15rem; }
        .bcc-card p { color: #52635c; margin: .22rem 0; font-size: .9rem; }
        .bcc-chip { display: inline-block; color: #075344; background: rgba(11,102,84,.10);
          border-radius: 999px; padding: .18rem .55rem; margin-right: .35rem; font-size: .78rem; font-weight: 700; }
        .bcc-score { font-variant-numeric: tabular-nums; font-size: 1.8rem; font-weight: 750;
          color: var(--bcc-deep); letter-spacing: -.04em; }
        div[data-testid="stMetric"] { border: 1px solid rgba(11,102,84,.13); border-radius: 16px;
          padding: .75rem 1rem; background: rgba(255,255,255,.66); }
        div[data-testid="stMetricValue"] { color: var(--bcc-deep); }
        div[data-testid="stDataFrame"] { border: 1px solid rgba(11,102,84,.12); border-radius: 14px; overflow: hidden; }
        .stButton button, .stDownloadButton button { font-weight: 680; }
        .bcc-source { color: #52635c; font-size: .84rem; }
        @media (max-width: 720px) { .bcc-hero h1 { font-size: 2.15rem; } .bcc-card { min-height: auto; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    with st.sidebar:
        st.image(str(ASSET_DIR / "logo.svg"), width="stretch")
        st.caption(TAGLINE)


def hero(title: str, description: str, eyebrow: str = BRAND) -> None:
    st.markdown(
        f"""
        <section class="bcc-hero">
          <div class="bcc-eyebrow">{escape(eyebrow)}</div>
          <h1>{escape(title)}</h1>
          <p>{escape(description)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def candidate_card(candidate: dict, score: float | None = None) -> None:
    score_html = f'<div class="bcc-score">{score:.2f}</div>' if score is not None else ""
    st.markdown(
        f"""
        <article class="bcc-card">
          <span class="bcc-chip">{escape(candidate['party'])}</span>
          <span class="bcc-chip">{escape(str(candidate['number']))}</span>
          <h3>{escape(candidate['ballot_name'])}</h3>
          {score_html}
          <p>{escape(candidate['current_role'])}</p>
        </article>
        """,
        unsafe_allow_html=True,
    )


def evidence_notice() -> None:
    st.markdown(
        """
        <div class="bcc-note"><strong>Leitura correta:</strong> cadastro e finanças vêm do TSE;
        biografia vem da Wikipédia; notas e pesos são avaliação editorial auditável. A pontuação
        não comprova execução futura e não substitui a leitura das fontes.</div>
        """,
        unsafe_allow_html=True,
    )


def format_score(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")
