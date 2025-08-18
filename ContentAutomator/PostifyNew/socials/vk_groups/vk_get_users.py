import os
from dotenv import load_dotenv
from datetime import datetime
import requests
from pprint import pprint
from tqdm import tqdm
import json
import csv
import re

load_dotenv()
token = os.getenv('VK_GROUP_TOKEN')
version = os.getenv('VERSION')
# my_token = os.getenv('MY_TOKEN')

auth_params = {
    'access_token': token,
    'v': version
}

url = 'https://api.vk.com/method/'


def get_user_info(con_id):
    """Получаем информацию о пользователях конкретной страны с id = con_id"""
    method = 'users.search'
    fields = ['last_seen', 'bdate', 'sex', 'city', 'country', 'followers_count', 'contacts',
              'connections', 'can_write_private_message', 'can_post']
    user_params = {
        'country': con_id,
        'extended': 0,
        'fields': ','.join(fields),
        'sex': 2,  # 1 - women, 2 - men, 0 - not specified
        # 'count': 1000,
        'age_from': 18,
        'sort': 0,
        **auth_params
    }
    response = requests.get(url + method, params=user_params)
    return response.json()['response']


def get_code():
    """Получаем коды стран из списка стран ISO3166-1.alpha2.json"""
    res = []
    countries = 'Austria, Belgium, Bulgaria, United Kingdom, Hungary, Germany, Greece, Denmark, Ireland, Spain, Italy, ' \
                'Cyprus, Latvia, Lithuania, Luxembourg, Malta, Netherlands, Poland, Portugal, Romania, Slovakia, ' \
                'Slovenia, Finland, France, Croatia, Czech Republic, Sweden, Estonia, Montenegro, Georgia, Kosovo, ' \
                'Serbia, Armenia, Georgia, Turkey, Bosnia and Herzegovina'.split(', ')
    with open('ISO3166-1.alpha2.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        for code, country in data.items():
            # if country in countries:
            res.append(code)
    return ','.join(res)


def get_countries_code_vk():
    """Получаем список кодов vk интересующих нас стран"""
    # print(len(get_code().split(',')))
    params = {'need_all': 1,
              'code': get_code(),
              'count': 1000,
              **auth_params}
    method = 'database.getCountries'
    resp = requests.get(url + method, params=params)
    # pprint(resp.json()['response']['items'])
    # with open('countries.json', 'w', encoding='utf-8') as file:
    #     json.dump(resp.json()['response']['items'], file, ensure_ascii=False)
    # print(len(resp.json()['response']['items']))
    return resp.json()['response']['items']
    # with open('countries.json', 'r', encoding='utf-8') as file:
    #     return json.load(file)


def get_european_users(filename):
    """Получаем пользователей по странам и сохраняем в filensme (json)"""
    all_countries = {}
    res = get_countries_code_vk()
    print(res)
    for country in tqdm(res):
        con_id = country['id']
        country_title = country['title']
        print('\n', con_id, country_title)
        result = []
        for user in get_user_info(con_id):
            if user.get('can_write_private_message') and user.get('country', {}).get('id') == con_id:
                dt = user.get('bdate', '')
                bdate = '.'.join(dt.split('.')[:-1]) if len(dt.split('.')) == 3 else dt
                byear = dt.split('.')[-1] if len(dt.split('.')) == 3 else ''
                res = {
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'last_seen': datetime.fromtimestamp(user.get('last_seen', {}).get('time', 0)).strftime('%d.%m.%Y'),
                    'sex': user.get('sex', 0),
                    'id': user.get('id', ''),
                    'followers_count': user.get('followers_count', ''),
                    'country_id': user.get('country', {}).get('id', ''),
                    'country_title': user.get('country', {}).get('title', ''),
                    'city_id': user.get('city', {}).get('id', ''),
                    'city_title': user.get('city', {}).get('title', ''),
                    'bdate': bdate,
                    'byear': byear,
                    'contacts': user.get('contacts'),
                    'connections': user.get('connections'),
                    'can_write_private_message': user.get('can_write_private_message', ''),
                    'can_post': user.get('can_post', '')
                }
                result.append(res)
                all_countries.setdefault(f'{country_title}_{con_id}', []).append(res)

        # with open(f'users_{con_id}_{country_title}.json', 'w', encoding='utf-8') as file:
        #     json.dump(result, file, ensure_ascii=False, indent=3)

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(all_countries, file, ensure_ascii=False, indent=3)


def european_users_to_csv(filename):
    """Сохраняем полученные данные по пользователям в csv"""
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    cnt = 0
    name = re.sub(r'\.json', '', filename)

    with open(f"{name}.csv", "w", newline='', encoding='cp1251') as f:
        fieldnames = ['first_name', 'last_name', 'id', 'last_seen', 'sex', 'followers_count', 'country_id',
                      'country_title',  'city_id', 'city_title', 'bdate', 'byear', 'contacts', 'connections',
                      'can_write_private_message', 'can_post']
        datawriter = csv.DictWriter(f, delimiter=',', fieldnames=fieldnames)
        datawriter.writeheader()
        for country, users in data.items():
            for user in users:
                try:
                    datawriter.writerow(user)
                except UnicodeEncodeError:
                    res = {
                        'first_name': '',
                        'last_name': '',
                        'last_seen': user.get('last_seen', ''),
                        'sex': user.get('sex', 0),
                        'id': user.get('id', ''),
                        'followers_count': user.get('followers_count', ''),
                        'country_id': user.get('country', {}).get('id', ''),
                        'country_title': user.get('country', {}).get('title', ''),
                        'city_id': user.get('city', {}).get('id', ''),
                        'city_title': user.get('city', {}).get('title', ''),
                        'bdate': user.get('bdate', 0),
                        'byear': user.get('byear', 0),
                        'contacts': user.get('contacts'),
                        'connections': user.get('connections'),
                        'can_write_private_message': user.get('can_write_private_message', ''),
                        'can_post': user.get('can_post', '')
                    }
                    cnt += 1
                    datawriter.writerow(res)
        print(f'файл {name}.csv записан')
        print(f'{cnt} пользователей со сбитой кодировкой')


def count_of_european_users(filename):
    """Считаем количество найденных пользователей"""
    res = 0
    with open(filename, 'r', encoding='utf-8') as file:
        for key, val in json.load(file).items():
            res += len(val)
    return res


if __name__ == '__main__':
    # file = 'files/all_users_men.json'
    # get_european_users(file)
    # print(count_of_european_users(file))
    # european_users_to_csv(file)
    # # pprint(get_countries_code_vk())
    pprint(get_user_info(1))