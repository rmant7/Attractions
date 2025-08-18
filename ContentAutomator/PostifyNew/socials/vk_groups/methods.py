import asyncio
import re
from datetime import datetime, timedelta
import json
import logging
import os
import aioschedule
import facebook
import requests
from PIL import Image
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from instagrapi import Client


# Asynchronous function to add a task to the scheduler
async def add_task(*args, task, post_date, trigger='date'):
    scheduler = AsyncIOScheduler()

    try:
        scheduler.add_job(task, args=args, trigger=trigger, run_date=post_date)
        scheduler.start()
        return True
    except Exception as e:
        raise e


# Retrieve the Facebook page object using the access token and page name
def get_page(acc_token, page_name):
    graph = facebook.GraphAPI(acc_token)
    accounts = graph.get_connections('me', 'accounts')
    page = None
    for account in accounts['data']:
        if account['name'] == page_name:
            page = account
    return page


def get_hashtags(json_data: dict):
    # Extract hashtags, name, and location from the JSON data

    def process_strings(string_list):
        processed_list = []
        for string in string_list:
            words = string.split()
            processed_words = []
            for i, word in enumerate(words):
                if i > 0 and word.isalpha():
                    word = word.capitalize()
                processed_words.append(re.sub(r'[^\w\s]', '', word))
            processed_list.append(''.join(processed_words))
        return processed_list

    hashtags = ' '.join([hashtag for hashtag in json_data['hashtags']])
    name_raw = [item.capitalize() for item in (json_data['name'].split(' '))]
    locations_list_raw = [item.capitalize() for item in (json_data['location'].split(', '))]
    locations_list = process_strings(locations_list_raw)
    names_list = process_strings(name_raw)

    name = '#' + ''.join(names_list)
    locations_str = '#' + ' #'.join(locations_list) + ' ' + name
    return locations_str, hashtags


def get_hashtags_old(json_data: dict):
    # Extract hashtags, name, and location from the JSON data

    def process_strings(string_list):
        processed_list = []
        for string in string_list:
            words = string.split()
            processed_words = []
            for i, word in enumerate(words):
                if i > 0 and word.isalpha():
                    word = word.capitalize()
                processed_words.append(re.sub(r'[^\w\s]', '', word))
            processed_list.append(''.join(processed_words))
        return processed_list

    hashtags = ' '.join([hashtag for hashtag in json_data['hashtags']])
    locations_list_raw = [item.capitalize() for item in (json_data['location'].split(', '))]
    locations_list = process_strings(locations_list_raw)
    # print(locations_list)

    locations_str = '#' + ' #'.join(locations_list)
    return locations_str, hashtags


# Get the text and image bytes from the provided JSON data and path
def get_text_image_bytes(json_data: dict, path: str):
    try:
        footer = 'Больше о нас:\nhttps://cheaptrip.guru'

        location, hashtags = get_hashtags(json_data)

        # Generate the text using location, JSON text, footer, and hashtags
        text = location + '\n' + json_data["text"] + '\n\n' + footer + '\n\n' + hashtags
        images = []

        image_url_list = json_data['images']
        for image_url in image_url_list:
            # Fetch the image content from the URL and append to the images list
            response = requests.get(image_url, stream=True)
            images.append(BytesIO(response.content))

        return text, images
    except Exception as e:
        logging.warning(f'Error. {e}, \n {path}')
        raise e


def cut_text(text: str, additional_chars: int, char_limit: int) -> str:
    """
    Cut text message by message from end to char limit

    :param text: some text
    :param additional_chars: count of chars for geolocation/links/hashtags
    :param char_limit: max count of chars
    :return: cutted text
    """
    text_len = len(text)
    text_paragraphs = text.split("\n")

    splited_text = list(map(lambda x: re.split(r'(?<=[.?!])\s+', x), text_paragraphs))

    for i in range(len(splited_text) - 2, 0, -1):
        for j in range(len(splited_text[i]) - 1, -1, -1):
            deleted_text = splited_text[i].pop(j)
            text_len -= len(deleted_text)

            if text_len + additional_chars + 10 < char_limit:
                break
        if text_len + additional_chars + 10 < char_limit:
            break

    result_text = "\n".join(list(map(lambda x: " ".join(x), splited_text)))

    return result_text


# Get the text and images from the provided JSON data and path
def get_text_images(json_data: dict, path: str, social: str):
    footers = {
        'Vkontakte': """Узнай больше на
https://cheaptrip.guru

#cheaptrip #cheaptripguru #бюджетноепутешествие #экономичныепутешествия #бюджетныйтуризм #путешествиенахаляву #дешевыепоездки #сэкономитьнапутешествии #бюджетноепутешествиепо #бюджетныйотдых #путешествиядешево""",
        'Facebook': """Больше о нас:\nhttps://cheaptrip.guru""",
        'Instagram': """Больше о нас:\nhttps://cheaptrip.guru"""
    }
    try:
        footer = footers[social]

        location, hashtags = get_hashtags(json_data)

        # Generate the text using location, JSON text, footer, and hashtags
        inner_text = json_data['text']

        if social == "Instagram":
            addition_chars = len(location) + len(footer) + len(hashtags)
            inner_text = cut_text(inner_text, addition_chars, 2200)

        text = location + '\n' + inner_text + '\n\n' + footer + '\n\n' + hashtags
        images = []

        image_url_list = json_data['images']
        for image_url in image_url_list:
            parsed = urlparse(image_url)
            path = parsed.path[1:]
            images.append(path)

        return text, images
    except Exception as e:
        logging.warning(f'Error. {e}, \n {path}')


# Read files from the path, structure them, and return the text and photos ready for publication
def get_post_data_by_path(path: str, social: str):
    try:
        with open(f'{path}', 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(data)
        return get_text_images(json_data=data, path=path, social=social)
    except Exception as e:
        logging.warning(f'Error. {e}, \n {path}')
        raise e


async def get_post_data_by_path_old(path: str, social: str):
    try:
        with open(f'{path}/text.json', 'r') as f:
            text, image = get_text_images_old(json_data=json.load(f), path=path, social=social)
        return text, image
    except Exception as e:
        logging.warning(f'Error. {e}, \n {path}')
        raise e


# Iterate over folders and return paths with data
async def get_data_directory(path: str, all_paths=None):
    if all_paths is None:
        all_paths = {}
    for element in os.listdir(path):
        new_path = path + '/' + element
        if os.path.isdir(new_path):
            await get_data_directory(all_paths=all_paths, path=new_path)
        else:
            if '.json' not in element:
                break

            post_path = path + '/'
            all_paths[post_path] = {}
            break
    return all_paths


# iterates over folders and return paths with data
async def get_data_directory_old(all_paths: dict, path: str):
    for element in os.listdir(path):
        new_path = path + '/' + element
        # if the element is a folder, we go deeper
        if os.path.isdir(new_path):
            await get_data_directory(all_paths=all_paths, path=new_path)
        # else if the element is a file, we save path to the file and repeating the loop
        else:
            if '.json' not in element:
                break

            post_path = path + '/'
            all_paths[post_path] = {}
            break
    return all_paths


# Get the list of JSON file names in the specified directory
async def get_json_names_list(path: str, all_paths=None):
    if all_paths is None:
        all_paths = {}
    for element in os.listdir(path):
        if '.json' not in element:
            continue
        new_path = path + '/' + element
        json_path = new_path
        all_paths[json_path] = {}
    return all_paths


# Record post information to a JSON file
def record_post_info(path: str, social: str, date: datetime = datetime.now(), published=False):
    try:
        with open('utils/posts_info.json', 'r') as json_file:
            posts = json.load(json_file)
    except Exception:
        with open('utils/posts_info.json', 'w') as json_file:
            posts = {}

    fileName = path.split('/')[-2:]
    name = f'{fileName[0]}/{fileName[1]}'

    post = posts.get(name, None)

    if post:
        posts[name].append(
            {
                'social': social,
                'published': published,
                'publish_date': date.strftime('%m/%d/%Y %H:%M')
            }
        )
    else:
        posts[name] = [
            {
                'social': social,
                'published': published,
                'publish_date': date.strftime('%m/%d/%Y %H:%M')
            }
        ]

    with open('utils/posts_info.json', 'w') as output_json:
        output_json.write(json.dumps(posts, indent=4))
        return True


def update_post_info(path: str, social: str, value: bool):
    try:
        with open('utils/posts_info.json', 'r') as json_file:
            posts = json.load(json_file)
    except Exception as e:
        return e
    fileName = path.split('/')[-2:]
    strFilename = f'{fileName[0]}/{fileName[1]}'

    if strFilename in posts:
        for i in range(len(posts[strFilename])):
            if posts[strFilename][i]['social'] == social:
                posts[strFilename][i]['published'] = value

        with open('utils/posts_info.json', 'w') as output_json:
            output_json.write(json.dumps(posts, indent=4))
        return True
    return False


# Check if a post exists in the recorded post information

def check_if_post_exists(path, social=None):
    fileName = path.split('/')[-2:]
    name = f'{fileName[0]}/{fileName[1]}'

    with open('utils/posts_info.json') as json_file:
        all_posts = json.load(json_file)
        post_socials = all_posts.get(name)
        if not social:
            return True if post_socials else False
        elif post_socials:
            for post in post_socials:
                if post['social'] == social:
                    logging.warning('The post already exists!')
                    return True
        else:
            return False
    return False


def record_post_info_old(path: str, social: str, date: datetime = datetime.now(), published=False):
    try:
        with open('utils/posts_info.json', 'r') as json_file:
            posts = json.load(json_file)
    except Exception:
        with open('utils/posts_info.json', 'w') as json_file:
            posts = {}

    fileName = path.split('/')[-3:]
    name = f'{fileName[0]}/{fileName[1]}'

    post = posts.get(name, None)

    if post:
        posts[name].append(
            {
                'social': social,
                'published': published,
                'publish_date': date.strftime('%m/%d/%Y %H:%M')
            }
        )
    else:
        posts[name] = [
            {
                'social': social,
                'published': published,
                'publish_date': date.strftime('%m/%d/%Y %H:%M')
            }
        ]

    with open('utils/posts_info.json', 'w') as output_json:
        output_json.write(json.dumps(posts, indent=4))
        return True


def check_if_post_exists_old(path, social=None):
    fileName = path.split('/')[-3:]
    name = f'{fileName[0]}/{fileName[1]}'

    with open('utils/posts_info.json') as json_file:
        all_posts = json.load(json_file)
        post_socials = all_posts.get(name)
        if not social:
            return True if post_socials else False
        elif post_socials:
            for post in post_socials:
                if post['social'] == social:
                    logging.warning('The post already exists!')
                    return True
        else:
            return False
    return False


def update_post_info_old(path: str, social: str, value: bool):
    try:
        with open('utils/posts_info.json', 'r') as json_file:
            posts = json.load(json_file)
    except Exception as e:
        return e
    fileName = path.split('/')[-3:]
    strFilename = f'{fileName[0]}/{fileName[1]}'

    if strFilename in posts:
        for i in range(len(posts[strFilename])):
            if posts[strFilename][i]['social'] == social:
                posts[strFilename][i]['published'] = value

        with open('utils/posts_info.json', 'w') as output_json:
            output_json.write(json.dumps(posts, indent=4))
        return True
    return False


def get_text_images_old(json_data: dict, path: str, social: str):
    footers = {
        'Vkontakte': """Узнай больше на
https://cheaptrip.guru

#cheaptrip #cheaptripguru #бюджетноепутешествие #экономичныепутешествия #бюджетныйтуризм #путешествиенахаляву #дешевыепоездки #сэкономитьнапутешествии #бюджетноепутешествиепо #бюджетныйотдых #путешествиядешево""",
        'Facebook': """Больше о нас:\nhttps://cheaptrip.guru""",
        'Instagram': """Больше о нас:\nhttps://cheaptrip.guru"""
    }
    try:
        footer = footers[social]

        location, hashtags = get_hashtags_old(json_data)
        print(location)

        # Generate the text using location, JSON text, footer, and hashtags
        text = location + '\n' + json_data["text"] + '\n\n' + footer + '\n\n' + hashtags
        image = f'{path}/image.jpg'

        return text, image

    except Exception as e:
        logging.warning(f'Error. {e}, \n {path}')
        raise e



# Get the scheduled tasks for a Facebook page
def get_scheduled_tasks_fb(acc_token: str, page_name: str):
    page = get_page(acc_token, page_name)
    page_id = page['id']
    access_token = page['access_token']
    url = f"https://graph.facebook.com/v17.0/{page_id}/scheduled_posts"
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)

    def get_data(response_data):
        data = {}
        for item in response_data:
            data[item['id']] = {'created_time': item['created_time'].split('+')[0].replace('T', ', '),
                                'post': item['message'].split('\n')[0], 'id': item['id']}
        return data

    data = {}
    if response.status_code == 200 and response.json()['data']:
        data.update(get_data(response.json()['data']))
        while 'next' in response.json()['paging']:
            response = requests.get(response.json()['paging']['next'], headers=headers)
            data.update(get_data(response.json()['data']))
        return data
    else:
        print(f"Request failed with status code {response.status_code}")


def remove_scheduled_tasks_fb(acc_token, page_name):
    posts_to_remove = get_scheduled_tasks_fb(acc_token=acc_token, page_name=page_name)

    page = get_page(acc_token, page_name)
    access_token = page['access_token']
    if not posts_to_remove:
        logging.warning('No posts_to_remove')
        return False

    for post_id in posts_to_remove:
        # Make a request to delete each scheduled post
        delete_response = requests.delete(f"https://graph.facebook.com/v17.0/{post_id}?access_token={access_token}")
        delete_data = delete_response.json()

        if "success" in delete_data and delete_data["success"]:
            print(f"Deleted post with ID: {post_id}")
        else:
            print(f"Failed to delete post with ID: {post_id}")


# Clear the scheduled tasks
async def clear_tasks():
    aioschedule.clear()


# Get file names from a link
async def get_names_from_link(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')

        files = []
        for link in links:
            if '.json' in link.getText():
                files.append(link.getText())
        return files
    except Exception as e:
        logging.warning(f'Failed to parse files from the link. Error:\n{e}')


async def start_func(data_folder_path: str, start_date: datetime, interval: timedelta, task, **kwargs):
    all_paths = await get_json_names_list(path=data_folder_path)

    if start_date <= datetime.now():
        logging.warning(f'Start date in the past. {interval} HOUR ADDED')
        start_date += interval

    post_date = start_date

    for path in all_paths:
        try:
            our_task = await task(post_path=path, post_date=post_date, **kwargs)

            if our_task:
                post_date = post_date + interval
                await asyncio.sleep(1)
            else:
                continue

        except Exception as e:
            logging.error(f'\n{e}\n')
            continue

    await asyncio.sleep(post_date.timestamp() - datetime.now().timestamp())


def get_last_post_date(social):
    with open('utils/posts_info.json') as json_file:
        posts = json.load(json_file)
        posts_list = list(posts)
        posts_list.reverse()

        for post_name in posts_list:
            for post in posts[post_name]:
                if post['social'] == social:
                    return datetime.strptime(post['publish_date'], '%m/%d/%Y %H:%M')
