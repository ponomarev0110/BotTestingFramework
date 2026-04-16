import logging
import time
from typing import Iterable
import random

from repository import BotRepository
from .phone import PhoneService


class BotService:
    __slots__ = ["bot_repository"]

    def __init__(self, bot_repository: BotRepository):
        self.bot_repository = bot_repository

    def get_api_keys(self) -> Iterable[str]:
        return self.bot_repository.get_api_keys()