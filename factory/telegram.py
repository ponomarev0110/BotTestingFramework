import uuid

from telethon import TelegramClient
import socks

from config.constants import Constants


def telegram_client(session_name=uuid.uuid4().hex):
    client = TelegramClient(
        session_name,
        Constants.API_ID,
        Constants.API_HASH,
        proxy={
            "proxy_type": socks.HTTP,
            "addr": Constants.PROXY_URL,
            "port": Constants.PROXY_PORT,
            "username": Constants.PROXY_USERNAME,
            'password': Constants.PROXY_PASSWORD,
            'rdns': True
        }
    )
    return client
