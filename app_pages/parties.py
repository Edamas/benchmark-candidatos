from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import factor_radar_chart, ranking_chart
from src.config import KEY_FACTOR_IDS, PLOTLY_CONFIG
from src.data import load_benchmark, load_candidates, load_sources, long_scores, weighted_scores
from src.ui import analytic_footer, hero


hero(
    "Partidos",
    "Legendas presentes no recorte atual, com o painel gráfico sempre à direita.",
)

candidates = load_candidates()
benchmark = load_benchmark()
all_slugs = [candidate["slug"] for candidate in candidates]
ranking = weighted_scores(benchmark)
long_frame = long_scores(benchmark, all_slugs)
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

body, graph = st.columns([1.08, 0.92], gap="large", vertical_alignment="top")
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
            ["Radar-chave", "Ranking"],
            default="Radar-chave",
            key="parties_chart_type",
        )
        figure = (
            factor_radar_chart(long_frame, KEY_FACTOR_IDS, "Fatores-chave por candidato")
            if chart_type == "Radar-chave"
            else ranking_chart(ranking)
        )
        st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG)

analytic_footer(
    [source for source in load_sources() if source["key"] == "tse_candidates"],
    [
        "Espectro político será acrescentado somente depois de definida uma taxonomia com fonte, período e critérios.",
        "Rótulos como direita ou esquerda não alteram notas por si mesmos.",
    ],
)
