import asyncio
import logging
import random
from dataclasses import dataclass
from time import time
from typing import List, Optional, Dict

import telethon.types
from sqlalchemy.exc import SQLAlchemyError
from telethon import events

from prometheus_client import Histogram

from service.telegram import TelegramService
from config.constants import Constants
from repository.response import ResponseRepository
from entity.response import Response

WAIT_MIN = 40
WAIT_MAX = 120

TIMEOUT_ALERT = '''
Время отклика от бота {name}
на сообщение {message}: 
{response_time:.2f} секунд
'''


ERROR_ALERT = '''
Бот {name} не откликнулся 
на сообщение {message} за 
{response_time:.2f} секунд
'''

ERROR_CONTINUE_ALERT = '''
Бот {name} продолжает не откликаться 
на сообщение {message} за 
{response_time:.2f} секунд
'''

STATISTICS_TEMPLATE = '''
Среднее время отклика {name}: {average:.2f} за {total} запросов из них: 
{first_bucket}% <1 секунды, 
{second_bucket}% от 1 до 5 секунд, 
{third_bucket}% >5 секунд
'''


@dataclass
class Scenario:
    name: str
    message: Optional[str]
    timestamp: float
    next_messages: List[str]
    erred: bool
    entity: telethon.types.InputPeerUser

    @classmethod
    def create(cls, name: str, scenario: List[str], entity: telethon.types.InputPeerUser):
        return cls(
            name=name,
            message=None,
            timestamp=time(),
            next_messages=scenario,
            erred=False,
            entity=entity
        )


async def wait():
    await asyncio.sleep(random.uniform(WAIT_MIN, WAIT_MAX))


class TestService:
    __slots__ = ["response_repository", "telegram_service", "account", "client", "respondent", "awaited_scenarios",
                 "histograms", "manager", "bot", "bot_client", "message_queue", "processing", "scenarios"]

    def __init__(self, telegram_service: TelegramService, response_repository: ResponseRepository, account: str,
                 bot: str):
        self.telegram_service = telegram_service
        self.response_repository = response_repository

        self.account = account
        self.bot = bot
        self.client = None
        self.bot_client = None

        self.awaited_scenarios = {}
        self.scenarios: Dict[int, Scenario] = {}
        self.histograms = {}
        self.manager = None

        self.message_queue = asyncio.Queue()
        self.processing = False

    async def start(self):
        if not self.processing:
            self.processing = True
            logging.info("Starting tests")
            return asyncio.create_task(self.process_queue())
        else:
            logging.info("Tests have already started")

    def stop(self):
        self.processing = False

    async def process_queue(self):
        logging.info("Started processing")
        while self.processing:
            logging.info("Awaiting scenario")
            scenario = await self.message_queue.get()
            logging.info(f"Processing scenario: {scenario.name}")
            await self.process_step(scenario)
            self.message_queue.task_done()
            await asyncio.sleep(15)

    async def process_step(self, scenario: Scenario):
        if scenario.erred:
            await self.repeat_message(scenario.message, scenario.entity)
        else:
            recipient_id = scenario.entity.user_id
            await self.advance_scenario(scenario)
            count = 0
            worth_waiting = True
            while worth_waiting:
                await asyncio.sleep(1)
                count += 1
                worth_waiting = recipient_id in self.awaited_scenarios and self.awaited_scenarios[
                    recipient_id].message == scenario.next_messages[0] and count < Constants.TEST_INTERVAL

    async def advance_scenario(self, scenario: Scenario):
        message = scenario.next_messages[0]
        recipient = scenario.entity
        self.awaited_scenarios[recipient.user_id] = Scenario(
            name=scenario.name,
            message=message,
            timestamp=time(),
            next_messages=scenario.next_messages[1:],
            erred=False,
            entity=recipient
        )
        try:
            await self.telegram_service.send_message(self.client, recipient, message)
            logging.info(f"Sent {message} to {scenario.name}")
        except ValueError as exc:
            logging.warning(exc)
            logging.warning(f"Could not find PeerUser for {recipient}:{scenario.name}")
            del self.awaited_scenarios[recipient.user_id]
            await self.send_alert(f"Не нашел бота для {recipient}:{scenario.name}")

    async def repeat_message(self, message, recipient):
        await self.telegram_service.send_message(self.client, recipient, message)

    async def send_alert(self, message):
        await self.telegram_service.send_message(self.bot_client, self.manager, message)

    async def save(self, response_time, name):
        try:
            self.response_repository.save(Response(None, response_time, name))
        except SQLAlchemyError as exc:
            await self.send_alert(f"Не удалось сохранить ответ для бота {name} в базу данных. Ошибка {str(exc)}.")

    async def init_client(self):
        self.client = await self.telegram_service.login(self.account)
        self.bot_client = await self.telegram_service.login_bot(self.bot)

        @self.client.on(events.NewMessage(incoming=True))
        async def handler(event):
            end = time()
            try:
                sender_id = event.message.input_sender.user_id
                if sender_id in self.awaited_scenarios:
                    scenario = self.awaited_scenarios.pop(sender_id)
                    response_time = end - scenario.timestamp
                    name = scenario.name
                    self.histograms[name].observe(response_time)

                    await self.save(response_time, name)
                    logging.info(f'Time on response for {name}: {response_time}')

                    if response_time > Constants.TEST_TIMEOUT:
                        await self.send_alert(
                            TIMEOUT_ALERT.format(name=name, message=scenario.message, response_time=response_time)
                        )

                    if len(scenario.next_messages) > 0:
                        await self.message_queue.put(scenario)
                    else:
                        await self.message_queue.put(self.scenarios[scenario.entity.user_id])
            except Exception as exc:
                logging.info(exc)

    async def add_scenario(self, scenario_list: List[str], name: str, recipient: telethon.types.InputPeerUser):
        if name not in self.histograms:
            self.histograms[name] = Histogram(f"{name}_request_latency_seconds",
                                              f"Latency between sending a message and getting a response for {name}")
        if recipient.user_id not in self.scenarios:
            scenario = Scenario.create(name, scenario_list, recipient)
            self.scenarios[recipient.user_id] = scenario
            await self.message_queue.put(scenario)

    async def start_cleanup(self):
        answers_to_clean = self.awaited_scenarios.copy()
        messages = []
        for recipient in answers_to_clean:
            scenario = self.awaited_scenarios[recipient]
            response_time = time() - scenario.timestamp
            if response_time > Constants.ERROR_TIMEOUT:
                scenario = self.awaited_scenarios[recipient]
                alert = ERROR_ALERT if not scenario.erred else ERROR_CONTINUE_ALERT
                scenario.erred = True
                messages.append(alert.format(
                    name=scenario.name,
                    message=scenario.message,
                    response_time=response_time
                ))
                await self.message_queue.put(scenario)
        if len(messages) > 0:
            logging.warning("Sending alerts")
            await self.send_alert(
                '\n'.join(messages)
            )

    async def send_statistics(self):
        statistics = self.response_repository.statistics()
        message = []
        for bot in statistics:
            text = STATISTICS_TEMPLATE.format(
                name=bot["name"], average=bot["average"], total=bot["total"],
                first_bucket=bot["first_bucket"], second_bucket=bot["second_bucket"],
                third_bucket=bot["third_bucket"]
            ).strip()
            message.append(text)
            if sum(map(len, message)) > 2000:
                await self.send_alert('\n'.join(message))
                message = []
        if message:
            await self.send_alert('\n'.join(message))
