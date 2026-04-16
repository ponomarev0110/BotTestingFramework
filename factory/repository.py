from repository import ResponseRepository, BotRepository
from config.engine import DatabaseConfiguration


class RepositoryFactory:
    __slots__ = ["_bot", "_response"]
    instance = None

    def __init__(self):
        self._bot = None
        self._response = None

    @property
    def bot(self) -> BotRepository:
        if self._bot is None:
            self._bot = BotRepository(DatabaseConfiguration.get_feedmer_engine())
        return self._bot

    @property
    def response(self) -> ResponseRepository:
        if self._response is None:
            self._response = ResponseRepository(DatabaseConfiguration.get_log_engine())
        return self._response

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = RepositoryFactory()
        return cls.instance

