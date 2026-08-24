from __future__ import annotations

import streamlit as st

from src.charts import dimension_profile_chart, ranking_chart
from src.config import PLOTLY_CONFIG
from src.data import (
    candidate_map,
    dimension_scores,
    export_payload,
    json_bytes,
    load_benchmark,
    load_candidates,
    weighted_scores,
)
from src.navigation import go_to
from src.ui import candidate_card, evidence_notice, hero


hero(
    "Benchmark de Candidatos",
    "Compare tendências de soberania e autonomia estratégica sem misturar fatos oficiais, contexto biográfico e avaliação editorial.",
    "Eleição presidencial · 2026",
)

filter_cols = st.columns([1, 1.35, 1])
with filter_cols[0]:
    st.segmented_control("Ano", [2026], default=2026, disabled=True)
with filter_cols[1]:
    st.segmented_control("Cargo", ["Presidência"], default="Presidência", disabled=True)
with filter_cols[2]:
    st.segmented_control("Distrito", ["Brasil"], default="Brasil", disabled=True)

evidence_notice()

benchmark = load_benchmark()
candidates = load_candidates()
candidates_by_slug = candidate_map()
labels_to_slugs = {f"{c['ballot_name']} · {c['party']}": c["slug"] for c in candidates}

st.subheader("Escolha direta")
selected_labels = st.pills(
    "Um nome abre a ficha; dois ou mais habilitam a comparação.",
    list(labels_to_slugs),
    selection_mode="multi",
    key="home_candidate_selection",
)
selected_slugs = [labels_to_slugs[label] for label in selected_labels]

action_cols = st.columns([1, 1, 3])
with action_cols[0]:
    if st.button(
        "Ver ficha",
        icon=":material/person:",
        type="primary",
        width="stretch",
        disabled=len(selected_slugs) != 1,
    ):
        go_to("app_pages/profile.py", {"candidato": selected_slugs[0]})
with action_cols[1]:
    if st.button(
        "Comparar",
        icon=":material/compare_arrows:",
        width="stretch",
        disabled=len(selected_slugs) < 2,
    ):
        go_to("app_pages/compare.py", {"candidatos": ",".join(selected_slugs)})

ranking = weighted_scores(benchmark)
score_lookup = ranking.set_index("slug")["score"].to_dict()
card_cols = st.columns(len(candidates))
for column, candidate in zip(card_cols, candidates):
    with column:
        candidate_card(candidate, score_lookup[candidate["slug"]])

tab_ranking, tab_dimensions = st.tabs(["Ranking ponderado", "Dimensões estratégicas"])
with tab_ranking:
    st.plotly_chart(ranking_chart(ranking), width="stretch", config=PLOTLY_CONFIG)
with tab_dimensions:
    dimensions = dimension_scores(benchmark, [c["slug"] for c in candidates])
    st.plotly_chart(dimension_profile_chart(dimensions), width="stretch", config=PLOTLY_CONFIG)

st.caption("Use o ícone de câmera na barra do gráfico para baixar PNG em alta resolução.")
payload = export_payload(benchmark, [c["slug"] for c in candidates])
st.download_button(
    "Baixar visão geral em JSON",
    data=json_bytes(payload),
    file_name="benchmark-presidencia-2026.json",
    mime="application/json",
    icon=":material/download:",
)

with st.expander("Como a nota final é calculada"):
    st.latex(r"\text{média ponderada}=\frac{\sum(\text{nota do fator}\times\text{peso do fator})}{\sum\text{pesos}}")
    st.write(
        "Os pesos-base variam de 1 a 5 e resultam de essencialidade, concentração externa, "
        "tempo de recomposição, efeito sistêmico e exposição à coerção. A simulação detalhada fica na página Comparar."
    )
