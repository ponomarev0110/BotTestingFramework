import os


class Constants:
    TEST_TIMEOUT = int(os.environ.get("TEST_TIMEOUT"))
    ERROR_TIMEOUT = int(os.environ.get("ERROR_TIMEOUT"))
    TEST_INTERVAL = int(os.environ.get("TEST_INTERVAL"))
    CLEANUP_INTERVAL = int(os.environ.get("CLEANUP_INTERVAL"))
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    ACCOUNT = os.environ.get("ACCOUNT")
    API_KEY_BOT = os.environ.get("API_KEY_BOT")
    LOG_DB_URL = os.environ.get("LOG_DB_URL")
    FEEDMER_DB_URL = os.environ.get("FEEDMER_DB_URL")
    PROXY_URL = os.environ.get("PROXY_URL", None)
    PROXY_PORT = int(os.environ.get("PROXY_PORT")) if os.environ.get("PROXY_PORT") else None
    PROXY_USERNAME = os.environ.get("PROXY_USERNAME", None)
    PROXY_PASSWORD = os.environ.get("PROXY_password", None)
