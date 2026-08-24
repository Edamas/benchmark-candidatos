from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import (
    dimension_profile_chart,
    factor_comparison_chart,
    factor_radar_chart,
    ranking_chart,
    score_heatmap,
)
from src.config import KEY_FACTOR_IDS, PLOTLY_CONFIG
from src.data import (
    comparison_table_with_summary,
    csv_bytes,
    dimension_scores,
    export_payload,
    json_bytes,
    load_benchmark,
    load_candidates,
    load_original_basis,
    load_sources,
    long_scores,
    weighted_scores,
)
from src.navigation import get_selected_slugs
from src.ui import analytic_footer, hero


hero(
    "Comparar candidatos",
    "Conteúdo à esquerda, radar comparativo à direita e todas as tabelas no mesmo fluxo da página.",
)

benchmark = load_benchmark()
candidates = load_candidates()
labels_to_slugs = {f"{candidate['ballot_name']} · {candidate['party']}": candidate["slug"] for candidate in candidates}
slugs_to_labels = {value: key for key, value in labels_to_slugs.items()}
query_slugs = [
    slug
    for slug in get_selected_slugs([candidates[0]["slug"], candidates[1]["slug"]])
    if slug in slugs_to_labels
]
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
    st.write("A simulação muda somente o cenário atual; as notas-base permanecem intactas.")
    reset_col, formula_col = st.columns([1, 3])
    with reset_col:
        if st.button("Restaurar pesos-base", icon=":material/restart_alt:", width="stretch"):
            st.session_state.pop("weight_editor", None)
            st.rerun()
    with formula_col:
        st.caption(
            "Peso-base = arredondamento de (essencialidade + concentração + recomposição + efeito sistêmico + coerção) ÷ 2."
        )
    editor_source = benchmark[["id", "block", "factor", "weight"]].rename(
        columns={"id": "ID", "block": "Bloco", "factor": "Fator", "weight": "Peso"}
    )
    edited_weights = st.data_editor(
        editor_source,
        hide_index=True,
        width="stretch",
        height=460,
        disabled=["ID", "Bloco", "Fator"],
        column_config={"Peso": st.column_config.NumberColumn("Peso", min_value=0, max_value=5, step=1, format="%d")},
        key="weight_editor",
    )

custom_weights = {int(row.ID): float(row.Peso) for row in edited_weights.itertuples(index=False)}
ranking = weighted_scores(benchmark, selected_slugs, custom_weights)
dimensions = dimension_scores(benchmark, selected_slugs, custom_weights)
long_frame = long_scores(benchmark, selected_slugs)
comparison = comparison_table_with_summary(benchmark, selected_slugs, custom_weights)

factor_labels = {f"{int(row.id)} · {row.factor}": int(row.id) for row in benchmark.itertuples(index=False)}
default_factor_labels = [label for label, factor_id in factor_labels.items() if factor_id in KEY_FACTOR_IDS]

body, graph = st.columns([1.08, 0.92], gap="large", vertical_alignment="top")
with body:
    metric_cols = st.columns(2)
    for position, row in enumerate(ranking.itertuples(index=False)):
        metric_cols[position % 2].metric(f"{row.candidate} · {row.party}", f"{row.score:.2f}".replace(".", ","))

    st.subheader("Fatores exibidos no gráfico detalhado")
    chosen = st.multiselect(
        "Escolha os eixos ou fatores",
        list(factor_labels),
        default=default_factor_labels,
        placeholder="Escolha os fatores…",
    )
    chosen_ids = [factor_labels[label] for label in chosen]

    st.subheader("Tabela comparativa completa")
    block_options = ["Todos", *benchmark["block"].drop_duplicates().tolist()]
    selected_block = st.pills("Bloco", block_options, default="Todos", key="compare_block")
    if selected_block == "Todos":
        shown = comparison
    else:
        shown = pd.concat(
            [comparison[comparison["Bloco"] == selected_block], comparison[comparison["Bloco"] == "RESUMO"]],
            ignore_index=True,
        )
    st.dataframe(shown, hide_index=True, width="stretch", height=570)

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

with graph:
    with st.container(key="compare_chart_panel"):
        st.markdown('<div class="bcc-panel-label">Gráfico comparativo</div>', unsafe_allow_html=True)
        chart_type = st.segmented_control(
            "Tipo de gráfico",
            ["Radar-chave", "Radar por blocos", "Ranking", "Fatores", "Mapa"],
            default="Radar-chave",
            key="compare_chart_type",
        )
        if chart_type == "Radar-chave":
            figure = factor_radar_chart(long_frame, KEY_FACTOR_IDS, "Comparação dos fatores-chave")
        elif chart_type == "Radar por blocos":
            figure = dimension_profile_chart(dimensions, "Comparação por dimensão")
        elif chart_type == "Ranking":
            figure = ranking_chart(ranking, "Resultado do cenário atual")
        elif chart_type == "Fatores":
            figure = factor_comparison_chart(long_frame, chosen_ids or KEY_FACTOR_IDS)
        else:
            figure = score_heatmap(long_frame, "Mapa completo de notas")
        st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG)
        st.caption("O mesmo seletor funciona em desktop e celular.")

st.subheader("Tabela-base original · prós, contras e saldo por candidato")
base = load_original_basis()
base = base[base["slug"].isin(selected_slugs)].drop(columns=["slug"]).rename(
    columns={
        "Fator original": "Fator",
        "Peso original": "Peso",
        "Pontos +": "Nota prós",
        "Pontos −": "Nota contras",
        "Saldo original": "Saldo do fator",
    }
)
base["Fonte(s)"] = "Não informada na entrada original"
base_columns = [
    "Candidato",
    "Fator",
    "Peso",
    "Prós",
    "Contras",
    "Nota prós",
    "Nota contras",
    "Saldo do fator",
    "Fonte(s)",
]
st.dataframe(base[base_columns], hide_index=True, width="stretch", height=620)
st.download_button(
    "Baixar comentários da base",
    csv_bytes(base[base_columns]),
    file_name="comparacao-tabela-base.csv",
    mime="text/csv",
    icon=":material/download:",
)

source_keys = {"tse_candidates", "tse_finance", "constitution", "defense", "minerals", "ai"}
analytic_footer(
    [source for source in load_sources() if source["key"] in source_keys],
    [
        "A tabela original não continha fontes por linha; a lacuna é preservada em vez de preenchida por suposição.",
        "O radar-chave destaca terras raras, transição energética, indústria nacional e ferrovias/logística.",
        "Alterar pesos muda somente o cenário da sessão; as notas editoriais permanecem intactas.",
        "A média ponderada é sempre a última linha das tabelas revisadas.",
    ],
)
