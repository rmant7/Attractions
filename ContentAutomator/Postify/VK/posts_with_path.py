import datetime as DT
import requests
import os
import json

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

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

    def post_on_wall(self, post, owner_id, user_id, publish_date=None, pic_id=None):
        if publish_date is not None:
            publish_date = date_to_unix(publish_date)

        post_path = os.path.join(DIR_PATH + '/post_1/' + post)

        with open(post_path, 'r') as f:
            json_data = f.read()
            data_dict = json.loads(json_data)
        hashtags_string = ', '.join(data_dict['hashtags'])
        text = f"{data_dict['text']} \n \n {hashtags_string} \n \n {data_dict['location']}"
        resp_post = requests.post(self.api_url + ApiData.POST_ON_WALL,
                                  params={
                                      "access_token": self.token,
                                      "owner_id": owner_id,
                                      "message": text,
                                      "publish_date": publish_date,
                                      "attachments": f'photo{user_id}_{pic_id}',
                                      "v": self.api_version,
                                      "from_group": 1
                                     }
                                  ).json()
        print(resp_post)
        return resp_post["response"]["post_id"]

    def get_upload_url(self):
        resp_url = requests.post(self.api_url + ApiData.PIC_UPLOAD_ON_SERVER,
                                 params={
                                     "access_token": self.token,
                                     "v": self.api_version,
                                 }
                                 ).json()
        print(resp_url)
        return resp_url["response"]["upload_url"]

    @staticmethod
    def send_pic_to_url(upload_url, image_name):
        image_path = os.path.join(DIR_PATH + '/post_1/' + image_name)
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
        return (save_photo["response"][0]["owner_id"],
                save_photo["response"][0]["id"],
                save_photo["response"][0]["sizes"][5]["url"])


def date_to_unix(date: str):
    dt = DT.datetime.fromisoformat(date)
    return dt.timestamp()


def add_post_with_pic(token, owner_id, post, pic_name, pub_date=None):
    # получаем url загрузки, создавая при этом экземпляр VkApiMethods
    upload_url = VkApiMethods(api_url=ApiData.API_URL,
                              token=token,
                              api_version=ApiData.API_VERSION).get_upload_url()


    photo, server, photo_hash = VkApiMethods(api_url=ApiData.API_URL,
                                             token=token,
                                             api_version=ApiData.API_VERSION).send_pic_to_url(
        upload_url=upload_url, image_name=pic_name)

    user_id, photo_id, url = VkApiMethods(api_url=ApiData.API_URL,
                                          token=token,
                                          api_version=ApiData.API_VERSION).save_photo_before_post(photo=photo,
                                                                                                  server=server,
                                                                                                  photo_hash=photo_hash)
    post_id = VkApiMethods(api_url=ApiData.API_URL,
                           token=token,
                           api_version=ApiData.API_VERSION
                           ).post_on_wall(
                           post=post, owner_id=owner_id, user_id=user_id, publish_date=pub_date, pic_id=photo_id)

    return post_id

