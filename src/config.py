from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ASSET_DIR = ROOT / "assets"

APP_TITLE = "Benchmark de Candidatos"
BRAND = "Brasil Com Censo"
TAGLINE = "Dados para escolher com autonomia"
SNAPSHOT_DATE = "2026-08-24"

CANDIDATE_COLORS = {
    "lula": "#C33A46",
    "caiado": "#0B6654",
    "flavio": "#2858A5",
    "renan": "#7A4C9E",
    "hertz": "#D97706",
    "edmilson": "#8B1E3F",
    "clariana": "#B45309",
    "pablo": "#4F46E5",
    "rui": "#991B1B",
    "zema": "#2563EB",
    "wilson": "#0F766E",
    "augusto": "#9333EA",
    "samara": "#BE185D",
}

PLOTLY_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": False,
    "modeBarButtonsToRemove": ["lasso2d"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "brasil-com-censo",
        "height": 900,
        "width": 1600,
        "scale": 2,
    },
}
