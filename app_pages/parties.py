from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data import load_candidates
from src.ui import hero


hero(
    "Partidos",
    "Visão concisa das legendas presentes no recorte atual. O benchmark pertence ao candidato e não é automaticamente atribuído ao partido.",
)

candidates = load_candidates()
table = pd.DataFrame(
    [
        {
            "Sigla": candidate["party"],
            "Partido": candidate["party_name"],
            "Número": candidate["number"],
            "Candidato no recorte": candidate["ballot_name"],
        }
        for candidate in candidates
    ]
).sort_values("Sigla")

st.dataframe(table, hide_index=True, width="stretch")
st.info(
    "Espectro político será acrescentado apenas depois de definida uma taxonomia com fonte, período e critérios. "
    "Rótulos vagos como “direita” ou “esquerda” não alteram notas por si mesmos."
)
