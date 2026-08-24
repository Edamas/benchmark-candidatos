from __future__ import annotations

import streamlit as st

from src.data import candidate_map, load_benchmark, load_candidates, weighted_scores
from src.navigation import go_to
from src.ui import candidate_card, hero


hero(
    "Candidatos",
    "Acesse a ficha, as fontes, o financiamento disponível e a decomposição completa das notas.",
)

candidates = load_candidates()
benchmark = load_benchmark()
ranking = weighted_scores(benchmark).set_index("slug")

party_options = ["Todos", *sorted({candidate["party"] for candidate in candidates})]
selected_party = st.pills("Partido", party_options, default="Todos")
query = st.text_input("Buscar por nome", placeholder="Digite parte do nome…", icon=":material/search:")

filtered = [
    candidate
    for candidate in candidates
    if (selected_party == "Todos" or candidate["party"] == selected_party)
    and (not query or query.casefold() in candidate["full_name"].casefold() or query.casefold() in candidate["ballot_name"].casefold())
]

if not filtered:
    st.info("Nenhum candidato corresponde aos filtros.")
else:
    for start in range(0, len(filtered), 2):
        columns = st.columns(2)
        for column, candidate in zip(columns, filtered[start : start + 2]):
            with column:
                candidate_card(candidate, float(ranking.loc[candidate["slug"], "score"]))
                st.write(candidate["summary"])
                if st.button(
                    f"Abrir ficha de {candidate['ballot_name']}",
                    key=f"profile_{candidate['slug']}",
                    icon=":material/arrow_forward:",
                    width="stretch",
                ):
                    go_to("app_pages/profile.py", {"candidato": candidate["slug"]})
