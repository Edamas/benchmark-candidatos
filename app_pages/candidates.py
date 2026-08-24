from __future__ import annotations

import streamlit as st

from src.charts import ranking_chart
from src.config import PLOTLY_CONFIG
from src.data import load_benchmark, load_candidates, load_sources, overview_scores, scored_slugs, weighted_scores
from src.radar import render_radar
from src.ui import analytic_footer, candidate_card, hero


hero(
    "Candidatos",
    "Acesse fichas completas e mantenha o gráfico analítico visível ao lado da lista.",
)

candidates = load_candidates()
benchmark = load_benchmark()
all_slugs = scored_slugs()
ranking = weighted_scores(benchmark, all_slugs)
ranking_index = ranking.set_index("slug")
overview = overview_scores(benchmark, all_slugs)

party_options = ["Todos", *sorted({candidate["party"] for candidate in candidates})]
selected_party = st.pills("Partido", party_options, default="Todos")
query = st.text_input("Buscar por nome", placeholder="Digite parte do nome…", icon=":material/search:")
filtered = [
    candidate
    for candidate in candidates
    if (selected_party == "Todos" or candidate["party"] == selected_party)
    and (not query or query.casefold() in candidate["full_name"].casefold() or query.casefold() in candidate["ballot_name"].casefold())
]

body, graph = st.columns([0.96, 1.04], gap="large", vertical_alignment="top")
with body:
    if not filtered:
        st.info("Nenhum candidato corresponde aos filtros.")
    for candidate in filtered:
        score = float(ranking_index.loc[candidate["slug"], "score"]) if candidate["slug"] in ranking_index.index else None
        candidate_card(candidate, score)
        st.write(candidate["summary"])
        st.link_button(
            f"Abrir ficha de {candidate['ballot_name']}",
            f"./presidencia-{candidate['slug']}",
            icon=":material/arrow_forward:",
            width="stretch",
        )

with graph:
    with st.container(key="candidates_chart_panel"):
        st.markdown('<div class="bcc-panel-label">Painel gráfico</div>', unsafe_allow_html=True)
        chart_type = st.segmented_control(
            "Tipo de gráfico",
            ["Radar geral", "Ranking"],
            default="Radar geral",
            key="candidates_chart_type_v3",
        )
        if chart_type == "Radar geral":
            render_radar(overview, "Visão geral · 40 fatores", key="candidates_radar")
        else:
            st.plotly_chart(ranking_chart(ranking), width="stretch", config=PLOTLY_CONFIG)
        st.caption("Todos os 40 fatores participam do radar geral.")

analytic_footer(
    [source for source in load_sources() if source["key"] in {"tse_candidates", "constitution"}],
    ["A lista reproduz os 13 pedidos do snapshot do TSE; a situação judicial deve ser confirmada no DivulgaCandContas."],
)
