from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import contribution_chart, finance_chart, individual_scores_chart
from src.config import PLOTLY_CONFIG
from src.connectors import wikipedia_sections, wikipedia_summary
from src.data import (
    SCORE_COLUMNS,
    candidate_map,
    candidate_official_record,
    candidate_table_with_summary,
    csv_bytes,
    json_bytes,
    load_benchmark,
    load_candidates,
    load_finance,
    load_sources,
    original_candidate_table_with_summary,
    overview_scores,
    weighted_scores,
)
from src.navigation import get_route_param
from src.radar import render_radar
from src.ui import analytic_footer, format_score, hero


def _official_table(record: dict) -> pd.DataFrame:
    fields = [
        ("Nome completo", "NM_CANDIDATO"),
        ("Nome de urna", "NM_URNA_CANDIDATO"),
        ("Número", "NR_CANDIDATO"),
        ("Partido", "SG_PARTIDO"),
        ("Nascimento", "DT_NASCIMENTO"),
        ("UF de nascimento", "SG_UF_NASCIMENTO"),
        ("Escolaridade", "DS_GRAU_INSTRUCAO"),
        ("Ocupação", "DS_OCUPACAO"),
        ("Coligação", "NM_COLIGACAO"),
        ("Situação bruta no arquivo", "DS_SITUACAO_CANDIDATURA"),
        ("Sequencial TSE", "SQ_CANDIDATO"),
        ("Data do snapshot", "snapshot_date"),
    ]
    return pd.DataFrame(
        [{"Campo": label, "Valor": record.get(key, "Não informado") or "Não informado"} for label, key in fields]
    )


def _wikipedia_panel(candidate: dict) -> None:
    st.subheader("Wikipédia")
    st.caption(
        "Fonte enciclopédica secundária, editável e sujeita a mudanças. Controvérsia não equivale a condenação; "
        "o texto abaixo só aparece quando o próprio verbete contém seção com título correspondente."
    )
    with st.spinner("Consultando o verbete e suas seções…", show_time=True):
        wiki = wikipedia_summary(candidate.get("wiki_title"))
        sections = wikipedia_sections(candidate.get("wiki_title"))
    if not wiki.get("ok"):
        st.info("Não foi localizado um verbete individual confiável para associar automaticamente a este nome.")
        return
    if wiki.get("thumbnail"):
        st.image(wiki["thumbnail"], width=140)
    st.markdown(f"**{wiki.get('title', candidate['ballot_name'])}**")
    if wiki.get("description"):
        st.caption(wiki["description"])
    st.write(wiki.get("extract") or "Resumo não disponível.")
    if wiki.get("url"):
        st.link_button("Abrir verbete completo", wiki["url"], icon=":material/open_in_new:")

    groups = sections.get("groups", {}) if sections.get("ok") else {}
    labels = ["Trajetória", "Prêmios e reconhecimentos", "Controvérsias e questões públicas"]
    tabs = st.tabs(labels)
    for tab, label in zip(tabs, labels):
        with tab:
            entries = groups.get(label, [])
            if not entries:
                st.caption("Nenhuma seção explicitamente identificada com esse tema no verbete consultado.")
            for entry in entries:
                st.markdown(f"**{entry['heading']}**")
                st.write(entry["extract"])


def render_candidate_profile(slug_override: str | None = None) -> None:
    candidates = load_candidates()
    by_slug = candidate_map()
    slug = slug_override or get_route_param("candidato")
    if slug not in by_slug:
        hero("Ficha do candidato", "Escolha um nome no menu Presidência para abrir a ficha completa.")
        st.stop()

    candidate = by_slug[slug]
    record = candidate_official_record(slug)
    benchmark = load_benchmark()
    evaluated = slug in SCORE_COLUMNS

    hero(
        candidate["ballot_name"],
        f"{candidate['full_name']} · {candidate['party']} · nº {candidate['number']}",
        "Ficha completa · Presidência 2026",
    )
    link_cols = st.columns([1, 1, 3])
    with link_cols[0]:
        st.link_button("Perfil no TSE", candidate["tse_profile_url"], icon=":material/open_in_new:", width="stretch")
    with link_cols[1]:
        if candidate.get("plan_url"):
            st.link_button("Plano no TSE", candidate["plan_url"], icon=":material/description:", width="stretch")

    if evaluated:
        ranking = weighted_scores(benchmark, [slug])
        score = float(ranking.iloc[0]["score"])
        overview = overview_scores(benchmark, [slug])
        full_table = candidate_table_with_summary(benchmark, slug)
        original_table = (
            original_candidate_table_with_summary(slug)
            if slug in {"lula", "renan", "flavio", "caiado"}
            else pd.DataFrame()
        )
    else:
        score = None
        overview = pd.DataFrame()
        full_table = pd.DataFrame()
        original_table = pd.DataFrame()

    body, graph = st.columns([0.98, 1.02], gap="large", vertical_alignment="top")
    with body:
        metrics = st.columns(3)
        metrics[0].metric("Avaliação", format_score(score) if score is not None else "Pendente")
        metrics[1].metric("Partido · número", f"{candidate['party']} · {candidate['number']}")
        metrics[2].metric("Fatores avaliados", len(benchmark) if evaluated else 0)
        st.subheader("Síntese")
        st.write(candidate["summary"])
        st.caption(candidate["registration_notice"])
        if not evaluated:
            st.warning(
                "Este pedido de candidatura já está no cadastro oficial, mas ainda não passou pela revisão editorial "
                "dos 40 fatores. O app não cria notas automáticas nem usa ausência de informação como zero."
            )

        section_tabs = st.tabs(["Soberania", "Dados oficiais", "Wikipédia", "Financiamento"])
        with section_tabs[0]:
            if evaluated:
                st.subheader("Fatores, pesos, notas e fundamentos")
                st.write(
                    "A média ponderada é a última linha. Nota prós é a nota de autonomia; nota contras é seu "
                    "complemento até 10; o saldo varia de −10 a +10. Páginas indicam onde a proposta foi localizada."
                )
                display = full_table.copy()
                visible = [
                    "Fator", "Peso", "Prós", "Contras", "Nota prós", "Nota contras",
                    "Saldo do fator", "Fonte(s)", "Evidência", "Confiança", "URL da fonte", "Fundamento",
                ]
                st.dataframe(
                    display[visible],
                    hide_index=True,
                    width="stretch",
                    height=620,
                    column_config={
                        "URL da fonte": st.column_config.LinkColumn("Fonte", display_text="Abrir"),
                        "Peso": st.column_config.NumberColumn(format="%.0f"),
                        "Nota revisada": st.column_config.NumberColumn(format="%.2f"),
                    },
                )
                downloads = st.columns(2)
                downloads[0].download_button(
                    "Baixar tabela CSV", csv_bytes(display), f"{slug}-fatores.csv", "text/csv",
                    icon=":material/download:", width="stretch",
                )
                downloads[1].download_button(
                    "Baixar ficha JSON",
                    json_bytes({"candidate": candidate, "official": record, "weighted_score": score, "factors": display.to_dict("records")}),
                    f"{slug}-ficha.json", "application/json", icon=":material/download:", width="stretch",
                )
                if not original_table.empty:
                    with st.expander("Base original preservada"):
                        st.dataframe(original_table, hide_index=True, width="stretch", height=520)
            else:
                st.info("Avaliação fator a fator pendente de pesquisa e revisão documental.")
        with section_tabs[1]:
            st.subheader("Cadastro oficial do TSE")
            st.dataframe(_official_table(record), hide_index=True, width="stretch")
            st.caption("O código #NE é reproduzido literalmente do arquivo do TSE; o app não lhe atribui uma decisão judicial.")
        with section_tabs[2]:
            _wikipedia_panel(candidate)
        with section_tabs[3]:
            st.subheader("Financiamento eleitoral")
            finance = load_finance()
            candidate_finance = finance[finance["candidate_slug"] == slug] if not finance.empty else finance
            if candidate_finance.empty:
                st.warning("O snapshot local ainda não contém lançamentos. Dado indisponível não significa arrecadação zero.")
            else:
                total = float(candidate_finance["amount"].sum())
                st.metric("Receitas no snapshot", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.plotly_chart(finance_chart(candidate_finance, candidate["ballot_name"]), width="stretch", config=PLOTLY_CONFIG)
                st.dataframe(candidate_finance, hide_index=True, width="stretch")

    with graph:
        with st.container(key="profile_chart_panel"):
            st.markdown('<div class="bcc-panel-label">Gráfico do candidato</div>', unsafe_allow_html=True)
            if evaluated:
                chart_type = st.segmented_control(
                    "Tipo de gráfico",
                    ["Radar geral", "Contribuições", "Notas · 40"],
                    default="Radar geral",
                    key=f"profile_chart_{slug}",
                )
                if chart_type == "Radar geral":
                    render_radar(overview, f"40 fatores · {candidate['ballot_name']}", key=f"profile_radar_{slug}")
                elif chart_type == "Contribuições":
                    st.plotly_chart(
                        contribution_chart(full_table[full_table["Bloco"] != "RESUMO"], candidate["ballot_name"]),
                        width="stretch", config=PLOTLY_CONFIG,
                    )
                else:
                    st.plotly_chart(individual_scores_chart(full_table, candidate["ballot_name"]), width="stretch", config=PLOTLY_CONFIG)
                st.caption("O radar agrega todos os 40 fatores em nove dimensões; nenhum fator recebe destaque visual exclusivo.")
            else:
                st.info("O gráfico será habilitado quando a avaliação documental dos 40 fatores for concluída.")
                st.dataframe(_official_table(record), hide_index=True, width="stretch")

    source_keys = {"tse_candidates", "tse_finance", "constitution", "defense", "minerals", "ai", "wiki"}
    analytic_footer(
        [source for source in load_sources() if source["key"] in source_keys],
        [
            candidate["benchmark_basis"],
            "Pedido registrado não equivale a candidatura definitivamente deferida.",
            "Wikipédia é fonte secundária; alegações e controvérsias exigem conferência nas referências do verbete.",
            "Uma nota não prevê execução futura nem mede a qualidade geral do candidato.",
        ],
        plan_url=candidate.get("plan_url") or None,
    )
