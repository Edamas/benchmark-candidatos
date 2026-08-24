from __future__ import annotations

import pandas as pd
import streamlit as st

from src.connectors import probe_tse_sources
from src.data import WEIGHT_COMPONENTS, load_benchmark, load_sources
from src.ui import hero


hero(
    "Dados e metodologia",
    "Critérios escritos como norma, trilha de fontes e limitações explícitas para que o leitor possa discordar de modo verificável.",
    "Transparência",
)

tab_rule, tab_weights, tab_sources, tab_limits = st.tabs(
    ["Norma de avaliação", "Pesos", "Fontes e atualização", "Limites e versões"]
)

with tab_rule:
    articles = [
        ("Art. 1º — Objeto", "Estimar, de modo uniforme, a tendência de programas, atos e declarações presidenciais de fortalecer ou reduzir a soberania e a autonomia estratégica do Brasil."),
        ("Art. 2º — Soberania nacional", "Capacidade efetiva e continuada de o Estado e a sociedade brasileiros decidirem, produzirem, financiarem, protegerem e substituírem bens, serviços e tecnologias essenciais sem subordinação indevida a governo, empresa ou plataforma estrangeira."),
        ("Art. 3º — Autonomia estratégica", "Liberdade prática de escolher parceiros, políticas e meios de ação, sustentada por capacidade doméstica, diversificação externa, reservas, redundância e poder de barganha."),
        ("Art. 4º — Dependência crítica", "Dependência externa cuja interrupção, condicionamento ou captura possa comprometer defesa, alimentação, saúde, energia, finanças, dados, comunicações, logística, território ou funcionamento do Estado."),
        ("Art. 5º — Controle nacional", "Poder jurídico e material de decidir sobre operação, investimento, dados, propriedade intelectual, continuidade e alienação de ativo estratégico. Propriedade estatal não garante, por si só, autonomia; propriedade privada não a exclui quando houver controle e salvaguardas brasileiras."),
        ("Art. 6º — Domínio tecnológico", "Capacidade brasileira de pesquisar, projetar, modificar, produzir, manter e evoluir tecnologia, com acesso à engenharia, código, documentação, pessoal e propriedade intelectual necessários."),
        ("Art. 7º — Agregação de valor", "Transformação, processamento, engenharia, marcas e serviços realizados no Brasil; simples extração ou exportação primária não equivale a autonomia produtiva."),
        ("Art. 8º — Diversificação", "Existência de múltiplos fornecedores, mercados, moedas, rotas e parceiros, evitando alinhamento automático ou concentração capaz de permitir coerção."),
        ("Art. 9º — Salvaguardas", "Reciprocidade, análise de segurança nacional, limites de controle, conteúdo local eficiente, transferência tecnológica, proteção de dados, concorrência, estoques, reversibilidade e continuidade."),
        ("Art. 10 — Cooperação internacional", "Cooperação, comércio e investimento estrangeiro não são entreguismo por natureza; são positivos quando aumentam capacidade brasileira, alternativas e poder de decisão, e negativos quando transferem controle ou criam dependência crítica."),
        ("Art. 11 — Evidência", "A nota deve se apoiar, em ordem de força, em ato executado e comprovado; plano oficial; proposta formal; declaração inequívoca. Associação partidária, intenção presumida e adjetivo não constituem evidência."),
        ("Art. 12 — Imputação", "Atos de familiar, aliado, partido ou grupo não são atribuídos automaticamente ao candidato. Só entram quando houver autoria, adesão ou compromisso próprio documentado."),
    ]
    for title, body in articles:
        st.markdown(f"**{title}**")
        st.write(body)

    st.subheader("Escala de notas")
    scale = pd.DataFrame(
        [
            ("10", "Autonomia robusta, concreta e acompanhada de salvaguardas"),
            ("8–9", "Forte ganho de autonomia"),
            ("6–7", "Ganho parcial ou com riscos"),
            ("5", "Neutro, ambíguo ou evidência insuficiente"),
            ("3–4", "Dependência relevante"),
            ("1–2", "Dependência grave"),
            ("0", "Subordinação estrutural explícita"),
        ],
        columns=["Nota", "Interpretação"],
    )
    st.dataframe(scale, hide_index=True, width="stretch")

with tab_weights:
    st.subheader("Regra dos pesos")
    st.write(
        "Cada componente recebe 0, 1 ou 2. O peso-base é o arredondamento convencional da metade da soma, "
        "limitado ao intervalo de 1 a 5. Assim, popularidade, ideologia ou expectativa eleitoral não alteram o peso."
    )
    st.latex(r"peso=\operatorname{arred}\left(\frac{E+C+R+S+X}{2}\right)")
    definitions = pd.DataFrame(
        [
            ("E — Essencialidade", "Impacto sobre funções vitais do país"),
            ("C — Concentração externa", "Dependência de poucos países ou fornecedores"),
            ("R — Tempo de recomposição", "Dificuldade de reconstruir a capacidade no Brasil"),
            ("S — Efeito sistêmico", "Capacidade de paralisar outros setores"),
            ("X — Exposição à coerção", "Possibilidade de sanção, bloqueio ou condicionamento externo"),
        ],
        columns=["Componente", "Pergunta operacional"],
    )
    st.dataframe(definitions, hide_index=True, width="stretch")
    benchmark = load_benchmark()
    weights = benchmark[["id", "block", "factor", *WEIGHT_COMPONENTS, "weight"]].rename(
        columns={
            "id": "ID",
            "block": "Bloco",
            "factor": "Fator",
            "essentiality": "Essencialidade",
            "external_concentration": "Concentração externa",
            "replacement_time": "Recomposição",
            "systemic_effect": "Efeito sistêmico",
            "coercion_exposure": "Coerção",
            "weight": "Peso",
        }
    )
    st.dataframe(weights, hide_index=True, width="stretch", height=620)

with tab_sources:
    st.subheader("Catálogo de fontes")
    sources = pd.DataFrame(load_sources()).rename(
        columns={"title": "Fonte", "publisher": "Publicador", "type": "Tipo", "url": "URL", "use": "Uso", "cadence": "Atualização"}
    )
    display_cols = [column for column in ["Fonte", "Publicador", "Tipo", "Uso", "Atualização", "URL"] if column in sources]
    st.dataframe(
        sources[display_cols],
        hide_index=True,
        width="stretch",
        column_config={"URL": st.column_config.LinkColumn("Abrir fonte")},
    )
    st.write(
        "O TSE publica candidaturas quatro vezes ao dia e prestações de contas conforme o calendário da base. "
        "O app usa cache e mantém o último snapshot validado quando a origem não responde."
    )
    if st.button("Verificar acesso às bases do TSE", icon=":material/sync:"):
        with st.status("Consultando recursos oficiais…", expanded=False) as status:
            result = pd.DataFrame(probe_tse_sources())
            status.update(label="Verificação concluída", state="complete")
        st.dataframe(
            result,
            hide_index=True,
            width="stretch",
            column_config={
                "Página oficial": st.column_config.LinkColumn("Página oficial"),
                "Recurso": st.column_config.LinkColumn("Arquivo ZIP"),
            },
        )
        if not result["Disponível nesta rede"].all():
            st.warning("Uma falha de rede é mostrada como falha; nunca é convertida em zero, ausência de bens ou ausência de doações.")

with tab_limits:
    st.subheader("O que este índice não afirma")
    st.markdown(
        """
- Não prevê o comportamento futuro nem a capacidade de aprovar propostas.
- Não mede intenção de voto, competência administrativa, integridade pessoal ou qualidade geral do governo.
- Não considera “direita” ou “esquerda” como evidência suficiente.
- Não trata comércio ou investimento estrangeiro como negativos por definição.
- Não transforma ausência de dados em nota zero.
        """
    )
    st.subheader("Versão atual")
    st.write("**2026-08-24 · revisão 1**")
    st.write(
        "A nota de Lula em “Relação com os Estados Unidos” foi revista de 6 para 9 após incorporar documentos e atos oficiais sobre reciprocidade, resistência a pressões políticas e diversificação."
    )
