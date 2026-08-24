from __future__ import annotations

import json
from io import StringIO
from typing import Iterable, Mapping

import pandas as pd
import streamlit as st

from src.config import DATA_DIR


SCORE_COLUMNS = {
    "caiado": "caiado_score",
    "lula": "lula_score",
    "flavio": "flavio_score",
    "renan": "renan_score",
}

EVIDENCE_COLUMNS = {
    "caiado": "caiado_evidence",
    "lula": "lula_evidence",
    "flavio": "flavio_evidence",
    "renan": "renan_evidence",
}

WEIGHT_COMPONENTS = [
    "essentiality",
    "external_concentration",
    "replacement_time",
    "systemic_effect",
    "coercion_exposure",
]


@st.cache_data(show_spinner=False)
def load_candidates() -> list[dict]:
    payload = json.loads((DATA_DIR / "candidates.json").read_text(encoding="utf-8"))
    return payload["candidates"]


@st.cache_data(show_spinner=False)
def load_candidate_snapshot() -> dict:
    return json.loads((DATA_DIR / "candidates.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_benchmark() -> pd.DataFrame:
    frame = pd.read_csv(DATA_DIR / "benchmark.csv")
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


def candidate_map() -> dict[str, dict]:
    return {candidate["slug"]: candidate for candidate in load_candidates()}


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
    selected = list(slugs or SCORE_COLUMNS.keys())
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


def long_scores(benchmark: pd.DataFrame, slugs: Iterable[str]) -> pd.DataFrame:
    candidates = candidate_map()
    rows: list[dict] = []
    for slug in slugs:
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
    candidate = candidate_map()[slug]
    score = float(row[SCORE_COLUMNS[slug]])
    evidence = row[EVIDENCE_COLUMNS[slug]]
    note = (
        f"Nota {score:g}: {score_band(score)} neste critério. "
        f"Base classificada como “{str(evidence).lower()}”. "
        f"Leitura contextual: {candidate['summary']}"
    )
    return note, []


def candidate_factor_table(
    benchmark: pd.DataFrame,
    slug: str,
    custom_weights: Mapping[int, float] | None = None,
) -> pd.DataFrame:
    weights = normalize_weights(benchmark, custom_weights)
    rows: list[dict] = []
    for index, row in benchmark.iterrows():
        note, _ = factor_note(slug, row)
        score = float(row[SCORE_COLUMNS[slug]])
        weight = float(weights.iloc[index])
        rows.append(
            {
                "ID": int(row["id"]),
                "Bloco": row["block"],
                "Fator": row["factor"],
                "Peso": weight,
                "Nota": score,
                "Contribuição": round(score * weight, 2),
                "Evidência": row[EVIDENCE_COLUMNS[slug]],
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
