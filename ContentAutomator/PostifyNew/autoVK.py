import asyncio
import json
from datetime import datetime, timedelta

from socials.vk import add_task_vk
from utils.config import config
from utils.methods import start_func, get_last_post_date, get_first_last_day_of_month, start_func_limit


async def main():
    # Vk
    vkontakte = {'owner_id': config.owner_id.get_secret_value(), 'token': config.vk_token.get_secret_value(),
                 'task': add_task_vk}

    # Fill In this fields
    social = vkontakte
    posting_interval = timedelta(days=1)

    data_folder_path = 'files/posts/city_attractions/ru'
    posting_start_date, posting_end_date = get_first_last_day_of_month()
    posting_start_date = posting_start_date.replace(hour=10, minute=00)
    posting_end_date = posting_end_date.replace(hour=10, minute=00)

    await start_func_limit(data_folder_path=data_folder_path, start_date=posting_start_date, interval=posting_interval,
                           end_date=posting_end_date, ** social)


if __name__ == "__main__":
    asyncio.run(main())
