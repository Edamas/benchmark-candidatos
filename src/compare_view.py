from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import ranking_chart, score_heatmap
from src.config import PLOTLY_CONFIG
from src.data import (
    SCORE_COLUMNS,
    candidate_map,
    comparison_table_with_summary,
    csv_bytes,
    export_payload,
    json_bytes,
    load_benchmark,
    load_candidates,
    load_sources,
    load_tse_candidates,
    long_scores,
    overview_scores,
    weighted_scores,
)
from src.radar import render_factor_radar, render_radar
from src.ui import analytic_footer, hero


VIEW_TITLES = {
    "overview": ("Comparação geral", "Ranking, cadastro oficial e radar das nove dimensões de soberania."),
    "radar": ("Radar por fatores", "Escolha qualquer conjunto de fatores, sem categorias privilegiadas previamente."),
    "map": ("Mapa de notas", "Leia as notas dos 40 fatores lado a lado e encontre convergências e diferenças."),
    "weights": ("Pesos e tabela", "Simule pesos e audite a média ponderada na última linha da tabela."),
}


def _official_comparison(slugs: list[str]) -> pd.DataFrame:
    snapshot = load_tse_candidates()
    selected = snapshot[snapshot["candidate_slug"].isin(slugs)].copy()
    selected["Avaliação editorial"] = selected["candidate_slug"].map(
        lambda slug: "40 fatores avaliados" if slug in SCORE_COLUMNS else "Pendente"
    )
    return selected.rename(
        columns={
            "NM_URNA_CANDIDATO": "Candidato",
            "NR_CANDIDATO": "Número",
            "SG_PARTIDO": "Partido",
            "DT_NASCIMENTO": "Nascimento",
            "DS_GRAU_INSTRUCAO": "Escolaridade",
            "DS_OCUPACAO": "Ocupação",
            "NM_COLIGACAO": "Coligação",
            "DS_SITUACAO_CANDIDATURA": "Situação TSE (bruta)",
        }
    )[
        ["Candidato", "Número", "Partido", "Nascimento", "Escolaridade", "Ocupação", "Coligação", "Situação TSE (bruta)", "Avaliação editorial"]
    ]


def render_compare_view(view: str = "overview") -> None:
    title, description = VIEW_TITLES.get(view, VIEW_TITLES["overview"])
    hero(title, description, "Comparar · Presidência 2026")

    benchmark = load_benchmark()
    candidates = load_candidates()
    by_slug = candidate_map()
    labels = {f"{candidate['ballot_name']} · {candidate['party']}": candidate["slug"] for candidate in candidates}
    selected_labels = st.pills(
        "Candidaturas incluídas",
        list(labels),
        default=list(labels),
        selection_mode="multi",
        key=f"compare_candidates_{view}",
    )
    selected_slugs = [labels[label] for label in selected_labels]
    if not selected_slugs:
        st.warning("Selecione ao menos uma candidatura.")
        st.stop()

    evaluated_slugs = [slug for slug in selected_slugs if slug in SCORE_COLUMNS]
    pending_slugs = [slug for slug in selected_slugs if slug not in SCORE_COLUMNS]
    st.caption(
        f"{len(selected_slugs)} pedidos selecionados · {len(evaluated_slugs)} com avaliação concluída · "
        f"{len(pending_slugs)} sem notas presumidas. Todos os 13 vêm selecionados por padrão."
    )
    if pending_slugs:
        pending_names = ", ".join(by_slug[slug]["ballot_name"] for slug in pending_slugs)
        st.info(f"Sem avaliação documental concluída: {pending_names}. Eles permanecem nas tabelas oficiais, mas não são desenhados com notas inventadas.")

    custom_weights: dict[int, float] | None = None
    if view == "weights":
        with st.expander("Simular pesos dos 40 fatores", expanded=True):
            st.caption("A simulação altera apenas esta página. Notas editoriais e base publicada não são modificadas.")
            editor = benchmark[["id", "block", "factor", "weight"]].rename(
                columns={"id": "ID", "block": "Bloco", "factor": "Fator", "weight": "Peso"}
            )
            edited = st.data_editor(
                editor,
                hide_index=True,
                width="stretch",
                height=440,
                disabled=["ID", "Bloco", "Fator"],
                column_config={"Peso": st.column_config.NumberColumn(min_value=0, max_value=5, step=1, format="%d")},
                key="comparison_weight_editor",
            )
            custom_weights = {int(row.ID): float(row.Peso) for row in edited.itertuples(index=False)}

    ranking = weighted_scores(benchmark, evaluated_slugs, custom_weights) if evaluated_slugs else pd.DataFrame()
    overview = overview_scores(benchmark, evaluated_slugs, custom_weights) if evaluated_slugs else pd.DataFrame()
    long_frame = long_scores(benchmark, evaluated_slugs) if evaluated_slugs else pd.DataFrame()
    comparison = (
        comparison_table_with_summary(benchmark, evaluated_slugs, custom_weights)
        if evaluated_slugs else pd.DataFrame()
    )

    factor_labels = {f"{int(row.id)} · {row.factor}": int(row.id) for row in benchmark.itertuples(index=False)}
    weighted_default = benchmark.sort_values(["weight", "id"], ascending=[False, True]).head(8)["id"].tolist()
    default_factor_labels = [label for label, factor_id in factor_labels.items() if factor_id in weighted_default]
    chosen_ids: list[int] = []

    body, graph = st.columns([0.98, 1.02], gap="large", vertical_alignment="top")
    with body:
        if view == "overview":
            st.subheader("Cadastro oficial comparado")
            st.dataframe(_official_comparison(selected_slugs), hide_index=True, width="stretch", height=470)
            if not ranking.empty:
                st.subheader("Média ponderada · avaliações concluídas")
                st.dataframe(
                    ranking.rename(columns={"candidate": "Candidato", "party": "Partido", "score": "Média ponderada"})[
                        ["Candidato", "Partido", "Média ponderada"]
                    ],
                    hide_index=True,
                    width="stretch",
                )
        elif view == "radar":
            st.subheader("Escolha dos fatores")
            chosen = st.multiselect(
                "De 3 a 12 fatores",
                list(factor_labels),
                default=default_factor_labels,
                max_selections=12,
                help="A seleção inicial contém os oito primeiros fatores de maior peso, não um grupo temático especial.",
            )
            chosen_ids = [factor_labels[label] for label in chosen]
            selected_rows = benchmark[benchmark["id"].isin(chosen_ids)][["id", "block", "factor", "weight", "definition"]]
            st.dataframe(selected_rows, hide_index=True, width="stretch", height=510)
        else:
            st.subheader("Tabela comparativa dos 40 fatores")
            if comparison.empty:
                st.info("Nenhuma candidatura selecionada possui avaliação concluída.")
            else:
                st.dataframe(comparison, hide_index=True, width="stretch", height=650)
                st.download_button(
                    "Baixar comparação CSV",
                    csv_bytes(comparison),
                    "comparacao-presidencia-2026.csv",
                    "text/csv",
                    icon=":material/download:",
                )

        if evaluated_slugs:
            st.download_button(
                "Baixar cenário JSON",
                json_bytes(
                    {
                        "selected_official_candidates": [by_slug[slug] for slug in selected_slugs],
                        "evaluated_benchmark": export_payload(benchmark, evaluated_slugs, custom_weights),
                        "not_evaluated": pending_slugs,
                    }
                ),
                "cenario-presidencia-2026.json",
                "application/json",
                icon=":material/download:",
            )

    with graph:
        with st.container(key="compare_chart_panel"):
            st.markdown('<div class="bcc-panel-label">Gráfico comparativo</div>', unsafe_allow_html=True)
            if not evaluated_slugs:
                st.info("Selecione ao menos uma candidatura com avaliação concluída para desenhar um gráfico de notas.")
            elif view == "radar":
                if len(chosen_ids) < 3:
                    st.warning("Escolha pelo menos três fatores para formar o radar.")
                else:
                    render_factor_radar(long_frame, chosen_ids, "Fatores selecionados", key="compare_factor_radar")
            elif view == "map":
                st.plotly_chart(score_heatmap(long_frame, "Mapa completo · 40 fatores"), width="stretch", config=PLOTLY_CONFIG)
            elif view == "weights":
                render_radar(overview, "Cenário com pesos simulados", key="compare_weight_radar")
            else:
                render_radar(overview, "Visão geral · 40 fatores", key="compare_overview_radar")
                st.plotly_chart(ranking_chart(ranking, "Média ponderada"), width="stretch", config=PLOTLY_CONFIG)
            st.caption("Somente avaliações concluídas são traçadas; os demais registros continuam visíveis nas tabelas.")

    analytic_footer(
        [source for source in load_sources() if source["key"] in {"tse_candidates", "constitution", "defense", "minerals", "ai"}],
        [
            "Todos os 13 pedidos de candidatura são selecionados por padrão.",
            "O radar geral agrega todos os 40 fatores em nove dimensões; o radar por fatores não privilegia quatro temas.",
            "Ausência de avaliação não é convertida em nota zero.",
            "A média ponderada é a última linha das tabelas de notas.",
        ],
    )
