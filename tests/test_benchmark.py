from __future__ import annotations

import math

from src.data import (
    candidate_table_with_summary,
    load_benchmark,
    original_candidate_table_with_summary,
    weighted_scores,
)


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
