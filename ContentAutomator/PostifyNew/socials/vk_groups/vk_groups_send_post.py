from datetime import datetime
import logging
import requests
import os
import re
import json
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
from io import BytesIO

from methods import get_post_data_by_path, check_if_post_exists, record_post_info, update_post_info

NAME_PATTERN = r"\/\d+_(\w+).jpg"


class ApiData:
    API_URL = 'https://api.vk.com/method/'
    PIC_UPLOAD_ON_SERVER = 'photos.getWallUploadServer'
    PIC_SAVE_BEFORE_POST = 'photos.saveWallPhoto'
    POST_ON_WALL = 'wall.post'
    API_VERSION = 5.131


class VkApiMethods:
    def __init__(self, api_url, token,
                 api_version, user_id=None, domain=None):
        self.api_url = api_url
        self.token = token
        self.api_version = api_version
        self.user_id = user_id
        self.domain = domain

    def post_on_wall(self, post_text, owner_id, user_id, publish_date=None, images=None):
        if publish_date is not None:
            publish_date = publish_date.timestamp()
        images_list = []
        for image in images:
            images_list.append(f'photo{user_id}_{image}')
        attachments = ','.join(images_list)
        resp_post = requests.post(self.api_url + ApiData.POST_ON_WALL,
                                  params={
                                      "access_token": self.token,
                                      "owner_id": owner_id,
                                      "message": post_text,
                                      "publish_date": publish_date,
                                      "attachments": attachments,
                                      "v": self.api_version,
                                      "from_group": 0
                                  }
                                  )
        print('resp_post', resp_post)
        return True if resp_post.status_code == 200 else False

    def get_upload_url(self):
        response_json = requests.post(self.api_url + ApiData.PIC_UPLOAD_ON_SERVER,
                                      params={
                                          "access_token": self.token,
                                          "v": self.api_version,
                                      }
                                      ).json()
        try:
            upload_url = response_json["response"]["upload_url"]
            return upload_url
        except KeyError as e:
            logging.warning(f'Error\n{response_json}')
            raise e

    @staticmethod
    def send_pic_to_url(upload_url, image_path):
        image_path = os.path.join(image_path)
        file = {"file1": open(f"{image_path}", "rb")}
        response_photo = requests.post(upload_url, files=file).json()
        return (response_photo["photo"],
                response_photo["server"],
                response_photo["hash"])

    def save_photo_before_post(self, photo, server, photo_hash):
        save_photo = requests.post(self.api_url + ApiData.PIC_SAVE_BEFORE_POST,
                                   params={
                                       "access_token": self.token,
                                       "v": self.api_version,
                                       "user_id": self.user_id,
                                       "photo": photo,
                                       "server": server,
                                       "hash": photo_hash
                                   }
                                   ).json()
        try:
            return (save_photo["response"][0]["owner_id"],
                    save_photo["response"][0]["id"],
                    save_photo["response"][0]["sizes"][5]["url"])
        except KeyError:
            logging.warning(f'Error:\n{save_photo}')


def add_post_with_pic(token, owner_id, post_path, post_date=None):
    print('!')
    post_text, images = get_post_data_by_path(post_path, social='Vkontakte')
    image_path_list = []
    for image in images:
        photo_path = download_photo(image)
        image_path_list.append(photo_path)

    account = VkApiMethods(api_url=ApiData.API_URL,
                           token=token,
                           api_version=ApiData.API_VERSION)

    # получаем url загрузки, создавая при этом экземпляр VkApiMethods
    upload_url = account.get_upload_url()
    print(upload_url)
    photo_id_list = []
    user_id = ''
    for image_path in image_path_list:
        photo, server, photo_hash = account.send_pic_to_url(upload_url=upload_url, image_path=image_path)

        user_id, photo_id, url = account.save_photo_before_post(photo=photo,
                                                                server=server,
                                                                photo_hash=photo_hash)
        photo_id_list.append(photo_id)
    task = account.post_on_wall(post_text=post_text, owner_id=owner_id,
                                user_id=user_id, publish_date=post_date, images=photo_id_list)
    print(task)
    if task:
        update_post_info(path=post_path, social='Vkontakte', value=True)
    for image_path in image_path_list:
        os.remove(image_path)
    return task


def download_photo(url: str) -> Path:
    host = 'http://20.240.63.21/'
    url = host + url
    image = Image.open(BytesIO(requests.get(url).content))

    match = re.search(NAME_PATTERN, url)

    if match:
        file_name = match.group(1)
        file_path = Path(f"{file_name}.jpg")
    else:
        file_path = Path(url[url.rindex("/") + 1:])
        print(file_path, ' saved')
    image.save(file_path)

    return file_path


async def add_task_vk(token, owner_id, post_path, post_date=None):
    social = 'Vkontakte'

    if check_if_post_exists(path=post_path, social=social):
        logging.warning(f'{post_path} post already exists')
        return False
    elif post_date <= datetime.now():
        logging.warning('Post date is in the past.')
        return False
    else:
        await add_post_with_pic(token=token, owner_id=owner_id, post_path=post_path,
                                post_date=post_date)

        logging.warning(f'{post_path}\n{post_date.strftime("%m/%d/%Y, %H:%M:%S")}\n{social} (planned)\n')
        record_post_info(path=post_path, social=social, date=post_date, published=True)
        return True

load_dotenv()
token = os.getenv('VK_GROUP_TOKEN')
my_token = os.getenv('MY_TOKEN')


with open('801.json', encoding='utf-8') as file:
    print(json.load(file))
get_post_data_by_path('801.json', social='Vkontakte')

add_post_with_pic(token=token, owner_id='-63731512', post_path='801.json')
download_photo('/files/images/city_attractions/Tehran/1_Golestan_Palace.jpg')