import os
from dotenv import load_dotenv

load_dotenv()

def get_env() -> dict:
    """
    Returns validated environment variables for the backend.
    """
    api_key = os.getenv("API_SPORTS_KEY")
    env = os.getenv("ENV", "development")

    if not api_key:
        raise RuntimeError("API_SPORTS_KEY no configurada")

    return {
        "API_SPORTS_KEY": api_key,
        "ENV": env,
    }
