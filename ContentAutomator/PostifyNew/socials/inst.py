import logging
import os
import re
from datetime import datetime

import requests
from pathlib import Path
from io import BytesIO

from instagrapi import Client
from instagrapi.types import Location
from PIL import Image

from geopy.geocoders import Nominatim
from utils.methods import get_post_data_by_path, update_post_info, check_if_post_exists, add_task, record_post_info

NAME_PATTERN = r"\/\d+_(\w+).jpg"

geolocator = Nominatim(user_agent=__name__)


def account_authentication(username: str, password: str) -> Client:
    """
    Login user on Instagram by username and password
    :param username: Instagram username
    :param password: Instagram user password
    :return: instance of Client
    """

    cl = Client()
    settings_file = Path(f"settings_{username}.json")

    if settings_file.is_file():
        cl.load_settings(settings_file)

    cl.login(username=username, password=password)

    if not settings_file.is_file():
        cl.dump_settings(settings_file)

    return cl


def _upload_photo(client: Client, image_path: Path, text: str, location: Location) -> None:
    """
    Upload photo on Instagram
    :param client: logined user
    :param image_path: path to image
    :param text: message
    :param location: geolocation
    :return: None
    """

    client.photo_upload(
        path=image_path,
        caption=text,
        location=location,
        extra_data={
            'custom_accessibility_caption': 'alt text example',
            'like_and_view_counts_disabled': False,
            'disable_comments': False,
        }
    )


def _upload_album(client: Client, image_paths: list, text: str, location: Location) -> None:
    """
    Upload album on Instagram
    :param client: logined user
    :param image_paths: list of paths to images
    :param text: message
    :param location: geolocation
    :return: None
    """

    client.album_upload(
        paths=image_paths,
        caption=text,
        location=location,
        extra_data={
            'custom_accessibility_caption': 'alt text example',
            'like_and_view_counts_disabled': False,
            'disable_comments': False,
        }
    )


def _download_photo(url: str) -> Path:
    """
    Download photo by url ,and save
    :param url: link on photo
    :return: path to downloaded image
    """

    image = Image.open(BytesIO(requests.get(url).content))

    match = re.search(NAME_PATTERN, url)

    if match:
        file_name = match.group(1)
        file_path = Path(f"{file_name}.jpg")
    else:
        file_path = Path(url[url.rindex("/") + 1:])

    image.save(file_path)

    return file_path


async def make_post(client: Client, post_path: str, location_name=None) -> bool:
    """
    Takes data for post and create post like client on Instagram
    :param client: logined user, by 'account_authenticate' function
    :param post_path: path to post
    :param location_name: Name of place(city and country) for geolocation
    :return: None
    """

    text, image_list = await get_post_data_by_path(post_path, social='Instagram')

    image_paths = []
    for image in image_list:
        file_path = _download_photo(image)

        image_paths.append(file_path)

    location = None
    if location_name:
        location_title = image_paths[0].stem
        location_name = location_name[location_name.rindex(','):]

        location_data = geolocator.geocode(location_title + location_name, language="ru,en")
        location_name = location_data.address[:location_data.address.index(",")]

        location = Location(name=location_name, lat=location_data.latitude, lng=location_data.longitude)

    if len(image_paths) == 0:
        raise ValueError("List of links is empty")
    elif len(image_paths) == 1:
        _upload_photo(client, image_paths[0], text, location)
    else:
        _upload_album(client, image_paths, text, location)

    for path in image_paths:
        os.remove(path)

    update_post_info(post_path, "instagram", True)
    return True


async def add_task_instagram(post_path: str,
                             post_date: datetime,
                             client: Client):
    social = 'Instagram'

    if check_if_post_exists(path=post_path, social=social):
        logging.warning(f'{post_path} post already exists')
        return False

    if post_date <= datetime.now():
        logging.warning('Post date is in the past.')
        return False
    else:
        await add_task(client, post_path, task=make_post, post_date=post_date,
                       trigger='date')
        logging.warning(f'{post_path}\n{post_date.strftime("%m/%d/%Y, %H:%M:%S")}\n{social} (immediate)\n')
        record_post_info(path=post_path, social=social, date=post_date)
        return True
