import asyncio
import json
import logging
import random
from time import time
from typing import List

from telethon import events

from service.telegram import TelegramService
from config.constants import Constants
from repository.response import ResponseRepository
from entity.response import Response

WAIT_MIN = 20
WAIT_MAX = 90


async def wait():
    await asyncio.sleep(random.uniform(WAIT_MIN, WAIT_MAX))


class TestService:
    __slots__ = ["response_repository", "telegram_service", "account", "client", "respondent", "await_answers", "manager", "bot", "bot_client"]

    def __init__(self, telegram_service: TelegramService, response_repository: ResponseRepository, account: str, bot: str):
        self.telegram_service = telegram_service
        self.response_repository = response_repository

        self.account = account
        self.bot = bot
        self.client = None
        self.bot_client = None

        self.await_answers = {}
        self.manager = None

    async def advance_scenario(self, awaited_answer, recipient):
        await wait()
        scenario = awaited_answer["scenario"]
        message = scenario[0]
        self.await_answers[recipient] = {
            "name": awaited_answer["name"],
            "message": message,
            "timestamp": time(),
            "scenario": scenario[1:]
        }
        await self.telegram_service.send_message(self.client, recipient, message)

    # async fuckery because fuck python
    async def init_client(self):
        self.client = await self.telegram_service.login(self.account)
        logging.debug(f"API KEY for bot: {self.bot}")
        self.bot_client = await self.telegram_service.login_bot(self.bot)

        @self.client.on(events.NewMessage(incoming=True))
        async def handler(event):
            end = time()
            try:
                recipient = event.message.peer_id.user_id
                if recipient in self.await_answers:
                    awaited_answer = self.await_answers.pop(recipient)
                    scenario = awaited_answer["scenario"]
                    response_time = end - awaited_answer["timestamp"]
                    logging.info(f'Time on response for {awaited_answer["name"]}: {response_time}')
                    self.response_repository.save(Response(None, response_time, awaited_answer["name"]))
                    if response_time > Constants.TEST_TIMEOUT:
                        await wait()
                        await self.telegram_service.send_message(
                            self.bot_client,
                            self.manager,
                            f'''
?????????? ?????????????? ???? ???????? {awaited_answer["name"]}
???? ?????????????????? {awaited_answer["message"]}: 
{response_time:.2f} ????????????
                            ''')
                    if len(scenario) > 0:
                        await self.advance_scenario(awaited_answer, recipient)
                    else:
                        self.await_answers.pop(recipient)
            except Exception as exc:
                logging.info(exc)

    async def test_bot(self, scenario, name, recipient):
        start = {
            "name": name,
            "message": None,
            "timestamp": time(),
            "scenario": scenario
        }
        await self.advance_scenario(start, recipient.id)

    async def start_cleanup(self):
        for recipient in self.await_answers:
            response_time = time() - self.await_answers[recipient]["timestamp"]
            if response_time > Constants.ERROR_TIMEOUT:
                wait_task = wait()
                self.response_repository.save(Response(None, None, self.await_answers[recipient]["name"]))
                await wait_task
                await self.telegram_service.send_message(
                    self.bot_client,
                    self.manager,
                    f'''
?????? {self.await_answers[recipient]["name"]} ???? ?????????????????????? 
???? ?????????????????? {self.await_answers[recipient]["message"]}: 
???? {response_time:.2f} ????????????
                    ''')

    async def send_statistics(self):
        statistics = self.response_repository.statistics()
        for bot in statistics:
            await wait()
            await self.telegram_service.send_message(
                self.bot_client,
                self.manager,
                f'''
???????????????????? ???? {bot["name"]}:
?????????????? ?????????? ??????????????: {bot["average"]:.2f}
???????????????????? ?????????????? ??????????????: {bot["deviation"]:.2f}
?????????? ?????????????? ???????????????? ??????????????: {bot["total"]}
???? ??????:
<1 ?????????????? ??????????????: {bot["first_bucket"]}%
???? 1 ???? 2 ???????????? ??????????????: {bot["second_bucket"]}%
???? 2 ???? 3 ???????????? ??????????????: {bot["third_bucket"]}%
???? 3 ???? 4 ???????????? ??????????????: {bot["fourth_bucket"]}%
???? 4 ???? 5 ???????????? ??????????????: {bot["fifth_bucket"]}%
>5 ???????????? ??????????????: {bot["sixth_bucket"]}%
                ''')




