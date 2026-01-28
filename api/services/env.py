import os
from dotenv import load_dotenv

load_dotenv()

def get_env() -> dict:
    """
    Returns validated environment variables for the backend.
    
    Required:
    - ODDS_API_KEY: The Odds API for real betting odds
    
    Optional:
    - ENV: environment name (default: development)
    """
    odds_api_key = os.getenv("ODDS_API_KEY", "")
    env = os.getenv("ENV", "development")

    # ODDS_API_KEY is optional (fallbacks to cache if not set)
    if not odds_api_key:
        print("WARNING: ODDS_API_KEY not configured. Using cached odds only.")

    return {
        "ODDS_API_KEY": odds_api_key,
        "ENV": env,
    }
