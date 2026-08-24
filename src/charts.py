from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import CANDIDATE_COLORS


PAPER = "rgba(0,0,0,0)"
GRID = "rgba(67,88,78,.16)"
INK = "#24362E"
MUTED = "#5B6C64"


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
    for slug, group in dimensions.groupby("slug", sort=False):
        ordered = group.set_index("block").reindex(blocks).reset_index()
        fig.add_trace(
            go.Scatterpolar(
                r=ordered["score"],
                theta=ordered["block"],
                name=ordered["candidate"].iloc[0],
                mode="lines+markers",
                line={"color": CANDIDATE_COLORS.get(slug), "width": 2.5},
                marker={"size": 7, "symbol": "circle"},
                fill="toself" if dimensions["slug"].nunique() == 1 else None,
                opacity=0.76,
                hovertemplate="<b>%{theta}</b><br>%{r:.2f}/10<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(
        title={"text": title, "x": 0},
        polar={
            "bgcolor": PAPER,
            "radialaxis": {"range": [0, 10], "dtick": 2, "gridcolor": GRID, "tickfont": {"color": MUTED}},
            "angularaxis": {"gridcolor": GRID, "tickfont": {"size": 11}},
        },
    )
    fig = _layout(fig, height=610, margin={"l": 70, "r": 70, "t": 76, "b": 96})
    fig.update_layout(
        showlegend=dimensions["slug"].nunique() > 1,
        legend={"orientation": "h", "yanchor": "top", "y": -0.10, "xanchor": "left", "x": 0},
    )
    return fig


def factor_radar_chart(
    long_frame: pd.DataFrame,
    factor_ids: list[int],
    title: str = "Radar de fatores-chave",
) -> go.Figure:
    frame = long_frame[long_frame["id"].isin(factor_ids)].copy()
    order = {factor_id: position for position, factor_id in enumerate(factor_ids)}
    frame["_order"] = frame["id"].map(order)
    short_labels = {
        28: "Terras<br>raras",
        25: "Transição<br>energética",
        15: "Indústria<br>nacional",
        32: "Ferrovias<br>e logística",
    }
    frame["axis_label"] = frame.apply(
        lambda row: short_labels.get(int(row["id"]), row["factor"]),
        axis=1,
    )
    fig = go.Figure()
    for slug, group in frame.sort_values("_order").groupby("slug", sort=False):
        fig.add_trace(
            go.Scatterpolar(
                r=group["score"],
                theta=group["axis_label"],
                name=group["candidate"].iloc[0],
                mode="lines+markers",
                line={"color": CANDIDATE_COLORS.get(slug), "width": 3},
                marker={"size": 8},
                fill="toself" if frame["slug"].nunique() == 1 else None,
                opacity=0.78,
                customdata=group[["factor"]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{r:.1f}/10<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(
        title={"text": title, "x": 0},
        polar={
            "bgcolor": PAPER,
            "radialaxis": {"range": [0, 10], "dtick": 2, "gridcolor": GRID},
            "angularaxis": {"gridcolor": GRID, "tickfont": {"size": 11}},
        },
    )
    fig = _layout(fig, height=550, margin={"l": 58, "r": 58, "t": 72, "b": 96})
    fig.update_layout(
        showlegend=frame["slug"].nunique() > 1,
        legend={"orientation": "h", "yanchor": "top", "y": -0.11, "xanchor": "left", "x": 0},
    )
    return fig


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
