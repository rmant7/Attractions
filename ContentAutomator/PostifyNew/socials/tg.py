import logging
from datetime import datetime
from aiogram import types

from utils.config import config
from utils.loader import bot
from utils.methods import add_task, record_post_info, get_post_data, check_if_post_exists


async def add_task_telegram(post_path: str, post_date: datetime):
    async def post_telegram_immediate(image_urls: [str], post_text: str):
        image_urls = [
            "https://cheaptrip.guru/files/images/city_attractions/Tehran/1_Golestan_Palace.jpg",
            "https://cheaptrip.guru/files/images/city_attractions/Tehran/2_National_Museum_of_Iran.jpg",
            "https://cheaptrip.guru/files/images/city_attractions/Tehran/3_Tehran_Bazaar.jpg"
        ]
        media = [types.InputMediaPhoto(media=url) for url in image_urls]
        post = await bot.send_media_group(chat_id=config.channel_id.get_secret_value(), media=media)
        await bot.send_message(chat_id=config.channel_id.get_secret_value(), text=post_text,
                               reply_to_message_id=post.message_id)

    social = 'Telegram'
    if not check_if_post_exists(path=post_path, social=social):
        logging.warning(f'{post_path} post already exists')
        return False

    post_text, image = await get_post_data(post_path)

    await add_task(image, post_text, task=post_telegram_immediate, post_date=post_date, trigger='date')
    logging.warning(f'{post_path}\n{post_date.strftime("%m/%d/%Y, %H:%M:%S")}\n{social} (immediate)\n')
    record_post_info(path=post_path, social=social)
    return True
