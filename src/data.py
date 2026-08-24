from __future__ import annotations

import json
from io import StringIO
from typing import Iterable, Mapping

import pandas as pd
import streamlit as st

from src.config import DATA_DIR


SCORE_COLUMNS = {
    "lula": "lula_score",
    "renan": "renan_score",
    "hertz": "hertz_score",
    "edmilson": "edmilson_score",
    "flavio": "flavio_score",
    "clariana": "clariana_score",
    "pablo": "pablo_score",
    "rui": "rui_score",
    "zema": "zema_score",
    "wilson": "wilson_score",
    "caiado": "caiado_score",
    "augusto": "augusto_score",
    "samara": "samara_score",
}

EVIDENCE_COLUMNS = {
    "lula": "lula_evidence",
    "renan": "renan_evidence",
    "hertz": "hertz_evidence",
    "edmilson": "edmilson_evidence",
    "flavio": "flavio_evidence",
    "clariana": "clariana_evidence",
    "pablo": "pablo_evidence",
    "rui": "rui_evidence",
    "zema": "zema_evidence",
    "wilson": "wilson_evidence",
    "caiado": "caiado_evidence",
    "augusto": "augusto_evidence",
    "samara": "samara_evidence",
}

WEIGHT_COMPONENTS = [
    "essentiality",
    "external_concentration",
    "replacement_time",
    "systemic_effect",
    "coercion_exposure",
]

BLOCK_TO_OVERVIEW = {
    "Defesa e território": "Defesa e território",
    "Diplomacia": "Diplomacia",
    "Abastecimento": "Abastecimento",
    "Economia produtiva": "Economia e finanças",
    "Finanças": "Economia e finanças",
    "Tecnologia": "Tecnologia",
    "Energia e recursos": "Energia e recursos",
    "Território e ambiente": "Território e ambiente",
    "Território e recursos": "Território e ambiente",
    "Infraestrutura": "Infraestrutura e indústria",
    "Política industrial": "Infraestrutura e indústria",
    "Resiliência": "Resiliência e instituições",
    "Instituições": "Resiliência e instituições",
}

# Correspondências temáticas de alta confiança entre a planilha original e a
# taxonomia revisada. A tabela original permanece preservada integralmente.
CURRENT_TO_ORIGINAL = {
    1: 1,
    2: 2,
    3: 4,
    5: 26,
    7: 20,
    8: 23,
    9: 31,
    10: 32,
    12: 3,
    13: 9,
    15: 7,
    16: 14,
    17: 15,
    18: 16,
    19: 36,
    20: 25,
    21: 17,
    22: 37,
    23: 18,
    24: 40,
    25: 19,
    26: 27,
    28: 28,
    30: 10,
    31: 11,
    32: 38,
    37: 9,
    38: 6,
    39: 24,
}


@st.cache_data(show_spinner=False)
def load_candidates() -> list[dict]:
    payload = json.loads((DATA_DIR / "candidates.json").read_text(encoding="utf-8"))
    return payload["candidates"]


@st.cache_data(show_spinner=False)
def load_candidate_snapshot() -> dict:
    return json.loads((DATA_DIR / "candidates.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_assessments() -> dict:
    return json.loads((DATA_DIR / "assessments.json").read_text(encoding="utf-8"))


def assessment_factor(slug: str, factor_id: int) -> dict | None:
    """Return the page-traceable assessment for a newly researched candidate."""
    candidate = load_assessments().get("candidates", {}).get(slug)
    if not candidate:
        return None
    scores = candidate.get("scores", [])
    if not 1 <= int(factor_id) <= len(scores):
        return None
    group = next(
        (entry for entry in candidate.get("groups", []) if int(factor_id) in entry.get("ids", [])),
        None,
    )
    score = float(scores[int(factor_id) - 1])
    if group:
        pages = [int(page) for page in group.get("pages", [])]
        evidence = group.get("evidence", "Explícita no plano" if pages else "Indireta ou não detalhada")
        support = group["support"]
        reservation = group.get("reservation", candidate["default_reservation"])
        confidence = group.get("confidence", "Média")
    else:
        pages = []
        evidence = "Sem posição localizada"
        support = "Não foi localizada posição específica no plano oficial para este fator."
        reservation = candidate["default_reservation"]
        confidence = "Baixa"
    return {
        "score": score,
        "evidence": evidence,
        "support": support,
        "reservation": reservation,
        "confidence": confidence,
        "pages": pages,
        "source_keys": [candidate["source_key"]],
    }


@st.cache_data(show_spinner=False)
def load_benchmark() -> pd.DataFrame:
    frame = pd.read_csv(DATA_DIR / "benchmark.csv")
    assessments = load_assessments().get("candidates", {})
    for slug, assessment in assessments.items():
        score_column = SCORE_COLUMNS[slug]
        evidence_column = EVIDENCE_COLUMNS[slug]
        if score_column not in frame:
            frame[score_column] = assessment["scores"]
        if evidence_column not in frame:
            frame[evidence_column] = [
                assessment_factor(slug, factor_id)["evidence"] for factor_id in frame["id"]
            ]
    numeric = ["id", "weight", *WEIGHT_COMPONENTS, *SCORE_COLUMNS.values()]
    frame[numeric] = frame[numeric].apply(pd.to_numeric)
    return frame


@st.cache_data(show_spinner=False)
def load_sources() -> list[dict]:
    payload = json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))
    return payload["sources"]


@st.cache_data(show_spinner=False)
def load_score_notes() -> dict:
    return json.loads((DATA_DIR / "score_notes.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_finance() -> pd.DataFrame:
    path = DATA_DIR / "finance_snapshot.csv"
    frame = pd.read_csv(path)
    if "amount" in frame:
        frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    return frame


@st.cache_data(show_spinner=False)
def load_tse_candidates() -> pd.DataFrame:
    """Load the compact presidential snapshot exactly as published by the TSE."""
    path = DATA_DIR / "tse_candidates_snapshot.csv"
    return pd.read_csv(path, dtype=str, keep_default_na=False)


@st.cache_data(show_spinner=False)
def load_original_basis() -> pd.DataFrame:
    raw = pd.read_csv(
        DATA_DIR / "original_basis.tsv",
        sep="\t",
        header=None,
        skiprows=1,
        dtype=str,
        encoding="utf-8",
    )
    raw = raw[raw[0].str.fullmatch(r"\d+", na=False)].copy()
    layouts = {
        "caiado": {"comment": 2, "plus": 3, "minus": 4, "balance": 5},
        "lula": {"comment": 10, "plus": 7, "minus": 8, "balance": 9},
        "flavio": {"comment": 15, "plus": 12, "minus": 13, "balance": 14},
        "renan": {"comment": 19, "plus": 16, "minus": 17, "balance": 18},
    }
    candidates = candidate_map()
    rows: list[dict] = []
    for record in raw.itertuples(index=False, name=None):
        for slug, layout in layouts.items():
            comment = str(record[layout["comment"]])
            positive, negative = comment, ""
            if "❌" in comment:
                positive, negative = comment.split("❌", 1)
            positive = positive.replace("✅", "").replace("-", " ").strip()
            negative = negative.replace("-", " ").strip()
            rows.append(
                {
                    "ID original": int(record[0]),
                    "Fator original": record[6],
                    "Peso original": float(record[1]),
                    "slug": slug,
                    "Candidato": candidates[slug]["ballot_name"],
                    "Prós": positive,
                    "Contras": negative,
                    "Pontos +": float(record[layout["plus"]]),
                    "Pontos −": float(record[layout["minus"]]),
                    "Saldo original": float(str(record[layout["balance"]]).replace(",", ".")),
                }
            )
    return pd.DataFrame(rows)


def candidate_map() -> dict[str, dict]:
    return {candidate["slug"]: candidate for candidate in load_candidates()}


def scored_slugs() -> list[str]:
    """Candidates with a completed, column-by-column editorial assessment."""
    available = candidate_map()
    return [slug for slug in SCORE_COLUMNS if slug in available]


def candidate_official_record(slug: str) -> dict:
    snapshot = load_tse_candidates()
    rows = snapshot[snapshot["candidate_slug"] == slug]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def normalize_weights(
    benchmark: pd.DataFrame,
    custom_weights: Mapping[int, float] | None = None,
) -> pd.Series:
    weights = benchmark.set_index("id")["weight"].astype(float).copy()
    if custom_weights:
        for factor_id, value in custom_weights.items():
            if int(factor_id) in weights.index:
                weights.loc[int(factor_id)] = max(0.0, float(value))
    return benchmark["id"].map(weights).astype(float)


def weighted_scores(
    benchmark: pd.DataFrame,
    slugs: Iterable[str] | None = None,
    custom_weights: Mapping[int, float] | None = None,
) -> pd.DataFrame:
    requested = scored_slugs() if slugs is None else list(slugs)
    selected = [slug for slug in requested if slug in SCORE_COLUMNS]
    weights = normalize_weights(benchmark, custom_weights)
    denominator = weights.sum()
    rows: list[dict] = []
    candidates = candidate_map()
    for slug in selected:
        values = benchmark[SCORE_COLUMNS[slug]].astype(float)
        score = float((values * weights).sum() / denominator) if denominator else float("nan")
        rows.append(
            {
                "slug": slug,
                "candidate": candidates[slug]["ballot_name"],
                "party": candidates[slug]["party"],
                "score": round(score, 2),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["slug", "candidate", "party", "score"])
    return pd.DataFrame(rows).sort_values("score", ascending=False, ignore_index=True)


def dimension_scores(
    benchmark: pd.DataFrame,
    slugs: Iterable[str],
    custom_weights: Mapping[int, float] | None = None,
) -> pd.DataFrame:
    weights = normalize_weights(benchmark, custom_weights)
    working = benchmark[["block", "id"]].copy()
    working["_weight"] = weights
    candidates = candidate_map()
    result: list[dict] = []
    for slug in slugs:
        if slug not in SCORE_COLUMNS:
            continue
        working["_score"] = benchmark[SCORE_COLUMNS[slug]].astype(float)
        for block, group in working.groupby("block", sort=False):
            denom = group["_weight"].sum()
            value = (group["_score"] * group["_weight"]).sum() / denom if denom else float("nan")
            result.append(
                {
                    "slug": slug,
                    "candidate": candidates[slug]["ballot_name"],
                    "block": block,
                    "score": round(float(value), 2),
                }
            )
    return pd.DataFrame(result)


def overview_scores(
    benchmark: pd.DataFrame,
    slugs: Iterable[str],
    custom_weights: Mapping[int, float] | None = None,
) -> pd.DataFrame:
    """Aggregate all benchmark rows into nine readable radar axes."""
    weights = normalize_weights(benchmark, custom_weights)
    working = benchmark[["block", "id"]].copy()
    working["overview"] = working["block"].map(BLOCK_TO_OVERVIEW)
    if working["overview"].isna().any():
        missing = sorted(working.loc[working["overview"].isna(), "block"].unique())
        raise ValueError(f"Blocos sem dimensão geral: {missing}")
    working["_weight"] = weights
    candidates = candidate_map()
    result: list[dict] = []
    for slug in slugs:
        if slug not in SCORE_COLUMNS:
            continue
        working["_score"] = benchmark[SCORE_COLUMNS[slug]].astype(float)
        for overview, group in working.groupby("overview", sort=False):
            denominator = group["_weight"].sum()
            value = (group["_score"] * group["_weight"]).sum() / denominator if denominator else float("nan")
            result.append(
                {
                    "slug": slug,
                    "candidate": candidates[slug]["ballot_name"],
                    "block": overview,
                    "score": round(float(value), 2),
                    "factor_count": int(len(group)),
                    "weight_sum": float(denominator),
                }
            )
    return pd.DataFrame(result)


def long_scores(benchmark: pd.DataFrame, slugs: Iterable[str]) -> pd.DataFrame:
    candidates = candidate_map()
    rows: list[dict] = []
    for slug in slugs:
        if slug not in SCORE_COLUMNS:
            continue
        for row in benchmark.itertuples(index=False):
            rows.append(
                {
                    "slug": slug,
                    "candidate": candidates[slug]["ballot_name"],
                    "party": candidates[slug]["party"],
                    "id": row.id,
                    "block": row.block,
                    "factor": row.factor,
                    "weight": row.weight,
                    "score": getattr(row, SCORE_COLUMNS[slug]),
                    "evidence": getattr(row, EVIDENCE_COLUMNS[slug]),
                }
            )
    return pd.DataFrame(rows)


def score_band(score: float) -> str:
    if score >= 9:
        return "forte ganho de autonomia"
    if score >= 7:
        return "ganho relevante de autonomia"
    if score >= 6:
        return "ganho limitado ou com ressalvas"
    if score >= 5:
        return "neutro, ambíguo ou evidência insuficiente"
    if score >= 3:
        return "dependência relevante"
    if score >= 1:
        return "dependência grave"
    return "subordinação estrutural explícita"


def factor_note(slug: str, row: pd.Series) -> tuple[str, list[str]]:
    overrides = load_score_notes().get(slug, {}).get(str(int(row["id"])))
    if overrides:
        return overrides["note"], overrides.get("source_keys", [])
    assessment = assessment_factor(slug, int(row["id"]))
    if assessment:
        note = (
            f"Nota {assessment['score']:g}: {score_band(assessment['score'])}. "
            f"Base: {assessment['support']} Ressalva: {assessment['reservation']}"
        )
        return note, assessment["source_keys"]
    candidate = candidate_map()[slug]
    score = float(row[SCORE_COLUMNS[slug]])
    evidence = row[EVIDENCE_COLUMNS[slug]]
    note = (
        f"Nota {score:g}: {score_band(score)} neste critério. "
        f"Base classificada como “{str(evidence).lower()}”. "
        f"Leitura contextual: {candidate['summary']}"
    )
    return note, []


def factor_sources(slug: str, source_keys: Iterable[str]) -> list[dict]:
    """Return the official sources used by a revised factor assessment."""
    keys = list(source_keys)
    if keys:
        registry = {source["key"]: source for source in load_sources()}
        return [registry[key] for key in keys if key in registry]
    candidate = candidate_map()[slug]
    return [
        {
            "key": f"plan_{slug}",
            "title": f"Plano oficial de {candidate['ballot_name']} no TSE",
            "publisher": "Tribunal Superior Eleitoral",
            "type": "Proposta de governo",
            "url": candidate["plan_url"],
            "use": "Fonte geral da avaliação revisada",
        }
    ]


def original_candidate_table_with_summary(slug: str) -> pd.DataFrame:
    """Format the supplied base and keep its weighted balance as the final row."""
    source = load_original_basis()
    table = source[source["slug"] == slug].rename(
        columns={
            "Fator original": "Fator",
            "Peso original": "Peso",
            "Pontos +": "Nota prós",
            "Pontos −": "Nota contras",
            "Saldo original": "Saldo do fator",
        }
    )
    table = table[
        ["Fator", "Peso", "Prós", "Contras", "Nota prós", "Nota contras", "Saldo do fator"]
    ].copy()
    table["Fonte(s)"] = "Não informada na entrada original"

    denominator = float(table["Peso"].sum())
    weighted_plus = float((table["Nota prós"] * table["Peso"]).sum() / denominator) if denominator else float("nan")
    weighted_minus = float((table["Nota contras"] * table["Peso"]).sum() / denominator) if denominator else float("nan")
    weighted_balance = float((table["Saldo do fator"] * table["Peso"]).sum() / denominator) if denominator else float("nan")
    summary = pd.DataFrame(
        [
            {
                "Fator": "MÉDIA PONDERADA",
                "Peso": denominator,
                "Prós": "Σ(nota prós × peso) ÷ Σ(pesos)",
                "Contras": "Σ(nota contras × peso) ÷ Σ(pesos)",
                "Nota prós": round(weighted_plus, 2),
                "Nota contras": round(weighted_minus, 2),
                "Saldo do fator": round(weighted_balance, 2),
                "Fonte(s)": "Cálculo a partir das 40 linhas anteriores",
            }
        ]
    )
    return pd.concat([table, summary], ignore_index=True)


def candidate_factor_table(
    benchmark: pd.DataFrame,
    slug: str,
    custom_weights: Mapping[int, float] | None = None,
) -> pd.DataFrame:
    weights = normalize_weights(benchmark, custom_weights)
    original = load_original_basis()
    original_lookup = original.set_index(["slug", "ID original"])
    rows: list[dict] = []
    for index, row in benchmark.iterrows():
        note, source_keys = factor_note(slug, row)
        sources = factor_sources(slug, source_keys)
        score = float(row[SCORE_COLUMNS[slug]])
        weight = float(weights.iloc[index])
        original_id = CURRENT_TO_ORIGINAL.get(int(row["id"]))
        base = None
        if original_id and (slug, original_id) in original_lookup.index:
            base = original_lookup.loc[(slug, original_id)]
        assessment = assessment_factor(slug, int(row["id"]))
        pros = assessment["support"] if assessment else (
            base["Prós"] if base is not None else "Sem correspondência direta na tabela original"
        )
        cons = assessment["reservation"] if assessment else (
            base["Contras"] if base is not None else "Exige justificativa específica na revisão"
        )
        page_suffix = ""
        if assessment and assessment["pages"]:
            page_suffix = " — p. " + ", ".join(str(page) for page in assessment["pages"])
        rows.append(
            {
                "ID": int(row["id"]),
                "Bloco": row["block"],
                "Fator": row["factor"],
                "Peso": weight,
                "Nota": score,
                "Contribuição": round(score * weight, 2),
                "Evidência": row[EVIDENCE_COLUMNS[slug]],
                "Prós": pros,
                "Contras": cons,
                "Nota prós": score,
                "Nota contras": 10.0 - score,
                "Saldo do fator": 2.0 * score - 10.0,
                "Confiança": assessment["confidence"] if assessment else "Base legada",
                "Fonte(s)": (
                    "; ".join(source["title"] for source in sources) + page_suffix
                ),
                "URL da fonte": sources[0]["url"] if sources else "",
                "Fundamento": note,
            }
        )
    return pd.DataFrame(rows)


def candidate_table_with_summary(
    benchmark: pd.DataFrame,
    slug: str,
    custom_weights: Mapping[int, float] | None = None,
) -> pd.DataFrame:
    table = candidate_factor_table(benchmark, slug, custom_weights)
    denominator = table["Peso"].sum()
    average = table["Contribuição"].sum() / denominator if denominator else float("nan")
    weighted_plus = (table["Nota prós"] * table["Peso"]).sum() / denominator if denominator else float("nan")
    weighted_minus = (table["Nota contras"] * table["Peso"]).sum() / denominator if denominator else float("nan")
    weighted_balance = (table["Saldo do fator"] * table["Peso"]).sum() / denominator if denominator else float("nan")
    summary = pd.DataFrame(
        [
            {
                "ID": "",
                "Bloco": "RESUMO",
                "Fator": "MÉDIA PONDERADA",
                "Peso": denominator,
                "Nota": round(float(average), 2),
                "Contribuição": round(float(table["Contribuição"].sum()), 2),
                "Evidência": "Cálculo",
                "Prós": "Σ(nota prós × peso) ÷ Σ(pesos)",
                "Contras": "Σ(nota contras × peso) ÷ Σ(pesos)",
                "Nota prós": round(float(weighted_plus), 2),
                "Nota contras": round(float(weighted_minus), 2),
                "Saldo do fator": round(float(weighted_balance), 2),
                "Confiança": "—",
                "Fonte(s)": "Cálculo a partir das linhas anteriores",
                "URL da fonte": "",
                "Fundamento": "Σ(nota × peso) ÷ Σ(pesos)",
            }
        ]
    )
    output = pd.concat([table, summary], ignore_index=True)
    output["ID"] = output["ID"].astype(str).str.replace(r"\.0$", "", regex=True)
    return output


def comparison_table_with_summary(
    benchmark: pd.DataFrame,
    slugs: Iterable[str],
    custom_weights: Mapping[int, float] | None = None,
) -> pd.DataFrame:
    selected = list(slugs)
    weights = normalize_weights(benchmark, custom_weights)
    table = benchmark[["id", "block", "factor"]].copy()
    table["Peso"] = weights
    candidates = candidate_map()
    for slug in selected:
        table[candidates[slug]["ballot_name"]] = benchmark[SCORE_COLUMNS[slug]].astype(float)
    table = table.rename(columns={"id": "ID", "block": "Bloco", "factor": "Fator"})
    averages = weighted_scores(benchmark, selected, custom_weights).set_index("slug")["score"]
    summary: dict = {"ID": "", "Bloco": "RESUMO", "Fator": "MÉDIA PONDERADA", "Peso": weights.sum()}
    for slug in selected:
        summary[candidates[slug]["ballot_name"]] = float(averages.loc[slug])
    output = pd.concat([table, pd.DataFrame([summary])], ignore_index=True)
    output["ID"] = output["ID"].astype(str).str.replace(r"\.0$", "", regex=True)
    return output


def export_payload(
    benchmark: pd.DataFrame,
    slugs: Iterable[str],
    custom_weights: Mapping[int, float] | None = None,
) -> dict:
    selected = list(slugs)
    weights = normalize_weights(benchmark, custom_weights)
    ranking = weighted_scores(benchmark, selected, custom_weights).to_dict("records")
    assessment_tables = {
        slug: candidate_factor_table(benchmark, slug, custom_weights).set_index("ID")
        for slug in selected
    }
    factors = benchmark[
        ["id", "block", "factor", "definition", *WEIGHT_COMPONENTS]
    ].copy()
    factors["weight"] = weights
    factor_records: list[dict] = []
    for _, row in factors.iterrows():
        record = row.to_dict()
        record["scores"] = {
            slug: float(benchmark.loc[benchmark["id"] == row["id"], SCORE_COLUMNS[slug]].iloc[0])
            for slug in selected
        }
        record["assessments"] = {}
        for slug in selected:
            assessment = assessment_tables[slug].loc[int(row["id"])]
            record["assessments"][slug] = {
                "score": float(assessment["Nota"]),
                "pros": assessment["Prós"],
                "cons": assessment["Contras"],
                "positive_note": float(assessment["Nota prós"]),
                "negative_note": float(assessment["Nota contras"]),
                "factor_balance": float(assessment["Saldo do fator"]),
                "evidence": assessment["Evidência"],
                "confidence": assessment["Confiança"],
                "sources": assessment["Fonte(s)"],
                "source_url": assessment["URL da fonte"],
                "rationale": assessment["Fundamento"],
            }
        factor_records.append(record)
    return {
        "title": "Brasil Com Censo — Benchmark de Candidatos",
        "election": {"year": 2026, "office": "Presidência", "district": "Brasil"},
        "formula": "sum(score * weight) / sum(weight)",
        "ranking": ranking,
        "factors": factor_records,
    }


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def csv_bytes(frame: pd.DataFrame) -> bytes:
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8-sig")
