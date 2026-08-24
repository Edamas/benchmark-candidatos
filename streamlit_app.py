from __future__ import annotations

import inspect

import streamlit as st

from src.config import APP_TITLE, ASSET_DIR
from src.ui import inject_css


st.set_page_config(
    page_title=f"{APP_TITLE} · Brasil Com Censo",
    page_icon=str(ASSET_DIR / "favicon.svg"),
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "About": "Brasil Com Censo — dados, critérios e fontes para uma escolha autônoma.",
    },
)
inject_css()
st.logo(str(ASSET_DIR / "logo.svg"), size="large")


def page(path: str, *, title: str, icon: str, default: bool = False, hidden: bool = False):
    kwargs = {"title": title, "icon": icon, "default": default}
    if hidden and "visibility" in inspect.signature(st.Page).parameters:
        kwargs["visibility"] = "hidden"
    return st.Page(path, **kwargs)


pages = {
    "Explorar": [
        page("app_pages/election.py", title="Eleição", icon=":material/how_to_vote:", default=True),
        page("app_pages/candidates.py", title="Candidatos", icon=":material/groups:"),
        page("app_pages/profile.py", title="Ficha do candidato", icon=":material/person:"),
        page("app_pages/compare.py", title="Comparar", icon=":material/compare_arrows:"),
        page("app_pages/parties.py", title="Partidos", icon=":material/account_balance:"),
    ],
    "Transparência": [
        page("app_pages/methodology.py", title="Dados e metodologia", icon=":material/fact_check:"),
    ],
}

with st.sidebar:
    st.caption("Presidência · Brasil · 2026")

navigation = st.navigation(pages, position="sidebar", expanded=True)
navigation.run()
