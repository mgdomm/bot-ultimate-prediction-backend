from services.logger import logger

def safe_call(fn, *, name="external_api"):
    try:
        return fn()
    except Exception as e:
        logger.error(f"{name} failed: {e}", exc_info=True)
        return None
