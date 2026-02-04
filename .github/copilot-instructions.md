# Copilot Instructions - Bot Ultimate Prediction

## Architecture Overview

**Sports betting prediction platform** with automated daily data pipeline:
- **Backend**: FastAPI (Python) serving betting predictions via JSON contracts
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS
- **Deployment**: Render.com (separate Python + Node services)
- **Data Storage**: JSON files in `api/data/` organized by cycle day

## Critical Concept: Cycle Day

**Business day starts 6AM Europe/Madrid (not midnight UTC)**. Use `cycle_day_str()` from [api/utils/cycle_day.py](api/utils/cycle_day.py) everywhere, never `date.today()`.

```python
from api.utils.cycle_day import cycle_day_str
day = cycle_day_str()  # "2026-02-04" if before 6AM CET returns previous day
```

## Daily Pipeline Workflow

[api/scripts/daily_pipeline.py](api/scripts/daily_pipeline.py) orchestrates the complete ETL:

```
events_ingestion → odds_ingestion_multisport → odds_normalization → 
odds_probability → odds_estimation → odds_ev → odds_risk → 
odds_premium → inflated_pool_builder → picks_parlay → picks_classic → 
contract freeze
```

**Skip logic**: Each step checks if output exists before running (unless `--force`). When odds change, all downstream steps recompute automatically.

Run manually: `python api/scripts/daily_pipeline.py <cycle_day>`

## Dual Import Pattern

Code must run from **both** repo root (`uvicorn api.main:app`) and `/api` directory (Render). Always use try/except imports:

```python
try:
    from api.services.contract_service import create_contract
except ModuleNotFoundError:
    from services.contract_service import create_contract
```

See [api/main.py](api/main.py#L25-L30) for the canonical pattern.

## Path Resolution

Use [api/utils/paths.py](api/utils/paths.py) for data access (works regardless of cwd):

```python
from api.utils.paths import data_path, ensure_dir
picks_dir = data_path("picks_classic", day)  # absolute path
ensure_dir(picks_dir)  # creates if missing
```

**Never** use `os.path.join("api/data", ...)` directly.

## Data Model

### Contract Structure
JSON document returned by `/bets/today`:
```json
{
  "contract_version": "1.0",
  "contract_date": "2026-02-04",
  "picks_classic": [...],          // single bets
  "picks_by_sport": {...},          // organized by sport
  "picks_parlay_premium": [...],    // combo bets
  "daily_featured_parlay": {...},   // highlighted parlay
  "metadata": {}
}
```

### Pick Structure
```json
{
  "id": "unique_id",
  "sport": "football",
  "market": "match_winner",
  "choice": "team_name",
  "odds": 2.15,
  "ev": 0.08,
  "confidence": 0.72,
  "display": {
    "homeTeam": "...",
    "awayTeam": "...",
    "startTime": "2026-02-04T20:00:00Z",
    "competition": "...",
    "homeScore": 0,  // live updates
    "awayScore": 0
  }
}
```

## Service Layer Patterns

### Multi-sport Services
Services ending in `_multisport.py` process all enabled sports. Read from `api/data/odds/<sport>.json`, write to sport-specific outputs.

Entry point signature:
```python
def main():
    day = sys.argv[1] if len(sys.argv) > 1 else cycle_day_str()
    # process each sport
```

Run: `python api/services/<name>_multisport.py <cycle_day>`

### Sports Configuration
[api/services/sports_config.py](api/services/sports_config.py) defines enabled sports and markets. Always use `ENABLED_SPORTS` dict, not hardcoded lists.

### API Clients
External data sources in [api/services/](api/services/):
- `api_sofascore_client.py` - live odds (free, no API key)
- `api_theodds_client.py` - TheOdds API (requires key)
- `api_espn_client.py` - scores/events
- `api_thesportsdb_client.py` - metadata

All return normalized JSON. See individual files for response schemas.

## Scheduler & Automation

[api/scheduler/autoschedule.py](api/scheduler/autoschedule.py) runs pipeline automatically (Render-friendly, in-process).

**Backoff logic**: On failure, waits exponentially (1h → 2h → 4h → 6h max). State stored in `/tmp/scheduler_backoff_<day>.json`.

Lock file: `/tmp/daily_pipeline_<day>.lock` prevents concurrent runs.

## FastAPI Endpoints

Key routes in [api/main.py](api/main.py):
- `GET /bets/today` - current cycle day contract (with display enrichment)
- `GET /flashscore/match_url` - resolve team to Flashscore URL (cached)
- `GET /live/events` - multi-source live scores (ESPN + alternatives)
- `POST /admin/regenerate-contract/{day}` - force rebuild contract
- `GET /internal/ensure_today` - trigger scheduler manually

## Display Enrichment

[api/services/display_enrichment.py](api/services/display_enrichment.py) attaches:
- Team logos (from event snapshots)
- Live scores (from periodic snapshots)
- Competition names

Applied in-memory to contracts before serving. **Do not** save enriched data to disk.

## Settlement

[api/services/settlement_service.py](api/services/settlement_service.py) evaluates bet results post-match.

Run: `bash api/scripts/run_settlement.sh`

Uses [api/utils/football_results.py](api/utils/football_results.py) and [api/utils/other_sports_results.py](api/utils/other_sports_results.py) to fetch outcomes.

## Testing & Debugging

Common scripts in [api/scripts/](api/scripts/):
- `check_cycle_status.py <day>` - verify pipeline outputs
- `inspect_odds_day.py <day>` - dump raw odds data
- `diagnose_combo_blocker.py <day>` - debug parlay generation
- `generate_demo_data.py <day>` - create sample data

## Development Commands

**Backend**:
```bash
cd /workspaces/bot-ultimate-prediction-backend
pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd web
npm install
npm run dev  # http://localhost:3000
```

**Pipeline** (manual):
```bash
python api/scripts/daily_pipeline.py $(python -c "from api.utils.cycle_day import cycle_day_str; print(cycle_day_str())")
```

## File Naming Conventions

- `*_multisport.py` - processes all sports
- `*.py.bak*` - backup files (ignore)
- JSON data: `api/data/<category>/<cycle_day>/<sport>.json` or `api/data/<category>/<cycle_day>.json`

## Common Pitfalls

1. **Don't use `date.today()`** - always `cycle_day_str()`
2. **Don't hardcode paths** - use `data_path()` from [api/utils/paths.py](api/utils/paths.py)
3. **Don't skip import fallbacks** - Render runs from different cwd
4. **Don't modify enriched data** - it's computed on-the-fly per request
5. **Check skip logic** - pipeline won't re-run if outputs exist (use `--force`)

## Environment Variables

Set in Render or local `.env`:
- `ODDS_SPORTS` - comma-separated sports to process (e.g., `football,basketball,tennis`)
- `ODDS_MAX_EVENTS_PER_SPORT` - limit events fetched (default: 40)
- `APP_TZ` - timezone for cycle day (default: `Europe/Madrid`)
- API keys for external services (TheOdds, etc.)

## Code Style

- Use type hints where practical
- Fail gracefully with `safe_call()` wrapper (see [api/services/safe_call.py](api/services/safe_call.py))
- Log with timestamps: `f"[{datetime.now()}] message"`
- JSON: `ensure_ascii=False, indent=2`
