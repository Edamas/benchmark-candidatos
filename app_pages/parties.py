from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import ranking_chart
from src.config import PLOTLY_CONFIG
from src.data import load_benchmark, load_candidates, load_sources, overview_scores, scored_slugs, weighted_scores
from src.radar import render_radar
from src.ui import analytic_footer, hero


hero(
    "Partidos",
    "Legendas presentes no recorte atual, com o painel gráfico sempre à direita.",
)

candidates = load_candidates()
benchmark = load_benchmark()
all_slugs = scored_slugs()
ranking = weighted_scores(benchmark, all_slugs)
overview = overview_scores(benchmark, all_slugs)
table = pd.DataFrame(
    [
        {
            "Sigla": candidate["party"],
            "Partido": candidate["party_name"],
            "Número": candidate["number"],
            "Candidato no recorte": candidate["ballot_name"],
        }
        for candidate in candidates
    ]
).sort_values("Sigla")

body, graph = st.columns([0.96, 1.04], gap="large", vertical_alignment="top")
with body:
    st.dataframe(table, hide_index=True, width="stretch")
    st.write(
        "O índice pertence ao candidato e não é automaticamente atribuído à legenda. "
        "Partido, coligação e histórico institucional serão dimensões próprias em versões futuras."
    )

with graph:
    with st.container(key="candidates_chart_panel"):
        st.markdown('<div class="bcc-panel-label">Painel gráfico</div>', unsafe_allow_html=True)
        chart_type = st.segmented_control(
            "Tipo de gráfico",
            ["Radar geral", "Ranking"],
            default="Radar geral",
            key="parties_chart_type_v3",
        )
        if chart_type == "Radar geral":
            render_radar(overview, "Visão geral · 40 fatores", key="parties_radar")
        else:
            st.plotly_chart(ranking_chart(ranking), width="stretch", config=PLOTLY_CONFIG)
        st.caption("Todos os 40 fatores participam do radar geral.")

analytic_footer(
    [source for source in load_sources() if source["key"] == "tse_candidates"],
    [
        "Espectro político será acrescentado somente depois de definida uma taxonomia com fonte, período e critérios.",
        "Rótulos como direita ou esquerda não alteram notas por si mesmos.",
    ],
)
