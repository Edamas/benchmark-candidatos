from __future__ import annotations

import inspect
from collections.abc import Callable

import streamlit as st

from src.config import APP_TITLE, ASSET_DIR
from src.data import load_candidates
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


def page(
    target: str | Callable[[], None],
    *,
    title: str,
    icon: str,
    default: bool = False,
    hidden: bool = False,
    url_path: str | None = None,
):
    kwargs = {"title": title, "icon": icon, "default": default}
    if url_path:
        kwargs["url_path"] = url_path
    if hidden and "visibility" in inspect.signature(st.Page).parameters:
        kwargs["visibility"] = "hidden"
    return st.Page(target, **kwargs)


def candidate_runner(slug: str) -> Callable[[], None]:
    def run_candidate() -> None:
        from src.profile_view import render_candidate_profile

        render_candidate_profile(slug)

    return run_candidate


def comparison_runner(view: str) -> Callable[[], None]:
    def run_comparison() -> None:
        from src.compare_view import render_compare_view

        render_compare_view(view)

    return run_comparison


candidates = load_candidates()
presidency_pages = [
    page("app_pages/election.py", title="Visão geral", icon=":material/how_to_vote:", default=True),
    *[
        page(
            candidate_runner(candidate["slug"]),
            title=candidate["ballot_name"],
            icon=":material/person:",
            url_path=f"presidencia-{candidate['slug']}",
        )
        for candidate in candidates
    ],
]


pages = {
    "Presidência": presidency_pages,
    "Comparar": [
        page(comparison_runner("overview"), title="Visão geral", icon=":material/compare_arrows:", url_path="comparar"),
        page(comparison_runner("radar"), title="Radar por fatores", icon=":material/radar:", url_path="comparar-radar"),
        page(comparison_runner("map"), title="Mapa de notas", icon=":material/grid_view:", url_path="comparar-mapa"),
        page(comparison_runner("weights"), title="Pesos e tabela", icon=":material/tune:", url_path="comparar-pesos"),
    ],
    "Dados": [
        page("app_pages/parties.py", title="Partidos", icon=":material/account_balance:"),
        page("app_pages/methodology.py", title="Dados e metodologia", icon=":material/fact_check:"),
    ],
}

with st.sidebar:
    st.caption("Presidência · Brasil · 2026")

navigation = st.navigation(pages, position="sidebar", expanded=True)
navigation.run()
