import asyncio
import logging
import os
from datetime import datetime, timedelta
import facebook
import requests
import utils.methods
from socials.vk import download_photo
from utils.methods import add_task, record_post_info, get_post_data_by_path, get_page, check_if_post_exists, \
    update_post_info, record_post_info_old, check_if_post_exists_old, update_post_info_old, get_post_data_by_path_old

loger = logging.getLogger(__name__)
loger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

file_handler = logging.FileHandler('fb.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

loger.addHandler(file_handler)


async def add_task_facebook(post_path: str,
                            post_date: datetime,
                            page_name: str,
                            acc_token: str):
    social = 'Facebook'

    async def post_facebook_immediate(acc_token: str, image_paths: list, post_text: str, page_name: str):
        try:
            # Set name of the pages where we want to post
            page = get_page(acc_token, page_name)
            graphPage = facebook.GraphAPI(page['access_token'])
            # Upload the image
            for path in image_paths:
                # Upload the image
                with open(path, 'rb') as image_file:
                    image_data = image_file.read()
                    graphPage.put_photo(image=image_data, album_path='me/photos', message=post_text)
            update_post_info(path=post_path, social=social, value=True)
        except Exception as e:
            loger.warning(f'Error in post_facebook_immediate \n{e}')
            raise e
        finally:
            for image_path in image_path_list:
                os.remove(image_path)

    async def post_facebook_planned(acc_token: str, image_paths: list, post_text: str, page_name: str):
        ACC_ACCESS_TOKEN = acc_token
        try:
            # The Facebook ID of the page to post on
            page = get_page(acc_token, page_name)

            GET_TOKEN_URL = f'https://graph.facebook.com/{page["id"]}?fields=access_token&access_token={ACC_ACCESS_TOKEN}'

            # The page access token from Facebook App
            PAGE_ACCESS_TOKEN = requests.get(url=GET_TOKEN_URL).json()['access_token']

            # Scheduled time in the future
            SCHEDULED_TIME = int(post_date.timestamp())

            # The Graph API endpoint for photos
            url = f'https://graph.facebook.com/{page["id"]}/photos'

            # The image to post
            image_data_list = []
            for index, path in enumerate(image_paths):
                image_data = {
                    f'file{index}': open(path, 'rb')
                }
                image_data_list.append(image_data)
            files = {k: v for d in image_data_list for k, v in d.items()}

            # The other parameters
            post_data = {
                'access_token': PAGE_ACCESS_TOKEN,
                'published': 'false',
                'scheduled_publish_time': SCHEDULED_TIME,
                'message': post_text
            }
            print(SCHEDULED_TIME)

            # Send the POST request
            response = requests.post(url, data=post_data, files=files)
            loger.warning(response.json())
            # Print the response
            if response.status_code == 200:
                update_post_info(path=post_path, social=social, value=True)
                return True
            else:
                loger.warning(f'Failed to schedule the post. (planned) Response:\n{response.json()}')
                return False
        except facebook.GraphAPIError:
            loger.warning('facebook.GraphAPIError\n Continue in 20 minutes')
            await asyncio.sleep(1200)
            await post_facebook_planned(acc_token, images, post_text, page_name)
        except Exception as e:
            loger.warning(f'Failed to schedule the post. (planned) Error\n{e}')
            raise e
        finally:
            for image_path in image_path_list:
                os.remove(image_path)

    if check_if_post_exists(path=post_path, social=social):
        loger.warning(f'{post_path} post already exists')
        return False

    post_text, images = await get_post_data_by_path(post_path, social)
    image_path_list = []
    for image in images:
        photo_path = download_photo(image)
        image_path_list.append(photo_path)

    result = True

    if post_date <= datetime.now():
        loger.warning('Post date is in the past.')
        result = False
    elif post_date <= datetime.now() + timedelta(minutes=10):
        if await add_task(acc_token, image_path_list, post_text, page_name, task=post_facebook_immediate,
                          post_date=post_date,
                          trigger='date'):
            loger.warning(f'{post_path}\n{post_date.strftime("%m/%d/%Y, %H:%M:%S")}\n{social} (immediate)\n')
            record_post_info(path=post_path, social=social, date=post_date)
    else:
        if await post_facebook_planned(acc_token, image_path_list, post_text, page_name):
            loger.warning(f'{post_path}\n{post_date.strftime("%m/%d/%Y, %H:%M:%S")}\n{social} (planned)\n')
            record_post_info(path=post_path, social=social, date=post_date, published=True)
    return result


async def add_task_facebook_old(post_path: str,
                                post_date: datetime,
                                page_name: str,
                                acc_token: str):
    social = 'Facebook'

    async def post_facebook_immediate(acc_token: str, image_path: str, post_text: str, page_name: str):
        try:
            # Set name of the pages where we want to post
            page = get_page(acc_token, page_name)
            graphPage = facebook.GraphAPI(page['access_token'])
            # Upload the image
            image_data = {
                'file': open(image_path, 'rb')
            }
            graphPage.put_photo(image=image_data, album_path='me/photos', message=post_text)

            update_post_info_old(path=post_path, social=social, value=True)
        except Exception as e:
            loger.warning(f'Error in post_facebook_immediate \n{e}')
            raise e

    async def post_facebook_planned(acc_token: str, image_path: str, post_text: str, page_name: str):
        ACC_ACCESS_TOKEN = acc_token
        try:
            # The Facebook ID of the page to post on
            page = get_page(acc_token, page_name)

            GET_TOKEN_URL = f'https://graph.facebook.com/{page["id"]}?fields=access_token&access_token={ACC_ACCESS_TOKEN}'

            # The page access token from Facebook App
            PAGE_ACCESS_TOKEN = requests.get(url=GET_TOKEN_URL).json()['access_token']

            # Scheduled time in the future
            SCHEDULED_TIME = int(post_date.timestamp())

            # The Graph API endpoint for photos
            url = f'https://graph.facebook.com/{page["id"]}/photos'

            # The image to post
            image_data = {
                'file': open(image_path, 'rb')
            }

            # The other parameters
            post_data = {
                'access_token': PAGE_ACCESS_TOKEN,
                'published': 'false',
                'scheduled_publish_time': SCHEDULED_TIME,
                'message': post_text
            }
            print(SCHEDULED_TIME)

            # Send the POST request
            response = requests.post(url, data=post_data, files=image_data)
            loger.warning(response.json())
            # Print the response
            if response.status_code == 200:
                update_post_info_old(path=post_path, social=social, value=True)
                return True
            else:
                loger.warning(f'Failed to schedule the post. (planned) Response:\n{response.json()}')
                return False
        except facebook.GraphAPIError:
            loger.warning('facebook.GraphAPIError\n Continue in 20 minutes')
            await asyncio.sleep(1200)
            await post_facebook_planned(acc_token, image, post_text, page_name)
        except Exception as e:
            loger.warning(f'Failed to schedule the post. (planned) Error\n{e}')
            raise e

    if check_if_post_exists_old(path=post_path, social=social):
        loger.warning(f'{post_path} post already exists')
        return False

    post_text, image = await get_post_data_by_path_old(post_path, social)

    result = True

    if post_date <= datetime.now():
        loger.warning('Post date is in the past.')
        result = False
    elif post_date <= datetime.now() + timedelta(minutes=10):
        if await add_task(acc_token, image, post_text, page_name, task=post_facebook_immediate,
                          post_date=post_date,
                          trigger='date'):
            loger.warning(f'{post_path}\n{post_date.strftime("%m/%d/%Y, %H:%M:%S")}\n{social} (immediate)\n')
            if record_post_info_old(path=post_path, social=social, date=post_date):
                print('Recorded')
            else:
                print('Failed to Record')
    else:
        if await post_facebook_planned(acc_token, image, post_text, page_name):
            loger.warning(f'{post_path}\n{post_date.strftime("%m/%d/%Y, %H:%M:%S")}\n{social} (planned)\n')
            if record_post_info_old(path=post_path, social=social, date=post_date, published=True):
                print('Recorded')
            else:
                print('Failed to Record')
    return result
