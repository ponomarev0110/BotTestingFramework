import logging
from typing import Iterable

from sqlalchemy.engine import Engine
from sqlalchemy import text


class BotRepository:
    __slots__ = ['engine']

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_api_keys(self) -> Iterable[str]:
        result = self.engine.execute(
            text('''
                SELECT DISTINCT "tgBotToken"
                    FROM public.cafes
                    WHERE "tgBotToken" is not NULL
                UNION
                SELECT DISTINCT "tgBotToken"
                    FROM public.superbots
                    WHERE "tgBotToken" IS NOT NULL;
                    ''')
        ).fetchall()
        return map(
            lambda x: x["tgBotToken"],
            result
        )