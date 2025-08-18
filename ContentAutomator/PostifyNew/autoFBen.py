import asyncio
import logging
from datetime import datetime, timedelta

from socials.fb import add_task_facebook, add_task_facebook_old
from utils.config import config
from utils.methods import start_func, get_last_post_date, get_data_directory, get_data_directory_old, \
    get_first_last_day_of_month


async def main():
    all_paths = await get_data_directory_old(all_paths={},
                                             path='/Users/dima/PycharmProjects/ChipTripProjects/scheldulePosting/files')
    all_paths_list = (list(all_paths.keys()))

    # Facebook
    page_name = 'CheapTrip. Pay less, visit more.'
    facebook = {'page_name': page_name, 'acc_token': config.fb_token.get_secret_value(), 'task': add_task_facebook}

    posting_start_date, posting_end_date = get_first_last_day_of_month()
    posting_start_date = posting_start_date.replace(hour=10, minute=00)
    posting_end_date = posting_end_date.replace(hour=10, minute=00)

    for path in all_paths_list:
        if posting_start_date >= posting_end_date:
            logging.warning(f'Start date after end date S: {posting_start_date} E: {posting_end_date}')
            return False
        task = await add_task_facebook_old(post_path=path,
                                           post_date=posting_start_date,
                                           page_name=facebook['page_name'],
                                           acc_token=facebook['acc_token'])
        # task = True
        if task:
            posting_start_date = posting_start_date + timedelta(days=1)
            await asyncio.sleep(1)
        else:
            continue
    await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())
