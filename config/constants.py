import logging
import os
import configparser


class Constants:
    _config = configparser.ConfigParser()
    _config.read("resources/config.ini")

    TEST_TIMEOUT = int(os.environ.get("TEST_TIMEOUT") or _config["DEFAULT"]["TEST_TIMEOUT"])
    ERROR_TIMEOUT = int(os.environ.get("ERROR_TIMEOUT") or _config["DEFAULT"]["ERROR_TIMEOUT"])
    TEST_INTERVAL = int(os.environ.get("TEST_INTERVAL") or _config["DEFAULT"]["TEST_INTERVAL"])
    CLEANUP_INTERVAL = int(os.environ.get("CLEANUP_INTERVAL") or _config["DEFAULT"]["CLEANUP_INTERVAL"])
    API_ID = os.environ.get("API_ID") or _config["DEFAULT"]["API_ID"]
    API_HASH = os.environ.get("API_HASH") or _config["DEFAULT"]["API_HASH"]
    ACCOUNT = os.environ.get("ACCOUNT") or _config["DEFAULT"]["ACCOUNT"]
    API_KEY_BOT = os.environ.get("API_KEY_BOT") or _config["DEFAULT"]["API_KEY_BOT"]
    DB_URL = os.environ.get("DB_URL") or _config["DEFAULT"]["DB_URL"]

