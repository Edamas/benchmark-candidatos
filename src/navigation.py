from __future__ import annotations

from collections.abc import Mapping

import streamlit as st


def go_to(path: str, params: Mapping[str, str] | None = None) -> None:
    st.session_state["_pending_route_params"] = dict(params or {})
    st.switch_page(path)


def get_route_param(key: str, default: str = "") -> str:
    raw = st.query_params.get(key, "")
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    if raw:
        return str(raw)
    pending = st.session_state.get("_pending_route_params", {})
    value = str(pending.get(key, default))
    if value:
        st.query_params[key] = value
    return value


def get_selected_slugs(default: list[str] | None = None) -> list[str]:
    raw = get_route_param("candidatos")
    values = [value for value in str(raw).split(",") if value]
    return values or list(default or [])
