from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import CANDIDATE_COLORS


PAPER = "rgba(0,0,0,0)"
GRID = "rgba(67,88,78,.16)"
INK = "#24362E"
MUTED = "#5B6C64"

CANDIDATE_SYMBOLS = {
    "lula": "circle",
    "caiado": "diamond",
    "flavio": "square",
    "renan": "triangle-up",
}

RADAR_LABELS = {
    "Defesa e território": "Defesa e<br>território",
    "Diplomacia": "Diplomacia",
    "Abastecimento": "Abasteci<br>mento",
    "Economia e finanças": "Economia e<br>finanças",
    "Economia produtiva": "Economia<br>produtiva",
    "Finanças": "Finanças",
    "Tecnologia": "Tecnologia",
    "Energia e recursos": "Energia e<br>recursos",
    "Território e ambiente": "Território e<br>ambiente",
    "Infraestrutura e indústria": "Infraestrutura<br>e indústria",
    "Infraestrutura": "Infraestrutura",
    "Política industrial": "Política<br>industrial",
    "Resiliência e instituições": "Resiliência e<br>instituições",
    "Resiliência": "Resiliência",
    "Território e recursos": "Território e<br>recursos",
    "Instituições": "Instituições",
}


def _rgba(hex_color: str, alpha: float) -> str:
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return f"rgba({red},{green},{blue},{alpha})"


def _radar_layout(fig: go.Figure, *, title: str, series_count: int, height: int = 580) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0, "y": 0.98, "font": {"size": 18}},
        polar={
            "bgcolor": "rgba(255,255,255,.34)",
            "domain": {"x": [0.04, 0.96], "y": [0.04, 0.96]},
            "radialaxis": {
                "range": [0, 10],
                "tickvals": [2, 4, 6, 8, 10],
                "angle": 45,
                "gridcolor": "rgba(67,88,78,.18)",
                "linecolor": "rgba(67,88,78,.22)",
                "tickfont": {"color": MUTED, "size": 10},
                "ticks": "",
            },
            "angularaxis": {
                "rotation": 90,
                "direction": "clockwise",
                "gridcolor": "rgba(67,88,78,.13)",
                "linecolor": "rgba(67,88,78,.30)",
                "tickfont": {"size": 11, "color": INK},
            },
        },
    )
    fig = _layout(fig, height=height, margin={"l": 66, "r": 66, "t": 76, "b": 92})
    fig.update_layout(
        showlegend=series_count > 1,
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.10,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 12},
        },
    )
    return fig


def _layout(fig: go.Figure, *, height: int = 430, margin: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        font={"family": "Inter, Arial, sans-serif", "color": INK, "size": 13},
        margin=margin or {"l": 36, "r": 22, "t": 62, "b": 42},
        hoverlabel={"bgcolor": "#173E35", "font_color": "#FFFFFF"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
    )
    return fig


def ranking_chart(ranking: pd.DataFrame, title: str = "Índice ponderado de soberania") -> go.Figure:
    frame = ranking.sort_values("score", ascending=True)
    colors = [CANDIDATE_COLORS.get(slug, "#0B6654") for slug in frame["slug"]]
    fig = go.Figure(
        go.Bar(
            x=frame["score"],
            y=frame["candidate"],
            orientation="h",
            marker={"color": colors, "line": {"width": 0}},
            text=[f"{value:.2f}" for value in frame["score"]],
            textposition="outside",
            customdata=frame[["party"]],
            hovertemplate="<b>%{y}</b> · %{customdata[0]}<br>Índice: %{x:.2f}/10<extra></extra>",
        )
    )
    fig.update_layout(title={"text": title, "x": 0})
    fig.update_xaxes(title="Média ponderada (0–10)", range=[0, 10.65], gridcolor=GRID, dtick=2)
    fig.update_yaxes(title="", automargin=True)
    return _layout(fig, height=390, margin={"l": 18, "r": 50, "t": 60, "b": 46})


def dimension_profile_chart(dimensions: pd.DataFrame, title: str = "Perfil por dimensão") -> go.Figure:
    fig = go.Figure()
    blocks = dimensions["block"].drop_duplicates().tolist()
    series_count = dimensions["slug"].nunique()
    for slug, group in dimensions.groupby("slug", sort=False):
        ordered = group.set_index("block").reindex(blocks).reset_index()
        axis_labels = ordered["block"].map(RADAR_LABELS).fillna(ordered["block"])
        factor_count = ordered["factor_count"] if "factor_count" in ordered else pd.Series([pd.NA] * len(ordered))
        hover = (
            "<b>%{customdata[0]}</b><br>%{r:.2f}/10"
            "<br>%{customdata[1]} fatores agregados<extra>%{fullData.name}</extra>"
            if "factor_count" in ordered
            else "<b>%{customdata[0]}</b><br>%{r:.2f}/10<extra>%{fullData.name}</extra>"
        )
        color = CANDIDATE_COLORS.get(slug, "#0B6654")
        fig.add_trace(
            go.Scatterpolar(
                r=ordered["score"],
                theta=axis_labels,
                name=ordered["candidate"].iloc[0],
                mode="lines+markers",
                line={"color": color, "width": 3},
                marker={
                    "size": 7,
                    "symbol": CANDIDATE_SYMBOLS.get(slug, "circle"),
                    "color": color,
                    "line": {"color": "#F6F7F2", "width": 1.2},
                },
                fill="toself",
                fillcolor=_rgba(color, 0.20 if series_count == 1 else 0.13),
                customdata=pd.DataFrame({"block": ordered["block"], "factor_count": factor_count}),
                hovertemplate=hover,
            )
        )
    return _radar_layout(fig, title=title, series_count=series_count, height=590)


def factor_radar_chart(
    long_frame: pd.DataFrame,
    factor_ids: list[int],
    title: str = "Radar de fatores selecionados",
) -> go.Figure:
    frame = long_frame[long_frame["id"].isin(factor_ids)].copy()
    order = {factor_id: position for position, factor_id in enumerate(factor_ids)}
    frame["_order"] = frame["id"].map(order)
    frame["axis_label"] = frame["factor"].map(lambda value: str(value).replace(" ", "<br>", 1))
    fig = go.Figure()
    series_count = frame["slug"].nunique()
    for slug, group in frame.sort_values("_order").groupby("slug", sort=False):
        color = CANDIDATE_COLORS.get(slug, "#0B6654")
        fig.add_trace(
            go.Scatterpolar(
                r=group["score"],
                theta=group["axis_label"],
                name=group["candidate"].iloc[0],
                mode="lines+markers",
                line={"color": color, "width": 3},
                marker={
                    "size": 8,
                    "symbol": CANDIDATE_SYMBOLS.get(slug, "circle"),
                    "color": color,
                    "line": {"color": "#F6F7F2", "width": 1.2},
                },
                fill="toself",
                fillcolor=_rgba(color, 0.22 if series_count == 1 else 0.14),
                customdata=group[["factor"]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{r:.1f}/10<extra>%{fullData.name}</extra>",
            )
        )
    return _radar_layout(fig, title=title, series_count=series_count, height=570)


def score_heatmap(long_frame: pd.DataFrame, title: str = "Notas fator a fator") -> go.Figure:
    pivot = long_frame.pivot(index="factor", columns="candidate", values="score")
    id_map = long_frame.drop_duplicates("factor").set_index("factor")["id"]
    pivot = pivot.loc[id_map.sort_values().index]
    fig = px.imshow(
        pivot,
        zmin=0,
        zmax=10,
        aspect="auto",
        color_continuous_scale=[
            [0, "#71323B"],
            [0.45, "#D7835B"],
            [0.5, "#E8D7A5"],
            [0.75, "#58A27F"],
            [1, "#075344"],
        ],
        labels={"x": "Candidato", "y": "Fator", "color": "Nota"},
        text_auto=".0f",
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.0f}/10<extra></extra>",
        xgap=2,
        ygap=1,
    )
    fig.update_layout(title={"text": title, "x": 0}, coloraxis_colorbar={"title": "Nota", "len": 0.55})
    fig.update_xaxes(side="top")
    fig.update_yaxes(automargin=True, tickfont={"size": 10})
    return _layout(fig, height=max(620, 20 * len(pivot) + 150), margin={"l": 255, "r": 35, "t": 95, "b": 20})


def contribution_chart(factor_table: pd.DataFrame, candidate_name: str) -> go.Figure:
    frame = factor_table.assign(Impacto=lambda value: value["Contribuição"])
    frame = frame.sort_values("Impacto", ascending=True).tail(12)
    fig = go.Figure(
        go.Bar(
            x=frame["Impacto"],
            y=frame["Fator"],
            orientation="h",
            marker={"color": "#0B6654", "line": {"width": 0}},
            customdata=frame[["Nota", "Peso"]],
            hovertemplate="<b>%{y}</b><br>Nota %{customdata[0]:.0f} × peso %{customdata[1]:.0f} = %{x:.0f}<extra></extra>",
        )
    )
    fig.update_layout(title={"text": f"Maiores contribuições · {candidate_name}", "x": 0})
    fig.update_xaxes(title="Nota × peso", gridcolor=GRID)
    fig.update_yaxes(title="", automargin=True)
    return _layout(fig, height=520, margin={"l": 12, "r": 24, "t": 65, "b": 46})


def individual_scores_chart(factor_table: pd.DataFrame, candidate_name: str) -> go.Figure:
    frame = factor_table[factor_table["Bloco"] != "RESUMO"].copy()
    frame = frame.sort_values(["Bloco", "ID"], ascending=[True, False])
    colors = [
        "#0B6654" if score >= 7 else "#C79A2B" if score >= 5 else "#A64B55"
        for score in frame["Nota"]
    ]
    fig = go.Figure(
        go.Bar(
            x=frame["Nota"],
            y=frame["Fator"],
            orientation="h",
            marker={"color": colors, "line": {"width": 0}},
            customdata=frame[["Peso", "Bloco", "Evidência"]],
            hovertemplate=(
                "<b>%{y}</b><br>Nota %{x:.0f}/10 · peso %{customdata[0]:.0f}"
                "<br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(title={"text": f"Notas por fator · {candidate_name}", "x": 0})
    fig.update_xaxes(title="Nota (0–10)", range=[0, 10.3], dtick=2, gridcolor=GRID)
    fig.update_yaxes(title="", automargin=True, tickfont={"size": 10})
    return _layout(fig, height=max(700, len(frame) * 21 + 120), margin={"l": 18, "r": 18, "t": 65, "b": 42})


def factor_comparison_chart(long_frame: pd.DataFrame, factor_ids: list[int]) -> go.Figure:
    frame = long_frame[long_frame["id"].isin(factor_ids)].copy()
    frame["factor_label"] = frame["id"].astype(str) + " · " + frame["factor"]
    fig = px.scatter(
        frame,
        x="score",
        y="factor_label",
        color="slug",
        symbol="slug",
        color_discrete_map=CANDIDATE_COLORS,
        labels={"score": "Nota (0–10)", "factor_label": "", "slug": "Candidato"},
        hover_name="candidate",
        hover_data={"slug": False, "weight": True, "block": True, "factor_label": False},
    )
    fig.update_traces(marker={"size": 12, "line": {"color": "#F6F7F2", "width": 1.5}})
    fig.update_layout(title={"text": "Distância entre candidatos nos fatores selecionados", "x": 0})
    fig.update_xaxes(range=[-0.2, 10.2], dtick=1, gridcolor=GRID)
    fig.update_yaxes(automargin=True)
    return _layout(fig, height=max(390, len(factor_ids) * 52 + 150), margin={"l": 20, "r": 24, "t": 78, "b": 42})


def finance_chart(finance: pd.DataFrame, candidate_name: str) -> go.Figure:
    grouped = (
        finance.groupby("donor_type", dropna=False)["amount"].sum().sort_values(ascending=True).reset_index()
    )
    fig = go.Figure(
        go.Bar(
            x=grouped["amount"],
            y=grouped["donor_type"].fillna("Não informado"),
            orientation="h",
            marker={"color": "#0B6654"},
            hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(title={"text": f"Receitas por tipo de doador · {candidate_name}", "x": 0})
    fig.update_xaxes(title="Valor declarado (R$)", gridcolor=GRID)
    fig.update_yaxes(title="")
    return _layout(fig, height=390)
