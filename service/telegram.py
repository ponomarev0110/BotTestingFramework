import logging
import time
import random

import factory.telegram as telegram_factory
from service.phone import PhoneService


class TelegramService:
    __slots__ = ["phone_service"]

    def __init__(self, phone_service: PhoneService):
        self.phone_service = phone_service

    async def login(self, phone: str):
        client = telegram_factory.telegram_client(phone)
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            request_code = await self.phone_service.auth_code(phone)
            me = await client.sign_in(phone, request_code)
        return client

    async def login_bot(self, api: str):
        client = telegram_factory.telegram_client("testBot")
        me = await client.start(bot_token=api)
        logging.debug(f"Logged in: {me}")
        return client

    async def send_message(self, client, recipient: str, text: str):
        await client.send_message(recipient, text)
