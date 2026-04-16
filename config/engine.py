import os
from sqlalchemy import create_engine

from config.constants import Constants


class DatabaseConfiguration:
    BATCH_SIZE = 1000
    _log_engine = None
    _feedmer_engine = None

    @classmethod
    def get_log_engine(cls):
        if cls._log_engine is None:
            cls._log_engine = create_engine(
                Constants.LOG_DB_URL,
                echo=False,
                executemany_mode='values',
                executemany_values_page_size=cls.BATCH_SIZE
            )
        return cls._log_engine

    @classmethod
    def get_feedmer_engine(cls):
        if cls._feedmer_engine is None:
            cls._feedmer_engine = create_engine(
                Constants.FEEDMER_DB_URL,
                echo=False,
                executemany_mode='values',
                executemany_values_page_size=cls.BATCH_SIZE
            )
        return cls._feedmer_engine
