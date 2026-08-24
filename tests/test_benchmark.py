from __future__ import annotations

import math

from src.data import (
    EVIDENCE_COLUMNS,
    SCORE_COLUMNS,
    candidate_table_with_summary,
    export_payload,
    load_assessments,
    load_benchmark,
    load_candidates,
    load_tse_candidates,
    original_candidate_table_with_summary,
    overview_scores,
    scored_slugs,
    weighted_scores,
)
from src.radar import radar_options


def test_lula_us_score_is_revised_to_nine():
    benchmark = load_benchmark()
    row = benchmark.loc[benchmark["factor"] == "Relação com os Estados Unidos"].iloc[0]
    assert row["lula_score"] == 9


def test_weighted_score_is_calculated_from_rows():
    benchmark = load_benchmark()
    ranking = weighted_scores(benchmark, ["lula"])
    expected = (benchmark["lula_score"] * benchmark["weight"]).sum() / benchmark["weight"].sum()
    assert math.isclose(ranking.iloc[0]["score"], round(expected, 2))


def test_summary_is_last_row_and_matches_ranking():
    benchmark = load_benchmark()
    table = candidate_table_with_summary(benchmark, "flavio")
    ranking = weighted_scores(benchmark, ["flavio"])
    assert table.iloc[-1]["Fator"] == "MÉDIA PONDERADA"
    assert table.iloc[-1]["Nota"] == ranking.iloc[0]["score"]


def test_custom_weights_change_result_without_changing_base_data():
    benchmark = load_benchmark()
    original = benchmark["weight"].copy()
    custom = {factor_id: 0 for factor_id in benchmark["id"]}
    custom[8] = 5
    ranking = weighted_scores(benchmark, ["lula", "flavio"], custom)
    assert ranking.set_index("slug").loc["lula", "score"] == 9
    assert ranking.set_index("slug").loc["flavio", "score"] == 3
    assert benchmark["weight"].equals(original)


def test_original_candidate_table_has_requested_columns_and_weighted_summary():
    table = original_candidate_table_with_summary("lula")
    assert table.columns.tolist() == [
        "Fator",
        "Peso",
        "Prós",
        "Contras",
        "Nota prós",
        "Nota contras",
        "Saldo do fator",
        "Fonte(s)",
    ]
    assert len(table) == 41
    assert table.iloc[-1]["Fator"] == "MÉDIA PONDERADA"
    rows = table.iloc[:-1]
    expected = round(float((rows["Saldo do fator"] * rows["Peso"]).sum() / rows["Peso"].sum()), 2)
    assert table.iloc[-1]["Saldo do fator"] == expected


def test_revised_table_exposes_a_clickable_primary_source():
    table = candidate_table_with_summary(load_benchmark(), "lula")
    assert "URL da fonte" in table.columns
    assert table.iloc[:-1]["URL da fonte"].str.startswith("https://").all()


def test_overview_radar_represents_all_forty_factors():
    benchmark = load_benchmark()
    overview = overview_scores(benchmark, ["lula", "caiado"])
    assert overview["block"].nunique() == 9
    for slug, rows in overview.groupby("slug"):
        assert rows["factor_count"].sum() == len(benchmark) == 40
        assert rows["score"].between(0, 10).all(), slug


def test_echarts_overview_radar_keeps_nine_axes_and_filled_series():
    benchmark = load_benchmark()
    overview = overview_scores(benchmark, ["lula", "caiado"])
    options = radar_options(overview, "Visão geral")
    assert len(options["radar"]["indicator"]) == 9
    assert len(options["series"][0]["data"]) == 2
    assert all(len(series["value"]) == 9 for series in options["series"][0]["data"])
    assert all(series["areaStyle"]["opacity"] > 0 for series in options["series"][0]["data"])
    assert options["toolbox"]["feature"]["saveAsImage"]["title"] == "Baixar PNG"


def test_official_tse_snapshot_contains_all_thirteen_presidential_requests():
    candidates = load_candidates()
    snapshot = load_tse_candidates()
    assert len(candidates) == 13
    assert len(snapshot) == 13
    assert {candidate["slug"] for candidate in candidates} == set(snapshot["candidate_slug"])
    assert {13, 14, 16, 21, 22, 27, 28, 29, 30, 35, 55, 70, 80} == {
        int(candidate["number"]) for candidate in candidates
    }


def test_four_requested_topics_are_exclusive_factors_not_a_special_chart():
    benchmark = load_benchmark()
    factors = set(benchmark["factor"])
    assert {"Indústria nacional", "Transição energética", "Terras raras e minerais críticos", "Ferrovias"} <= factors
    assert "Transição e segurança energética" not in factors
    assert "Portos, ferrovias, rodovias e cabotagem" not in factors


def test_all_thirteen_candidates_have_complete_forty_factor_assessments():
    benchmark = load_benchmark()
    assert len(scored_slugs()) == 13
    ranking = weighted_scores(benchmark).set_index("slug")
    for slug in scored_slugs():
        assert len(benchmark[SCORE_COLUMNS[slug]]) == 40
        assert benchmark[SCORE_COLUMNS[slug]].between(0, 10).all(), slug
        assert benchmark[EVIDENCE_COLUMNS[slug]].astype(str).str.strip().ne("").all(), slug
        table = candidate_table_with_summary(benchmark, slug)
        rows, summary = table.iloc[:-1], table.iloc[-1]
        assert summary["Nota"] == ranking.loc[slug, "score"], slug
        expected_balance = round(
            float((rows["Saldo do fator"] * rows["Peso"]).sum() / rows["Peso"].sum()), 2
        )
        assert summary["Saldo do fator"] == expected_balance, slug


def test_new_non_neutral_scores_are_traceable_to_pages_and_sources():
    assessments = load_assessments()["candidates"]
    for slug, candidate in assessments.items():
        covered = {
            int(factor_id)
            for group in candidate["groups"]
            if group["pages"] and candidate.get("source_key")
            for factor_id in group["ids"]
        }
        non_neutral = {
            factor_id
            for factor_id, score in enumerate(candidate["scores"], start=1)
            if float(score) != 5
        }
        assert non_neutral <= covered, slug


def test_pablo_stays_neutral_when_official_plan_is_not_in_tse_bundle():
    benchmark = load_benchmark()
    assert set(benchmark["pablo_score"]) == {5}
    assert set(benchmark["pablo_evidence"]) == {"Sem posição localizada"}


def test_export_contains_auditable_pros_cons_sources_and_balance():
    payload = export_payload(load_benchmark(), ["hertz", "zema"])
    assessment = payload["factors"][0]["assessments"]["hertz"]
    assert {
        "score",
        "pros",
        "cons",
        "positive_note",
        "negative_note",
        "factor_balance",
        "evidence",
        "confidence",
        "sources",
        "source_url",
        "rationale",
    } <= assessment.keys()
    assert assessment["source_url"].startswith("https://")
