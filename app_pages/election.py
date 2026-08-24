from __future__ import annotations

import streamlit as st

from src.charts import dimension_profile_chart, factor_radar_chart, ranking_chart
from src.config import KEY_FACTOR_IDS, PLOTLY_CONFIG
from src.data import (
    dimension_scores,
    export_payload,
    json_bytes,
    load_benchmark,
    load_candidates,
    load_sources,
    long_scores,
    weighted_scores,
)
from src.navigation import go_to
from src.ui import analytic_footer, candidate_card, hero


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

benchmark = load_benchmark()
candidates = load_candidates()
all_slugs = [candidate["slug"] for candidate in candidates]
labels_to_slugs = {f"{candidate['ballot_name']} · {candidate['party']}": candidate["slug"] for candidate in candidates}
ranking = weighted_scores(benchmark)
score_lookup = ranking.set_index("slug")["score"].to_dict()
dimensions = dimension_scores(benchmark, all_slugs)
long_frame = long_scores(benchmark, all_slugs)

body, graph = st.columns([1.08, 0.92], gap="large", vertical_alignment="top")
with body:
    st.subheader("Escolha direta")
    selected_labels = st.pills(
        "Um nome abre a ficha; dois ou mais habilitam a comparação.",
        list(labels_to_slugs),
        selection_mode="multi",
        key="home_candidate_selection",
    )
    selected_slugs = [labels_to_slugs[label] for label in selected_labels]
    action_cols = st.columns(2)
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

    for start in range(0, len(candidates), 2):
        card_cols = st.columns(2)
        for column, candidate in zip(card_cols, candidates[start : start + 2]):
            with column:
                candidate_card(candidate, score_lookup[candidate["slug"]])

    st.subheader("Resultado calculado")
    st.dataframe(
        ranking.rename(
            columns={"candidate": "Candidato", "party": "Partido", "score": "Média ponderada"}
        )[["Candidato", "Partido", "Média ponderada"]],
        hide_index=True,
        width="stretch",
    )

with graph:
    with st.container(key="election_chart_panel"):
        st.markdown('<div class="bcc-panel-label">Painel gráfico</div>', unsafe_allow_html=True)
        chart_type = st.segmented_control(
            "Tipo de gráfico",
            ["Radar-chave", "Radar por blocos", "Ranking"],
            default="Radar-chave",
            key="election_chart_type",
        )
        if chart_type == "Radar-chave":
            figure = factor_radar_chart(long_frame, KEY_FACTOR_IDS, "Fatores estratégicos destacados")
        elif chart_type == "Radar por blocos":
            figure = dimension_profile_chart(dimensions, "Perfil por dimensão")
        else:
            figure = ranking_chart(ranking)
        st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG)
        st.caption("Câmera: baixa o gráfico atual em PNG.")

payload = export_payload(benchmark, all_slugs)
st.download_button(
    "Baixar visão geral em JSON",
    data=json_bytes(payload),
    file_name="benchmark-presidencia-2026.json",
    mime="application/json",
    icon=":material/download:",
)

source_keys = {"tse_candidates", "constitution", "defense", "minerals", "ai"}
analytic_footer(
    [source for source in load_sources() if source["key"] in source_keys],
    [
        "Cadastro e finanças são dados oficiais; notas e pesos são avaliação editorial auditável.",
        "A pontuação não comprova execução futura nem substitui a leitura dos planos.",
        "Ausência de dado nunca é convertida automaticamente em nota zero.",
    ],
)
