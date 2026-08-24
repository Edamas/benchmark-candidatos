from __future__ import annotations

import streamlit as st

from src.charts import ranking_chart
from src.config import PLOTLY_CONFIG
from src.data import (
    export_payload,
    json_bytes,
    load_benchmark,
    load_candidate_snapshot,
    load_candidates,
    load_sources,
    overview_scores,
    scored_slugs,
    weighted_scores,
)
from src.radar import render_radar
from src.ui import analytic_footer, candidate_card, hero


hero(
    "Benchmark de Candidatos",
    "Os 13 pedidos presidenciais do TSE aparecem abaixo, com avaliação dos 40 fatores. Nota neutra identifica silêncio ou lacuna documental — não aprovação automática.",
    "Eleição presidencial · Brasil · 2026",
)

filter_cols = st.columns([1, 1.35, 1])
filter_cols[0].segmented_control("Ano", [2026], default=2026, disabled=True)
filter_cols[1].segmented_control("Cargo", ["Presidência"], default="Presidência", disabled=True)
filter_cols[2].segmented_control("Distrito", ["Brasil"], default="Brasil", disabled=True)

benchmark = load_benchmark()
candidates = load_candidates()
evaluated = scored_slugs()
ranking = weighted_scores(benchmark, evaluated)
score_lookup = ranking.set_index("slug")["score"].to_dict()
overview = overview_scores(benchmark, evaluated)

body, graph = st.columns([0.98, 1.02], gap="large", vertical_alignment="top")
with body:
    st.subheader("Pedidos de candidatura no TSE")
    st.caption("Clique uma vez em “Abrir ficha” ou use o nome no menu Presidência.")
    for start in range(0, len(candidates), 2):
        columns = st.columns(2)
        for column, candidate in zip(columns, candidates[start : start + 2]):
            with column:
                candidate_card(candidate, score_lookup.get(candidate["slug"]))
                st.link_button(
                    "Abrir ficha",
                    f"./presidencia-{candidate['slug']}",
                    icon=":material/arrow_forward:",
                    width="stretch",
                )

    st.subheader("Média ponderada dos 40 fatores")
    st.dataframe(
        ranking.rename(columns={"candidate": "Candidato", "party": "Partido", "score": "Média ponderada"})[
            ["Candidato", "Partido", "Média ponderada"]
        ],
        hide_index=True,
        width="stretch",
    )

with graph:
    with st.container(key="election_chart_panel"):
        st.markdown('<div class="bcc-panel-label">Painel gráfico</div>', unsafe_allow_html=True)
        chart_type = st.segmented_control(
            "Tipo de gráfico",
            ["Radar geral", "Ranking"],
            default="Radar geral",
            key="election_chart_type",
        )
        if chart_type == "Radar geral":
            render_radar(overview, "Visão geral · 40 fatores", key="election_overview_radar")
        else:
            st.plotly_chart(ranking_chart(ranking), width="stretch", config=PLOTLY_CONFIG)
        st.caption("O radar agrega todos os 40 fatores. Nota 5 representa neutralidade, ambiguidade ou evidência insuficiente.")

payload = {
    "official_snapshot": load_candidate_snapshot(),
    "evaluated_benchmark": export_payload(benchmark, evaluated),
    "not_evaluated": [candidate["slug"] for candidate in candidates if candidate["slug"] not in evaluated],
}
st.download_button(
    "Baixar visão geral em JSON",
    data=json_bytes(payload),
    file_name="benchmark-presidencia-2026.json",
    mime="application/json",
    icon=":material/download:",
)

analytic_footer(
    [source for source in load_sources() if source["key"] in {"tse_candidates", "constitution", "defense", "minerals", "ai"}],
    [
        "Os 13 nomes constam no snapshot oficial do TSE de 24/08/2026; pedido registrado não significa registro deferido.",
        "Cadastro e finanças são dados oficiais; notas e pesos são avaliação editorial auditável.",
        "Quando o plano não trata um fator, a nota permanece neutra em 5; ausência de evidência nunca é convertida em zero.",
    ],
)
