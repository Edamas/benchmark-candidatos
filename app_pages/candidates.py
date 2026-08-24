from __future__ import annotations

import streamlit as st

from src.charts import dimension_profile_chart, factor_radar_chart, ranking_chart
from src.config import KEY_FACTOR_IDS, PLOTLY_CONFIG
from src.data import dimension_scores, load_benchmark, load_candidates, load_sources, long_scores, weighted_scores
from src.navigation import go_to
from src.ui import analytic_footer, candidate_card, hero


hero(
    "Candidatos",
    "Acesse fichas completas e mantenha o gráfico analítico visível ao lado da lista.",
)

candidates = load_candidates()
benchmark = load_benchmark()
all_slugs = [candidate["slug"] for candidate in candidates]
ranking = weighted_scores(benchmark)
ranking_index = ranking.set_index("slug")
dimensions = dimension_scores(benchmark, all_slugs)
long_frame = long_scores(benchmark, all_slugs)

party_options = ["Todos", *sorted({candidate["party"] for candidate in candidates})]
selected_party = st.pills("Partido", party_options, default="Todos")
query = st.text_input("Buscar por nome", placeholder="Digite parte do nome…", icon=":material/search:")
filtered = [
    candidate
    for candidate in candidates
    if (selected_party == "Todos" or candidate["party"] == selected_party)
    and (not query or query.casefold() in candidate["full_name"].casefold() or query.casefold() in candidate["ballot_name"].casefold())
]

body, graph = st.columns([1.08, 0.92], gap="large", vertical_alignment="top")
with body:
    if not filtered:
        st.info("Nenhum candidato corresponde aos filtros.")
    for candidate in filtered:
        candidate_card(candidate, float(ranking_index.loc[candidate["slug"], "score"]))
        st.write(candidate["summary"])
        if st.button(
            f"Abrir ficha de {candidate['ballot_name']}",
            key=f"profile_{candidate['slug']}",
            icon=":material/arrow_forward:",
            width="stretch",
        ):
            go_to("app_pages/profile.py", {"candidato": candidate["slug"]})

with graph:
    with st.container(key="candidates_chart_panel"):
        st.markdown('<div class="bcc-panel-label">Painel gráfico</div>', unsafe_allow_html=True)
        chart_type = st.segmented_control(
            "Tipo de gráfico",
            ["Radar-chave", "Radar por blocos", "Ranking"],
            default="Radar-chave",
            key="candidates_chart_type",
        )
        if chart_type == "Radar-chave":
            figure = factor_radar_chart(long_frame, KEY_FACTOR_IDS, "Fatores estratégicos")
        elif chart_type == "Radar por blocos":
            figure = dimension_profile_chart(dimensions, "Dimensões estratégicas")
        else:
            figure = ranking_chart(ranking)
        st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG)

analytic_footer(
    [source for source in load_sources() if source["key"] in {"tse_candidates", "constitution"}],
    ["A lista inicial é um recorte editorial; a situação cadastral deve ser confirmada no TSE."],
)
