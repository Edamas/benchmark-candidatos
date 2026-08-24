from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ASSET_DIR = ROOT / "assets"

APP_TITLE = "Benchmark de Candidatos"
BRAND = "Brasil Com Censo"
TAGLINE = "Dados para escolher com autonomia"
SNAPSHOT_DATE = "2026-08-24"
KEY_FACTOR_IDS = [28, 25, 15, 32]

CANDIDATE_COLORS = {
    "lula": "#C33A46",
    "caiado": "#0B6654",
    "flavio": "#2858A5",
    "renan": "#7A4C9E",
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
