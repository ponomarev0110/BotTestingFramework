import asyncio
import json
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from prometheus_client import start_http_server
from pytz import timezone

from config.constants import Constants
from factory.service import ServiceFactory

logging.basicConfig(
    format='%(asctime)s:%(levelname)s:%(message)s',
    encoding='utf-8',
    level=logging.INFO
)


async def schedule():
    test = ServiceFactory.get().test
    bots = ServiceFactory.get().bot
    telegram = ServiceFactory.get().telegram
    await test.init_client()
    run_client = test.client.run_until_disconnected()

    logging.debug("Preparing scheduling job")
    scheduler = AsyncIOScheduler()
    logging.debug("Starting schedule")
    cleanup_interval = IntervalTrigger(seconds=Constants.CLEANUP_INTERVAL)
    cron_stat = CronTrigger(hour=21, timezone=timezone("Europe/Samara"))
    scheduler.add_job(test.start_cleanup, cleanup_interval)
    scheduler.add_job(test.send_statistics, cron_stat)
    scheduler.start()
    run_tests = await test.start()
    with open("resources/scenarios.json", "rb") as f:
        data = json.load(f)
        test.manager = await test.bot_client.get_entity(data["manager"])
        scenario = data["scenario"]
        logging.info(f"Manager chat id :{test.manager.id}")
        for api_key in bots.get_api_keys():
            await asyncio.sleep(3)
            bot = await telegram.get_bot_name(api_key)
            name = bot.username
            await test.add_scenario(
                scenario, name, await test.client.get_input_entity(name)
            )
    await asyncio.gather(run_client, run_tests)


async def main():
    start_http_server(8080)
    await schedule()


if __name__ == "__main__":
    asyncio.run(main())
