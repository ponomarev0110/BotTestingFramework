from config.constants import Constants
from service import BotService, PhoneService, TelegramService, TestService
from factory.repository import RepositoryFactory


class ServiceFactory:
    __slots__ = ["_repository_factory", "_bot", "_phone", "_telegram", "_test"]
    instance = None

    def __init__(self):
        self._repository_factory = RepositoryFactory()
        self._bot = None
        self._phone = None
        self._telegram = None
        self._test = None

    @property
    def bot(self) -> BotService:
        if self._bot is None:
            self._bot = BotService(self._repository_factory.bot)
        return self._bot

    @property
    def phone(self) -> PhoneService:
        if self._phone is None:
            self._phone = PhoneService()
        return self._phone

    @property
    def telegram(self) -> TelegramService:
        if self._telegram is None:
            self._telegram = TelegramService(self.phone)
        return self._telegram

    @property
    def test(self) -> TestService:
        if self._test is None:
            self._test = TestService(self.telegram, self._repository_factory.response, Constants.ACCOUNT, Constants.API_KEY_BOT)
        return self._test

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = ServiceFactory()
        return cls.instance
