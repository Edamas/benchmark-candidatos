"""Refresh compact, candidate-level snapshots from official TSE ZIP files.

The script fails loudly when the source cannot be reached. Existing snapshots are
never erased on failure, so the app cannot turn a network error into a factual zero.
"""
from __future__ import annotations

import argparse
from datetime import date
import io
import json
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
USER_AGENT = "BrasilComCenso/0.1 (atualizador de dados publicos)"
URLS = {
    "candidates": "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip",
    "finance": "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2026.zip",
}


def normalized(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.upper().split())


def download_zip(url: str, max_bytes: int = 700_000_000) -> zipfile.ZipFile:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=90, stream=True)
    if response.status_code == 403 and url.startswith("https://cdn.tse.jus.br/"):
        response.close()
        fallback = "http://" + url.removeprefix("https://")
        response = requests.get(fallback, headers={"User-Agent": USER_AGENT}, timeout=90, stream=True)
    response.raise_for_status()
    body = io.BytesIO()
    for chunk in response.iter_content(1024 * 1024):
        body.write(chunk)
        if body.tell() > max_bytes:
            raise RuntimeError(f"Arquivo excede o limite de segurança de {max_bytes:,} bytes")
    body.seek(0)
    return zipfile.ZipFile(body)


def read_csv_member(archive: zipfile.ZipFile, member: str, **kwargs) -> pd.DataFrame:
    with archive.open(member) as source:
        return pd.read_csv(source, sep=";", encoding="latin-1", low_memory=False, **kwargs)


def candidate_member(archive: zipfile.ZipFile) -> str:
    csvs = [name for name in archive.namelist() if name.lower().endswith(".csv")]
    preferred = [name for name in csvs if "BRASIL" in normalized(name)]
    return (preferred or csvs)[0]


def refresh_candidates() -> tuple[pd.DataFrame, dict[str, str]]:
    archive = download_zip(URLS["candidates"])
    frame = read_csv_member(archive, candidate_member(archive))
    office = frame.get("DS_CARGO", pd.Series("", index=frame.index)).map(normalized)
    frame = frame[office == "PRESIDENTE"].copy()
    if frame.empty:
        raise RuntimeError("O recurso do TSE não retornou candidaturas à Presidência")

    seed = json.loads((DATA_DIR / "candidates.json").read_text(encoding="utf-8"))["candidates"]
    lookup: dict[str, str] = {}
    for candidate in seed:
        lookup[normalized(candidate["full_name"])] = candidate["slug"]
        lookup[normalized(candidate["ballot_name"])] = candidate["slug"]

    def find_slug(row: pd.Series) -> str:
        for column in ("NM_CANDIDATO", "NM_URNA_CANDIDATO"):
            name = normalized(row.get(column, ""))
            if name in lookup:
                return lookup[name]
        return ""

    frame["candidate_slug"] = frame.apply(find_slug, axis=1)
    selected = frame[frame["candidate_slug"] != ""].copy()
    columns = [
        "candidate_slug",
        "SQ_CANDIDATO",
        "NM_CANDIDATO",
        "NM_URNA_CANDIDATO",
        "NR_CANDIDATO",
        "SG_PARTIDO",
        "DS_SITUACAO_CANDIDATURA",
        "DS_SITUACAO_CANDIDATO_URNA",
        "DS_GRAU_INSTRUCAO",
        "DS_OCUPACAO",
        "DS_COR_RACA",
        "DS_GENERO",
        "DT_NASCIMENTO",
        "SG_UF_NASCIMENTO",
        "NM_COLIGACAO",
    ]
    selected = selected[[column for column in columns if column in selected.columns]]
    selected["snapshot_date"] = date.today().isoformat()
    selected["source_url"] = URLS["candidates"]
    selected.to_csv(DATA_DIR / "tse_candidates_snapshot.csv", index=False, encoding="utf-8-sig")
    sequence_to_slug = {
        str(row.SQ_CANDIDATO): row.candidate_slug
        for row in selected[["SQ_CANDIDATO", "candidate_slug"]].itertuples(index=False)
    }
    return selected, sequence_to_slug


def parse_brazilian_amount(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def refresh_finance(sequence_to_slug: dict[str, str]) -> pd.DataFrame:
    archive = download_zip(URLS["finance"])
    members = [
        name
        for name in archive.namelist()
        if name.lower().endswith(".csv") and "RECEITA" in normalized(name)
    ]
    preferred = [name for name in members if "BRASIL" in normalized(name)] or members
    rows: list[pd.DataFrame] = []
    for member in preferred:
        with archive.open(member) as source:
            for chunk in pd.read_csv(
                source,
                sep=";",
                encoding="latin-1",
                low_memory=False,
                chunksize=100_000,
            ):
                if "SQ_CANDIDATO" not in chunk:
                    continue
                chunk["candidate_slug"] = chunk["SQ_CANDIDATO"].astype(str).map(sequence_to_slug)
                chunk = chunk[chunk["candidate_slug"].notna()].copy()
                if not chunk.empty:
                    rows.append(chunk)
    if not rows:
        return pd.DataFrame(columns=["candidate_slug", "donor_name", "donor_type", "amount", "date", "source_url"])

    frame = pd.concat(rows, ignore_index=True)
    donor_name = next((name for name in ("NM_DOADOR_RFB", "NM_DOADOR") if name in frame), None)
    donor_type = next((name for name in ("DS_ORIGEM_RECEITA", "DS_ESPECIE_RECEITA") if name in frame), None)
    amount = next((name for name in ("VR_RECEITA", "VR_RECEITA_DOACAO") if name in frame), None)
    date = next((name for name in ("DT_RECEITA", "DT_GERACAO") if name in frame), None)
    compact = pd.DataFrame(
        {
            "candidate_slug": frame["candidate_slug"],
            "donor_name": frame[donor_name] if donor_name else "Não informado",
            "donor_type": frame[donor_type] if donor_type else "Não informado",
            "amount": parse_brazilian_amount(frame[amount]) if amount else pd.NA,
            "date": frame[date] if date else "",
            "source_url": URLS["finance"],
        }
    )
    compact.to_csv(DATA_DIR / "finance_snapshot.csv", index=False, encoding="utf-8-sig")
    return compact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-finance", action="store_true")
    args = parser.parse_args()
    _, sequence_to_slug = refresh_candidates()
    if not args.skip_finance:
        refresh_finance(sequence_to_slug)
    print("Snapshots do TSE atualizados com sucesso.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Falha ao atualizar o TSE: {exc}", file=sys.stderr)
        raise
