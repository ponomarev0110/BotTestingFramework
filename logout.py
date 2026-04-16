import json
import os
import pprint
from json import JSONDecodeError
from typing import Iterable

import requests
from sqlalchemy import create_engine, text

engine = create_engine(
    os.environ.get("FEEDMER_DB_URL"),
    echo=False,
    executemany_mode='values'
)


def get_all_api_keys() -> Iterable[str]:
    result = engine.execute(
        text('''
            SELECT DISTINCT "tgBotToken"
                FROM public.cafes
                WHERE "tgBotToken" is not NULL
            UNION
            SELECT DISTINCT "tgBotToken"
                FROM public.superbots
                WHERE "tgBotToken" IS NOT NULL
            UNION
            SELECT DISTINCT "tgBackBotToken"
                FROM public.cafes
                WHERE "tgBackBotToken" is not NULL
            UNION
            SELECT DISTINCT "tgBackBotToken"
                FROM public.superbots
                WHERE "tgBackBotToken" is not NULL;
            ''')
    ).fetchall()
    return map(
        lambda x: x["tgBotToken"],
        result
    )

logOutUrl = "{api_url}/bot{token}/logOut"


def logOut(api_url, token):
    response = requests.post(logOutUrl.format(api_url=api_url, token=token))
    try:
        return json.loads(response.text)
    except JSONDecodeError:
        return response.text


API_URL = 'https://middletg.feedmerdev.ru'
for api_key in get_all_api_keys():
    pprint.pprint(logOut(API_URL, api_key))
