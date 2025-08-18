import asyncio
from datetime import datetime, timedelta
from utils.methods import get_names_from_link
from utils.config import config
from socials.tg import add_task_telegram


async def main():
    url = 'http://20.240.63.21/files/posts/city_attractions/ru/'

    json_files = await get_names_from_link(url)

    # post_date = datetime.strptime('06/15/2023, 14:30:00', '%m/%d/%Y, %H:%M:%S')
    post_date = datetime.now() + timedelta(seconds=5)

    for name in json_files:
        post_path = url + name
        print(post_path)
        print(f'{json_files.index(name)}/{len(json_files)}')
        task = None
        try:
            task = await add_task_telegram(post_path=post_path, post_date=post_date)
        except KeyError:
            print(post_path)

        if task:
            await asyncio.sleep(100000)
            post_date = post_date + timedelta(hours=1)
            await asyncio.sleep(1)
        else:
            continue
    await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())
