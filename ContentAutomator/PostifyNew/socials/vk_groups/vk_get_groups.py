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


def get_user_groups(user_id):
    """Получаем список групп конкретного пользователя по его id"""
    user_params = {
        'user_id': user_id,
        'extended': 0,
        **auth_params
    }
    response = requests.get(url + 'groups.get', params=user_params)
    user_groups = response.json()['response']['items']
    return user_groups


def user_groups_info(user_id):
    """Получаем информацию о группах конкретного пользователя"""
    for group in get_user_groups(user_id):
        item = group_info(group)
        if item['can_post']:
            print(f"Название: '{item['name']}', закрытое: {'да' if item['is_closed'] else 'нет'}")


def group_info(group_id):
    """Получаем информацию о группе по ее id.
    can_post - Информация о том, может ли текущий пользователь оставлять записи на стене сообщества: 1 - может, 0 - нет
    """
    fields = ['can_post', 'can_suggest', 'members_count']  # , 'country', 'city', 'description', 'fixed_post']
    params = {
        'group_id': group_id,
        'fields': ', '.join(fields),
        **auth_params
    }
    response = requests.get(url + 'groups.getById', params=params)
    data = response.json().get('response', [])[0]
    return data


def groups_search():
    """Поиск групп по ключевой строке 'q'"""
    fields = ['can_post', 'can_suggest', 'members_count']
    params = {
        'type': 'group',
        'q': 'euro-trip',
        'fields': ', '.join(fields),
        **auth_params
    }
    response = requests.get(url + 'groups.search', params=params)
    data = response.json()['response']
    return data


def find_groups_from_search():
    """Записываем найденные группы в файл 'groups_can_post_new.txt'"""
    with open('groups/groups_can_post_new.txt', 'w', encoding='utf-8') as file1:
        data = groups_search()['items']
        for group in data:
            if group['can_post'] and group['members_count'] > 1000:
                file1.write(f"{group['id']} {group['name']}\n")
                pprint({'name': group['name'], 'can_post': group['can_post'], 'members_count': group['members_count']})

    groups_id = ['44058644\n']
    with open('groups/groups_can_post_new.txt', 'r', encoding='utf-8') as inp_file, \
            open('groups/groups_can_post.txt', 'w', encoding='utf-8') as out_file:
        for line in inp_file.readlines():
            gr = re.findall(r'\d+', line)[0]
            if gr not in groups_id:
                groups_id.append(gr + '\n')
        out_file.writelines(groups_id)


def find_groups_from_id():
    """Поиск групп 'вручную' по id группы"""
    with open('groups/groups_can_post.txt', 'a', encoding='utf-8') as file1, \
            open('groups/groups_can_suggest.txt', 'a', encoding='utf-8') as file2:
        while True:
            group_id = input('Введите id: ')
            if group_id == 'stop':
                break
            res = group_info(group_id)
            if res['can_post']:
                file1.write(f"{res['id']}\n")
            elif res['can_suggest']:
                file2.write(f"{res['id']}\n")


if __name__ == '__main__':
    find_groups_from_search()