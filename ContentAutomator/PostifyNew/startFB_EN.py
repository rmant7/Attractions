import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from socials.fb import add_task_facebook, add_task_facebook_old
from utils.config import config
from utils.methods import start_func, get_last_post_date, get_data_directory, get_data_directory_old


async def main():
    all_paths = await get_data_directory_old(all_paths={},
                                             path='/home/azureuser/files/posts/city_attractions/en')
    all_paths_list = (list(all_paths.keys()))

    # Facebook
    page_name = 'CheapTrip. Pay less, visit more.'
    # page_name = 'Chiptriptest'
    facebook = {'page_name': page_name, 'acc_token': config.fb_token.get_secret_value(), 'task': add_task_facebook}

    post_date = datetime.strptime('9/30/2023, 18:00:00', '%m/%d/%Y, %H:%M:%S')

    for path in all_paths_list:
        task = await add_task_facebook_old(post_path=path,
                                           post_date=post_date,
                                           page_name=facebook['page_name'],
                                           acc_token=facebook['acc_token'])
        # task = True
        if task:
            post_date = post_date + timedelta(hours=24)
            await asyncio.sleep(1)
        else:
            continue
    await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())
