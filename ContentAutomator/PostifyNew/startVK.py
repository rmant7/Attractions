import asyncio
import json
from datetime import datetime, timedelta

from socials.vk import add_task_vk
from utils.config import config
from utils.methods import start_func, get_last_post_date


async def main():
    # Vk
    vkontakte = {'owner_id': config.owner_id.get_secret_value(), 'token': config.vk_token.get_secret_value(),
                 'task': add_task_vk}

    # Fill In this fields
    social = vkontakte
    posting_interval = timedelta(hours=1)

    data_folder_path = 'files/posts/city_attractions/ru'
    posting_start_date = get_last_post_date('Vkontakte') + posting_interval

    await start_func(data_folder_path=data_folder_path, start_date=posting_start_date, interval=posting_interval,
                     **social)


if __name__ == "__main__":
    asyncio.run(main())
