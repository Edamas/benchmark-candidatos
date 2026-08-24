from __future__ import annotations

import pandas as pd

from src.config import CANDIDATE_COLORS


RADAR_LABELS = {
    "Defesa e território": "Defesa e\nterritório",
    "Diplomacia": "Diplomacia",
    "Abastecimento": "Abastecimento",
    "Economia e finanças": "Economia e\nfinanças",
    "Tecnologia": "Tecnologia",
    "Energia e recursos": "Energia e\nrecursos",
    "Território e ambiente": "Território e\nambiente",
    "Infraestrutura e indústria": "Infraestrutura\ne indústria",
    "Resiliência e instituições": "Resiliência e\ninstituições",
}


def radar_options(dimensions: pd.DataFrame, title: str) -> dict:
    """Build a responsive ECharts radar from the complete 40-factor aggregation."""
    blocks = dimensions["block"].drop_duplicates().tolist()
    indicators = [
        {"name": RADAR_LABELS.get(block, block), "max": 10, "color": "#24362E"}
        for block in blocks
    ]
    data: list[dict] = []
    colors: list[str] = []
    for slug, group in dimensions.groupby("slug", sort=False):
        ordered = group.set_index("block").reindex(blocks)
        name = str(ordered["candidate"].iloc[0])
        color = CANDIDATE_COLORS.get(slug, "#0B6654")
        colors.append(color)
        data.append(
            {
                "name": name,
                "value": [round(float(value), 2) for value in ordered["score"]],
                "symbol": "circle",
                "symbolSize": 7,
                "lineStyle": {"width": 3, "color": color},
                "itemStyle": {"color": color, "borderColor": "#F6F7F2", "borderWidth": 1},
                "areaStyle": {"color": color, "opacity": 0.20 if len(dimensions["slug"].unique()) == 1 else 0.10},
            }
        )
    return {
        "backgroundColor": "transparent",
        "color": colors,
        "animationDuration": 500,
        "title": {
            "text": title,
            "left": 4,
            "top": 4,
            "textStyle": {"color": "#24362E", "fontSize": 18, "fontWeight": 650},
        },
        "tooltip": {"trigger": "item"},
        "legend": {
            "type": "scroll",
            "bottom": 2,
            "left": "center",
            "itemWidth": 22,
            "itemHeight": 8,
            "textStyle": {"color": "#374A41", "fontSize": 12},
        },
        "toolbox": {
            "show": True,
            "right": 6,
            "top": 2,
            "feature": {"saveAsImage": {"title": "Baixar PNG", "pixelRatio": 2, "name": "brasil-com-censo-radar"}},
        },
        "radar": {
            "center": ["50%", "49%"],
            "radius": "63%",
            "startAngle": 90,
            "splitNumber": 5,
            "shape": "polygon",
            "indicator": indicators,
            "axisName": {"color": "#24362E", "fontSize": 11, "lineHeight": 14},
            "axisLine": {"lineStyle": {"color": "rgba(67,88,78,.18)"}},
            "splitLine": {"lineStyle": {"color": "rgba(67,88,78,.17)", "width": 1}},
            "splitArea": {
                "areaStyle": {
                    "color": ["rgba(255,255,255,.34)", "rgba(11,102,84,.025)"],
                }
            },
        },
        "series": [{"type": "radar", "data": data, "emphasis": {"lineStyle": {"width": 4}}}],
    }


def render_radar(
    dimensions: pd.DataFrame,
    title: str,
    *,
    key: str,
    height: str = "590px",
) -> None:
    if dimensions.empty:
        return
    try:
        from streamlit_echarts import st_echarts

        st_echarts(options=radar_options(dimensions, title), height=height, key=key)
    except Exception:
        # Streamlit's headless AppTest cannot register v2 component assets. The
        # fallback also keeps the app usable if a deployment cache is incomplete.
        import streamlit as st
        from src.charts import dimension_profile_chart
        from src.config import PLOTLY_CONFIG

        st.plotly_chart(dimension_profile_chart(dimensions, title), width="stretch", config=PLOTLY_CONFIG)


def factor_radar_options(long_frame: pd.DataFrame, factor_ids: list[int], title: str) -> dict:
    frame = long_frame[long_frame["id"].isin(factor_ids)].copy()
    order = {factor_id: position for position, factor_id in enumerate(factor_ids)}
    frame["_order"] = frame["id"].map(order)
    factors = (
        frame[["id", "factor"]]
        .drop_duplicates()
        .sort_values("id", key=lambda values: values.map(order))
    )
    indicators = [
        {"name": "\n".join(str(row.factor).split()[:3]), "max": 10, "color": "#24362E"}
        for row in factors.itertuples(index=False)
    ]
    data: list[dict] = []
    colors: list[str] = []
    for slug, group in frame.sort_values("_order").groupby("slug", sort=False):
        color = CANDIDATE_COLORS.get(slug, "#0B6654")
        colors.append(color)
        data.append(
            {
                "name": str(group["candidate"].iloc[0]),
                "value": [round(float(value), 2) for value in group["score"]],
                "lineStyle": {"width": 3, "color": color},
                "itemStyle": {"color": color, "borderColor": "#F6F7F2", "borderWidth": 1},
                "areaStyle": {"color": color, "opacity": 0.08},
                "symbolSize": 7,
            }
        )
    options = {
        "backgroundColor": "transparent",
        "color": colors,
        "animationDuration": 500,
        "title": {"text": title, "left": 4, "top": 4, "textStyle": {"color": "#24362E", "fontSize": 18}},
        "tooltip": {"trigger": "item"},
        "legend": {"type": "scroll", "bottom": 2, "left": "center"},
        "toolbox": {"show": True, "right": 6, "feature": {"saveAsImage": {"title": "Baixar PNG", "pixelRatio": 2}}},
        "radar": {
            "center": ["50%", "49%"], "radius": "61%", "splitNumber": 5, "indicator": indicators,
            "axisName": {"color": "#24362E", "fontSize": 10, "lineHeight": 12},
            "axisLine": {"lineStyle": {"color": "rgba(67,88,78,.18)"}},
            "splitLine": {"lineStyle": {"color": "rgba(67,88,78,.17)"}},
            "splitArea": {"areaStyle": {"color": ["rgba(255,255,255,.34)", "rgba(11,102,84,.025)"]}},
        },
        "series": [{"type": "radar", "data": data}],
    }
    return options


def render_factor_radar(long_frame: pd.DataFrame, factor_ids: list[int], title: str, *, key: str) -> None:
    if long_frame.empty or len(factor_ids) < 3:
        return
    try:
        from streamlit_echarts import st_echarts

        st_echarts(options=factor_radar_options(long_frame, factor_ids, title), height="590px", key=key)
    except Exception:
        import streamlit as st
        from src.charts import factor_radar_chart
        from src.config import PLOTLY_CONFIG

        st.plotly_chart(factor_radar_chart(long_frame, factor_ids, title), width="stretch", config=PLOTLY_CONFIG)
