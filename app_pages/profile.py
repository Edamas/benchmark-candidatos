from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import (
    contribution_chart,
    dimension_profile_chart,
    factor_radar_chart,
    finance_chart,
    individual_scores_chart,
)
from src.config import KEY_FACTOR_IDS, PLOTLY_CONFIG
from src.connectors import wikipedia_summary
from src.data import (
    SCORE_COLUMNS,
    candidate_map,
    candidate_table_with_summary,
    csv_bytes,
    dimension_scores,
    factor_note,
    factor_sources,
    json_bytes,
    load_benchmark,
    load_candidates,
    load_finance,
    load_sources,
    long_scores,
    original_candidate_table_with_summary,
    weighted_scores,
)
from src.navigation import get_route_param, go_to
from src.ui import analytic_footer, format_score, hero


candidates = load_candidates()
candidates_by_slug = candidate_map()
valid_slugs = list(candidates_by_slug)
slug = get_route_param("candidato")

if slug not in valid_slugs:
    labels = {f"{candidate['ballot_name']} · {candidate['party']}": candidate["slug"] for candidate in candidates}
    hero("Ficha do candidato", "Escolha um nome para abrir a ficha completa.")
    choice = st.segmented_control("Candidato", list(labels), default=list(labels)[0])
    if st.button("Abrir ficha", type="primary", icon=":material/person:"):
        go_to("app_pages/profile.py", {"candidato": labels[choice]})
    st.stop()

candidate = candidates_by_slug[slug]
benchmark = load_benchmark()
ranking = weighted_scores(benchmark, [slug])
score = float(ranking.iloc[0]["score"])
dimensions = dimension_scores(benchmark, [slug])
long_frame = long_scores(benchmark, [slug])
full_table = candidate_table_with_summary(benchmark, slug)
candidate_basis = original_candidate_table_with_summary(slug)

hero(
    candidate["ballot_name"],
    f"{candidate['full_name']} · {candidate['party']} · {candidate['current_role']}",
    "Ficha do candidato · Presidência 2026",
)

actions = st.columns([1, 1, 4])
with actions[0]:
    if st.button("Voltar à eleição", icon=":material/arrow_back:", width="stretch"):
        go_to("app_pages/election.py")
with actions[1]:
    if st.button("Comparar", icon=":material/compare_arrows:", width="stretch"):
        other = next(value for value in valid_slugs if value != slug)
        go_to("app_pages/compare.py", {"candidatos": f"{slug},{other}"})

body, graph = st.columns([1.1, 0.9], gap="large", vertical_alignment="top")
with body:
    metric_row_1 = st.columns(2)
    metric_row_1[0].metric("Índice ponderado", format_score(score), help="Média calculada com os pesos-base.")
    metric_row_1[1].metric("Partido · número", f"{candidate['party']} · {candidate['number']}")
    metric_row_2 = st.columns(2)
    metric_row_2[0].metric("Fatores avaliados", len(benchmark))
    metric_row_2[1].metric("Pesos somados", int(benchmark["weight"].sum()))

    st.subheader("Síntese")
    st.write(candidate["summary"])
    st.caption(candidate["registration_notice"])

    st.subheader("Tabela de fatores · base original")
    st.write(
        "Os campos abaixo são preservados da entrada que serviu de base. A ausência de fonte por linha é explicitada, "
        "pois não seria correto inventar uma referência retrospectiva."
    )
    basis_display = candidate_basis.copy()
    basis_columns = [
        "Fator",
        "Peso",
        "Prós",
        "Contras",
        "Nota prós",
        "Nota contras",
        "Saldo do fator",
        "Fonte(s)",
    ]
    st.dataframe(
        basis_display[basis_columns],
        hide_index=True,
        width="stretch",
        height=540,
        column_config={
            "Peso": st.column_config.NumberColumn(format="%.0f"),
            "Nota prós": st.column_config.NumberColumn(format="%.0f"),
            "Nota contras": st.column_config.NumberColumn(format="%.0f"),
            "Saldo do fator": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    st.subheader("Revisão atual · notas de 0 a 10")
    st.write(
        "A média ponderada permanece na última linha; fatores sem correspondência direta são marcados. "
        "A coluna de URL abre a fonte principal usada na revisão."
    )
    blocks = ["Todos", *benchmark["block"].drop_duplicates().tolist()]
    selected_block = st.pills("Bloco", blocks, default="Todos", key="profile_block")
    if selected_block == "Todos":
        displayed = full_table
    else:
        displayed = pd.concat(
            [full_table[full_table["Bloco"] == selected_block], full_table[full_table["Bloco"] == "RESUMO"]],
            ignore_index=True,
        )
    visible_columns = [
        "ID",
        "Fator",
        "Peso",
        "Nota",
        "Prós (base)",
        "Contras (base)",
        "Nota prós (base)",
        "Nota contras (base)",
        "Saldo do fator (base)",
        "Evidência",
        "Fonte(s)",
        "URL da fonte",
        "Fundamento",
    ]
    st.dataframe(
        displayed[visible_columns],
        hide_index=True,
        width="stretch",
        height=540,
        column_config={
            "Peso": st.column_config.NumberColumn(format="%.0f"),
            "Nota": st.column_config.NumberColumn(format="%.2f"),
            "Nota prós (base)": st.column_config.NumberColumn(format="%.0f"),
            "Nota contras (base)": st.column_config.NumberColumn(format="%.0f"),
            "Saldo do fator (base)": st.column_config.NumberColumn(format="%.2f"),
            "URL da fonte": st.column_config.LinkColumn("Abrir fonte", display_text="Abrir"),
        },
    )

    factor_options = {f"{int(row.id)} · {row.factor}": int(row.id) for row in benchmark.itertuples(index=False)}
    selected_factor_label = st.selectbox("Examinar o fundamento", list(factor_options))
    selected_row = benchmark.loc[benchmark["id"] == factor_options[selected_factor_label]].iloc[0]
    note, source_keys = factor_note(slug, selected_row)
    selected_sources = factor_sources(slug, source_keys)
    st.markdown(
        f"**{selected_row['factor']} — nota {selected_row[SCORE_COLUMNS[slug]]:g}, peso {selected_row['weight']:g}**"
    )
    st.write(selected_row["definition"])
    st.info(note)
    source_links = st.columns(min(3, len(selected_sources))) if selected_sources else []
    for position, source in enumerate(selected_sources):
        with source_links[position % len(source_links)]:
            st.link_button(
                source["title"],
                source["url"],
                icon=":material/open_in_new:",
                width="stretch",
            )

    download_cols = st.columns(2)
    with download_cols[0]:
        st.download_button(
            "Baixar tabela revisada",
            csv_bytes(full_table),
            file_name=f"{slug}-notas-pesos.csv",
            mime="text/csv",
            icon=":material/download:",
            width="stretch",
        )
    with download_cols[1]:
        st.download_button(
            "Baixar ficha JSON",
            json_bytes({"candidate": candidate, "weighted_score": score, "factors": full_table.to_dict("records")}),
            file_name=f"{slug}-ficha.json",
            mime="application/json",
            icon=":material/download:",
            width="stretch",
        )

with graph:
    with st.container(key="profile_chart_panel"):
        st.markdown('<div class="bcc-panel-label">Gráfico do candidato</div>', unsafe_allow_html=True)
        chart_type = st.segmented_control(
            "Tipo de gráfico",
            ["Radar-chave", "Radar por blocos", "Contribuições", "Notas"],
            default="Radar-chave",
            key=f"profile_chart_type_{slug}",
        )
        if chart_type == "Radar-chave":
            figure = factor_radar_chart(long_frame, KEY_FACTOR_IDS, f"Fatores-chave · {candidate['ballot_name']}")
        elif chart_type == "Radar por blocos":
            figure = dimension_profile_chart(dimensions, f"Dimensões · {candidate['ballot_name']}")
        elif chart_type == "Contribuições":
            figure = contribution_chart(full_table[full_table["Bloco"] != "RESUMO"], candidate["ballot_name"])
        else:
            figure = individual_scores_chart(full_table, candidate["ballot_name"])
        st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG)
        st.caption("No celular, este painel aparece logo depois do conteúdo principal.")

st.download_button(
    "Baixar tabela-base original",
    csv_bytes(basis_display[basis_columns]),
    file_name=f"{slug}-tabela-base-original.csv",
    mime="text/csv",
    icon=":material/download:",
)

st.divider()
details_left, details_right = st.columns(2, gap="large", vertical_alignment="top")
with details_left:
    st.subheader("Financiamento")
    finance = load_finance()
    candidate_finance = finance[finance["candidate_slug"] == slug] if not finance.empty else finance
    if candidate_finance.empty:
        st.warning(
            "O snapshot local ainda não contém lançamentos para esta candidatura. Dado indisponível não significa arrecadação zero."
        )
    else:
        total = float(candidate_finance["amount"].sum())
        st.metric("Receitas no snapshot", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.plotly_chart(finance_chart(candidate_finance, candidate["ballot_name"]), width="stretch", config=PLOTLY_CONFIG)
        st.dataframe(candidate_finance, hide_index=True, width="stretch")

with details_right:
    st.subheader("Biografia suplementar")
    wiki = wikipedia_summary(candidate["wiki_title"])
    if wiki.get("ok"):
        if wiki.get("thumbnail"):
            st.image(wiki["thumbnail"], width=150)
        if wiki.get("description"):
            st.caption(wiki["description"])
        st.write(wiki.get("extract") or "Resumo não disponível.")
    else:
        st.warning("A Wikipédia não respondeu agora. A falha não altera dados oficiais nem notas.")

source_keys = {"tse_candidates", "tse_finance", "constitution", "defense", "minerals", "ai", "wiki"}
analytic_footer(
    [source for source in load_sources() if source["key"] in source_keys],
    [
        candidate["benchmark_basis"],
        "A tabela-base original é preservada para auditoria, mas não vale como comprovação independente.",
        "Correspondências entre a taxonomia antiga e a revisada são temáticas e ficam explícitas nas colunas de prós e contras.",
        "Uma nota não prevê execução futura nem mede a qualidade geral do candidato.",
    ],
    plan_url=candidate["plan_url"],
)
