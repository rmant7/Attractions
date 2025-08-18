import os
from dotenv import load_dotenv
import requests
from vk_users.search_parameters import CITY_ID, CITY


load_dotenv()
TOKEN = os.getenv('VK_GROUP_TOKEN')
VERSION = os.getenv('VERSION')
AUTH_PARAMS = {
    'access_token': TOKEN,
    'v': VERSION
}
URL = 'https://api.vk.com/method/'


def get_cities_info():
    cities = CITY
    params = {'q': cities,
              'need_all': 0,
              'count': 1000,
              **AUTH_PARAMS}
    method = 'database.getCities'
    response = requests.get(URL + method, params=params)
    cities_list = response.json()["response"]["items"]
    return cities_list


def get_user_info(month, year, day=21, filter_value=''):
    """Получаем информацию о пользователях """
    method = 'users.search'
    fields = ['last_seen', 'bdate', 'sex', 'city', 'country',
              'followers_count', 'contacts', 'relation',
              'connections', 'can_write_private_message',
              'can_post', 'interests']
    user_params = {
        # 'q': filter_value,
        # 'online': 1,  # currently online
        'country_id': 1,
        'city_id': CITY_ID,
        'fields': ','.join(fields),
        'count': 1000,
        'age_from': 18,
        'sort': 1,
        # 'can_write_private_message': 1,
        # 'sex': sex,
        'birth_day': day,
        'birth_month': month,
        'birth_year': year,
        **AUTH_PARAMS
    }
    response = requests.get(URL + method, params=user_params)
    users_list = response.json()["response"]["items"]
    return users_list
