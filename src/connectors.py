from __future__ import annotations

from datetime import datetime, timezone
import re
from urllib.parse import quote

import requests
import streamlit as st
from bs4 import BeautifulSoup


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
    if not title:
        return {"ok": False, "title": "", "error": "Não há verbete individual associado.", "url": ""}
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


WIKI_SECTION_GROUPS = {
    "Trajetória": re.compile(r"biografia|trajet[oó]ria|carreira|vida (?:pessoal|pol[ií]tica)|atua[cç][aã]o", re.I),
    "Prêmios e reconhecimentos": re.compile(r"pr[eê]mios?|premia[cç][oõ]es|honrarias?|condecor|reconhecimentos?|distin[cç][oõ]es", re.I),
    "Controvérsias e questões públicas": re.compile(
        r"controv|pol[eê]mic|cr[ií]tic|process|investiga|acusa|condena|not[ií]cias falsas|quest[oõ]es judiciais",
        re.I,
    ),
}


def _plain_wikipedia_section(html: str, limit: int = 1600) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("sup, style, script, table, .mw-editsection, .navbox, .infobox"):
        node.decompose()
    text = " ".join(soup.get_text(" ", strip=True).split())
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0]
    return clipped + "…"


def _section_text(heading, limit: int = 1600) -> str:
    level = int(heading.name[1])
    fragments: list[str] = []
    for sibling in heading.next_siblings:
        if getattr(sibling, "name", "") in {f"h{number}" for number in range(2, level + 1)}:
            break
        fragments.append(str(sibling))
    return _plain_wikipedia_section("".join(fragments), limit=limit)


@st.cache_data(ttl=21600, show_spinner=False)
def wikipedia_sections(title: str) -> dict:
    """Return short, explicitly labelled extracts; never infer a controversy."""
    if not title:
        return {"ok": False, "title": "", "groups": {}, "url": "", "error": "Sem verbete individual."}
    api = f"https://pt.wikipedia.org/api/rest_v1/page/html/{quote(title.replace(' ', '_'), safe='')}"
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(api, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        resolved_title = title
        groups: dict[str, list[dict]] = {label: [] for label in WIKI_SECTION_GROUPS}
        soup = BeautifulSoup(response.text, "html.parser")
        used: set[str] = set()
        for heading_node in soup.find_all(re.compile(r"^h[2-6]$")):
            heading = " ".join(heading_node.get_text(" ", strip=True).split())
            for label, pattern in WIKI_SECTION_GROUPS.items():
                if heading not in used and len(groups[label]) < 3 and pattern.search(heading):
                    text = _section_text(heading_node)
                    if text:
                        groups[label].append({"heading": heading, "extract": text})
                    used.add(heading)
                    break

        return {
            "ok": True,
            "title": resolved_title,
            "groups": groups,
            "url": f"https://pt.wikipedia.org/wiki/{quote(resolved_title.replace(' ', '_'))}",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "title": title, "groups": {}, "url": "", "error": str(exc)}


@st.cache_data(ttl=1800, show_spinner=False)
def probe_tse_sources() -> list[dict]:
    results: list[dict] = []
    headers = {"User-Agent": USER_AGENT, "Range": "bytes=0-0"}
    for name, source in TSE_DATASETS.items():
        try:
            response = requests.get(
                source["resource"], headers=headers, timeout=TIMEOUT, stream=True
            )
            fallback_used = False
            if response.status_code == 403 and source["resource"].startswith("https://cdn.tse.jus.br/"):
                response.close()
                fallback_url = "http://" + source["resource"].removeprefix("https://")
                response = requests.get(fallback_url, headers=headers, timeout=TIMEOUT, stream=True)
                fallback_used = True
            ok = response.status_code in {200, 206}
            status = f"HTTP {response.status_code}" + (" · fallback do CDN" if fallback_used else "")
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
