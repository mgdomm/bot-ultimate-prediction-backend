from pathlib import Path

# Este archivo vive en: <repo>/api/utils/paths.py
# API_DIR = <repo>/api
API_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = API_DIR / "data"

def data_path(*parts) -> Path:
    """Path absoluto a <repo>/api/data/<parts...> (independiente del cwd)."""
    return DATA_DIR.joinpath(*parts)

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p
