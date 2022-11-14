import asyncio
import json
import logging
import random
from time import time
from typing import List

from telethon import events

from prometheus_client import Histogram


from service.telegram import TelegramService
from config.constants import Constants
from repository.response import ResponseRepository
from entity.response import Response

WAIT_MIN = 20
WAIT_MAX = 60


async def wait():
    await asyncio.sleep(random.uniform(WAIT_MIN, WAIT_MAX))


class TestService:
    __slots__ = ["response_repository", "telegram_service", "account", "client", "respondent", "await_answers", "histograms", "manager", "bot", "bot_client"]

    def __init__(self, telegram_service: TelegramService, response_repository: ResponseRepository, account: str, bot: str):
        self.telegram_service = telegram_service
        self.response_repository = response_repository

        self.account = account
        self.bot = bot
        self.client = None
        self.bot_client = None

        self.await_answers = {}
        self.histograms = {}
        self.manager = None

    async def advance_scenario(self, awaited_answer, recipient):
        await wait()
        scenario = awaited_answer["scenario"]
        message = scenario[0]
        self.await_answers[recipient] = {
            "name": awaited_answer["name"],
            "message": message,
            "timestamp": time(),
            "scenario": scenario[1:],
            "erred": False
        }
        await self.telegram_service.send_message(self.client, recipient, message)

    async def repeat_message(self, message, recipient):
        await wait()
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
                    name = awaited_answer["name"]
                    self.histograms[name].observe(response_time)
                    logging.info(f'Time on response for {name}: {response_time}')
                    self.response_repository.save(Response(None, response_time, name))
                    if response_time > Constants.TEST_TIMEOUT:
                        await wait()
                        await self.telegram_service.send_message(
                            self.bot_client,
                            self.manager,
                            f'''
Время отклика от бота {name}
на сообщение {awaited_answer["message"]}: 
{response_time:.2f} секунд
                            ''')
                    if len(scenario) > 0:
                        await self.advance_scenario(awaited_answer, recipient)
                    else:
                        self.await_answers.pop(recipient)
            except Exception as exc:
                logging.info(exc)

    async def test_bot(self, scenario, name, recipient):
        if name not in self.histograms:
            self.histograms[name] = Histogram(f"{name}_request_latency_seconds", f"Latency between sendning a message and getting a response for {name}")
        if recipient.id not in self.await_answers:
            start = {
                "name": name,
                "message": None,
                "timestamp": time(),
                "scenario": scenario,
                "erred": False
            }
            await self.advance_scenario(start, recipient.id)
        elif self.await_answers[recipient.id]["erred"]:
            start = self.await_answers[recipient.id]
            logging.info(f'Resending message {start["message"]} to {start["name"]}')
            message = start["message"]
            await self.repeat_message(message, recipient.id)

    async def start_cleanup(self):
        answers_to_clean = self.await_answers.copy()
        messages = []
        for recipient in answers_to_clean:
            response_time = time() - self.await_answers[recipient]["timestamp"]
            if response_time > Constants.ERROR_TIMEOUT:
                awaited_answer = self.await_answers[recipient]
                self.response_repository.save(Response(None, None, awaited_answer["name"]))
                if not awaited_answer["erred"]:
                    awaited_answer["erred"] = True
                    messages.append(
                        f'''
Бот {awaited_answer["name"]} не откликнулся 
на сообщение {awaited_answer["message"]} за 
{response_time:.2f} секунд
                        '''
                    )
                else:
                    messages.append(
                        f'''
Бот {awaited_answer["name"]} продолжает не откликаться 
на сообщение {awaited_answer["message"]}: 
{response_time:.2f} секунд
                        '''
                    )
        if len(messages) > 0:
            logging.warning("Sending alerts")
            await wait()
            await self.telegram_service.send_message(
                self.bot_client,
                self.manager,
                '\n'.join(messages))

    async def send_statistics(self):
        statistics = self.response_repository.statistics()
        for bot in statistics:
            await wait()
            await self.telegram_service.send_message(
                self.bot_client,
                self.manager,
                f'''
Статистика по {bot["name"]}:
Среднее время отклика: {bot["average"]:.2f}
Отклонение времени отклика: {bot["deviation"]:.2f}
Всего сделано запросов сегодня: {bot["total"]}
Из них:
<1 секунды отклика: {bot["first_bucket"]}%
от 1 до 2 секунд отклика: {bot["second_bucket"]}%
от 2 до 3 секунд отклика: {bot["third_bucket"]}%
от 3 до 4 секунд отклика: {bot["fourth_bucket"]}%
от 4 до 5 секунд отклика: {bot["fifth_bucket"]}%
>5 секунд отклика: {bot["sixth_bucket"]}%
                ''')




