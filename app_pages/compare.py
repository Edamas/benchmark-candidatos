from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import dimension_profile_chart, factor_comparison_chart, ranking_chart, score_heatmap
from src.config import PLOTLY_CONFIG
from src.data import (
    comparison_table_with_summary,
    csv_bytes,
    dimension_scores,
    export_payload,
    json_bytes,
    load_benchmark,
    load_candidates,
    long_scores,
    weighted_scores,
)
from src.navigation import get_selected_slugs
from src.ui import evidence_notice, hero


hero(
    "Comparar candidatos",
    "Altere os pesos, observe onde as diferenças realmente surgem e exporte o cenário reproduzível.",
)
evidence_notice()

benchmark = load_benchmark()
candidates = load_candidates()
labels_to_slugs = {f"{candidate['ballot_name']} · {candidate['party']}": candidate["slug"] for candidate in candidates}
slugs_to_labels = {value: key for key, value in labels_to_slugs.items()}
query_slugs = [slug for slug in get_selected_slugs([candidates[0]["slug"], candidates[1]["slug"]]) if slug in slugs_to_labels]
default_labels = [slugs_to_labels[slug] for slug in query_slugs]

selected_labels = st.pills(
    "Selecione de 2 a 4 candidatos",
    list(labels_to_slugs),
    default=default_labels,
    selection_mode="multi",
    key="compare_candidates",
)
selected_slugs = [labels_to_slugs[label] for label in selected_labels]
if len(selected_slugs) < 2:
    st.warning("Selecione pelo menos dois candidatos para comparar.")
    st.stop()

with st.expander("Simular pesos dos 40 fatores", expanded=False):
    st.write(
        "A simulação muda somente o cenário atual. As notas-base permanecem intactas e a média é recalculada automaticamente."
    )
    reset_col, formula_col = st.columns([1, 3])
    with reset_col:
        if st.button("Restaurar pesos-base", icon=":material/restart_alt:", width="stretch"):
            st.session_state.pop("weight_editor", None)
            st.rerun()
    with formula_col:
        st.caption("Peso-base = arredondamento de (essencialidade + concentração + recomposição + efeito sistêmico + coerção) ÷ 2.")
    editor_source = benchmark[["id", "block", "factor", "weight"]].rename(
        columns={"id": "ID", "block": "Bloco", "factor": "Fator", "weight": "Peso"}
    )
    edited_weights = st.data_editor(
        editor_source,
        hide_index=True,
        width="stretch",
        height=460,
        disabled=["ID", "Bloco", "Fator"],
        column_config={
            "Peso": st.column_config.NumberColumn("Peso", min_value=0, max_value=5, step=1, format="%d")
        },
        key="weight_editor",
    )

custom_weights = {int(row.ID): float(row.Peso) for row in edited_weights.itertuples(index=False)}
ranking = weighted_scores(benchmark, selected_slugs, custom_weights)
dimensions = dimension_scores(benchmark, selected_slugs, custom_weights)
long_frame = long_scores(benchmark, selected_slugs)

metric_cols = st.columns(len(ranking))
for column, row in zip(metric_cols, ranking.itertuples(index=False)):
    column.metric(f"{row.candidate} · {row.party}", f"{row.score:.2f}".replace(".", ","))

tab_rank, tab_profile, tab_heatmap, tab_factors = st.tabs(
    ["Ranking", "Perfil por dimensão", "Mapa de notas", "Fatores decisivos"]
)
with tab_rank:
    st.plotly_chart(ranking_chart(ranking, "Resultado do cenário atual"), width="stretch", config=PLOTLY_CONFIG)
with tab_profile:
    st.plotly_chart(dimension_profile_chart(dimensions), width="stretch", config=PLOTLY_CONFIG)
with tab_heatmap:
    st.plotly_chart(score_heatmap(long_frame), width="stretch", config=PLOTLY_CONFIG)
with tab_factors:
    factor_labels = {f"{int(row.id)} · {row.factor}": int(row.id) for row in benchmark.itertuples(index=False)}
    default_ids = [7, 8, 16, 20, 28, 35, 37]
    default_factor_labels = [label for label, factor_id in factor_labels.items() if factor_id in default_ids]
    chosen = st.multiselect(
        "Fatores exibidos",
        list(factor_labels),
        default=default_factor_labels,
        placeholder="Escolha os fatores…",
    )
    if chosen:
        st.plotly_chart(
            factor_comparison_chart(long_frame, [factor_labels[label] for label in chosen]),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

st.caption("Use o ícone de câmera na barra de cada gráfico para baixar PNG em alta resolução.")

st.subheader("Tabela comparativa completa")
comparison = comparison_table_with_summary(benchmark, selected_slugs, custom_weights)
block_options = ["Todos", *benchmark["block"].drop_duplicates().tolist()]
selected_block = st.pills("Filtrar bloco da tabela", block_options, default="Todos", key="compare_block")
if selected_block == "Todos":
    shown = comparison
else:
    shown = pd.concat(
        [comparison[comparison["Bloco"] == selected_block], comparison[comparison["Bloco"] == "RESUMO"]],
        ignore_index=True,
    )
st.dataframe(shown, hide_index=True, width="stretch", height=620)

download_cols = st.columns(2)
with download_cols[0]:
    st.download_button(
        "Baixar comparação CSV",
        csv_bytes(comparison),
        file_name="comparacao-presidencia-2026.csv",
        mime="text/csv",
        icon=":material/download:",
        width="stretch",
    )
with download_cols[1]:
    st.download_button(
        "Baixar cenário JSON",
        json_bytes(export_payload(benchmark, selected_slugs, custom_weights)),
        file_name="cenario-presidencia-2026.json",
        mime="application/json",
        icon=":material/download:",
        width="stretch",
    )
