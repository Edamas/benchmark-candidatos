from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import contribution_chart, dimension_profile_chart, finance_chart
from src.config import PLOTLY_CONFIG
from src.connectors import TSE_DATASETS, wikipedia_summary
from src.data import (
    SCORE_COLUMNS,
    candidate_map,
    candidate_table_with_summary,
    csv_bytes,
    dimension_scores,
    factor_note,
    json_bytes,
    load_benchmark,
    load_candidates,
    load_finance,
    load_sources,
    weighted_scores,
)
from src.navigation import get_route_param, go_to
from src.ui import evidence_notice, format_score, hero


candidates = load_candidates()
candidates_by_slug = candidate_map()
valid_slugs = list(candidates_by_slug)
slug = get_route_param("candidato")

if slug not in valid_slugs:
    labels = {f"{candidate['ballot_name']} · {candidate['party']}": candidate["slug"] for candidate in candidates}
    hero("Ficha do candidato", "Escolha um nome para abrir a ficha completa.")
    choice = st.segmented_control("Candidato", list(labels), default=list(labels)[0])
    slug = labels[choice]
    if st.button("Abrir ficha", type="primary", icon=":material/person:"):
        go_to("app_pages/profile.py", {"candidato": slug})
    st.stop()

candidate = candidates_by_slug[slug]
benchmark = load_benchmark()
ranking = weighted_scores(benchmark, [slug])
score = float(ranking.iloc[0]["score"])

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

metric_cols = st.columns(4)
metric_cols[0].metric("Índice ponderado", format_score(score), help="Média calculada com os pesos-base.")
metric_cols[1].metric("Partido", candidate["party"])
metric_cols[2].metric("Número", candidate["number"])
metric_cols[3].metric("Fatores avaliados", len(benchmark))

evidence_notice()

tab_overview, tab_sovereignty, tab_finance, tab_bio = st.tabs(
    ["Visão geral", "Soberania", "Financiamento", "Biografia e links"]
)

with tab_overview:
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("Síntese da avaliação")
        st.write(candidate["summary"])
        st.caption(candidate["benchmark_basis"])
        st.info(candidate["registration_notice"])
    with right:
        dimensions = dimension_scores(benchmark, [slug])
        st.plotly_chart(
            dimension_profile_chart(dimensions, "Perfil estratégico"),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

with tab_sovereignty:
    st.subheader("Notas, pesos e média ponderada")
    st.write("A última linha é o resumo calculado. A média não é tratada como uma coluna independente.")
    blocks = ["Todos", *benchmark["block"].drop_duplicates().tolist()]
    selected_block = st.pills("Bloco", blocks, default="Todos")
    full_table = candidate_table_with_summary(benchmark, slug)
    if selected_block == "Todos":
        displayed = full_table
    else:
        displayed = pd.concat(
            [
                full_table[full_table["Bloco"] == selected_block],
                full_table[full_table["Bloco"] == "RESUMO"],
            ],
            ignore_index=True,
        )
    st.dataframe(
        displayed,
        hide_index=True,
        width="stretch",
        height=620,
        column_config={
            "Peso": st.column_config.NumberColumn(format="%.0f"),
            "Nota": st.column_config.NumberColumn(format="%.2f"),
            "Contribuição": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.plotly_chart(
        contribution_chart(full_table[full_table["Bloco"] != "RESUMO"], candidate["ballot_name"]),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

    factor_options = {
        f"{int(row.id)} · {row.factor}": int(row.id) for row in benchmark.itertuples(index=False)
    }
    selected_factor_label = st.selectbox("Examinar fundamento de uma nota", list(factor_options))
    selected_row = benchmark.loc[benchmark["id"] == factor_options[selected_factor_label]].iloc[0]
    note, source_keys = factor_note(slug, selected_row)
    st.markdown(f"**{selected_row['factor']} — nota {selected_row[SCORE_COLUMNS[slug]]:g}, peso {selected_row['weight']:g}**")
    st.write(selected_row["definition"])
    st.info(note)
    source_map = {source["key"]: source for source in load_sources()}
    if source_keys:
        for source_key in source_keys:
            source = source_map[source_key]
            st.link_button(source["title"], source["url"], icon=":material/open_in_new:")
    else:
        st.link_button("Abrir plano oficial no TSE", candidate["plan_url"], icon=":material/open_in_new:")

    download_cols = st.columns(2)
    with download_cols[0]:
        st.download_button(
            "Baixar tabela CSV",
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

with tab_finance:
    st.subheader("Doações e prestação de contas")
    finance = load_finance()
    candidate_finance = finance[finance["candidate_slug"] == slug] if not finance.empty else finance
    if candidate_finance.empty:
        st.warning(
            "O snapshot financeiro local ainda não contém lançamentos para esta candidatura. "
            "Isso significa dado indisponível nesta cópia — não significa arrecadação zero."
        )
        st.link_button(
            "Consultar prestação de contas no TSE",
            TSE_DATASETS["Prestação de contas"]["page"],
            icon=":material/open_in_new:",
        )
    else:
        total = float(candidate_finance["amount"].sum())
        st.metric("Receitas no snapshot", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.plotly_chart(finance_chart(candidate_finance, candidate["ballot_name"]), width="stretch", config=PLOTLY_CONFIG)
        st.dataframe(candidate_finance, hide_index=True, width="stretch")
        st.download_button(
            "Baixar doações CSV",
            csv_bytes(candidate_finance),
            file_name=f"{slug}-doacoes.csv",
            mime="text/csv",
            icon=":material/download:",
        )

with tab_bio:
    st.subheader("Biografia suplementar")
    wiki = wikipedia_summary(candidate["wiki_title"])
    if wiki.get("ok"):
        left, right = st.columns([1, 3])
        with left:
            if wiki.get("thumbnail"):
                st.image(wiki["thumbnail"], caption=f"Imagem: Wikipédia · {wiki['title']}")
        with right:
            if wiki.get("description"):
                st.caption(wiki["description"])
            st.write(wiki.get("extract") or "Resumo não disponível.")
            if wiki.get("url"):
                st.link_button("Abrir artigo na Wikipédia", wiki["url"], icon=":material/open_in_new:")
    else:
        st.warning("A Wikipédia não respondeu agora. A falha não altera os dados oficiais nem as notas.")

    st.subheader("Links primários")
    links = [
        {"Recurso": "Plano de governo", "Origem": "TSE", "URL": candidate["plan_url"]},
        {"Recurso": "Cadastro e documentos", "Origem": "TSE", "URL": TSE_DATASETS["Candidaturas"]["page"]},
        {"Recurso": "Prestação de contas", "Origem": "TSE", "URL": TSE_DATASETS["Prestação de contas"]["page"]},
    ]
    st.dataframe(
        pd.DataFrame(links),
        hide_index=True,
        width="stretch",
        column_config={"URL": st.column_config.LinkColumn("Abrir")},
    )
