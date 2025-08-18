import asyncio
from datetime import datetime, timedelta

from socials.fb import add_task_facebook
from utils.config import config
from utils.methods import start_func, get_last_post_date, start_func_limit, get_first_last_day_of_month


async def main():
    # Facebook
    page_name = 'CheapTrip. Pay less, visit more.'
    facebook = {'page_name': page_name, 'acc_token': config.fb_token.get_secret_value(), 'task': add_task_facebook}

    # Fill In this fields
    social = facebook
    posting_interval = timedelta(days=1)

    data_folder_path = '/Users/dima/PycharmProjects/PostifyNew/files/posts/city_attractions/ru'

    posting_start_date, posting_end_date = get_first_last_day_of_month()
    posting_start_date = posting_start_date.replace(hour=10, minute=30)
    posting_end_date = posting_end_date.replace(hour=10, minute=30)

    await start_func_limit(data_folder_path=data_folder_path, start_date=posting_start_date, interval=posting_interval,
                           end_date=posting_end_date, **social)


if __name__ == "__main__":
    asyncio.run(main())
