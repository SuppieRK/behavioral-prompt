import os


def api_token_configured():
    return bool(os.getenv("API_TOKEN"))
