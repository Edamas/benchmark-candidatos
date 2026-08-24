from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

import requests
import streamlit as st


USER_AGENT = "BrasilComCenso/0.1 (aplicacao civica; dados publicos)"
TIMEOUT = 12

TSE_DATASETS = {
    "Candidaturas": {
        "page": "https://dadosabertos.tse.jus.br/pt_BR/dataset/candidatos-2026",
        "resource": "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip",
    },
    "Informações complementares": {
        "page": "https://dadosabertos.tse.jus.br/pt_BR/dataset/candidatos-2026",
        "resource": "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand_complementar/consulta_cand_complementar_2026.zip",
    },
    "Bens declarados": {
        "page": "https://dadosabertos.tse.jus.br/pt_BR/dataset/candidatos-2026",
        "resource": "https://cdn.tse.jus.br/estatistica/sead/odsele/bem_candidato/bem_candidato_2026.zip",
    },
    "Redes sociais": {
        "page": "https://dadosabertos.tse.jus.br/pt_BR/dataset/candidatos-2026",
        "resource": "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/rede_social_candidato_2026.zip",
    },
    "Prestação de contas": {
        "page": "https://dadosabertos.tse.jus.br/pt_BR/dataset/prestacao-de-contas-eleitorais-2026",
        "resource": "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2026.zip",
    },
}


@st.cache_data(ttl=21600, show_spinner=False)
def wikipedia_summary(title: str) -> dict:
    url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}"
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        return {
            "ok": True,
            "title": payload.get("title", title),
            "description": payload.get("description", ""),
            "extract": payload.get("extract", ""),
            "url": payload.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "thumbnail": payload.get("thumbnail", {}).get("source", ""),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "title": title, "error": str(exc), "url": ""}


@st.cache_data(ttl=1800, show_spinner=False)
def probe_tse_sources() -> list[dict]:
    results: list[dict] = []
    headers = {"User-Agent": USER_AGENT, "Range": "bytes=0-0"}
    for name, source in TSE_DATASETS.items():
        try:
            response = requests.get(
                source["resource"], headers=headers, timeout=TIMEOUT, stream=True
            )
            ok = response.status_code in {200, 206}
            status = f"HTTP {response.status_code}"
            response.close()
        except requests.RequestException as exc:
            ok = False
            status = exc.__class__.__name__
        results.append(
            {
                "Fonte": name,
                "Disponível nesta rede": ok,
                "Resposta": status,
                "Página oficial": source["page"],
                "Recurso": source["resource"],
            }
        )
    return results
