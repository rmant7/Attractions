import os
from dotenv import load_dotenv
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
URL = 'https://api.vk.com/method/'


def connect():
    connect = psycopg2.connect(DATABASE_URL)
    return connect


def get_vk_users():
    with connect() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT * FROM users;')
            return cursor.fetchall()


def add_user_to_db(user):
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO users\
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
                %s, %s, %s, %s, %s);',
                           (user['id'], user['first_name'],
                            user['last_name'],
                            user.get('city', {}).get('id'),
                            user.get('country', {}).get('id'),
                            str(user['can_post']),
                            str(user['can_write_private_message']),
                            user.get('mobile_phone', ''),
                            user.get('home_phone', ''),
                            datetime.fromtimestamp(user['last_seen']['time']),
                            user.get('followers_count', 0),
                            user['sex'],  # 1-women, 2-men, 0-not specified
                            str(user['can_access_closed']),
                            str(user['is_closed']), user.get('bdate'),
                            user.get('relation')
                            # 1 — не женат (не замужем),
                            # 2 — встречается,
                            # 3 — помолвлен(-а),
                            # 4 — женат (замужем),
                            # 5 — всё сложно,
                            # 6 — в активном поиске,
                            # 7 — влюблен(-а),
                            # # 8 — в гражданском браке.
                            )
                           )


def get_user_by_id(id):
    with connect() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT * FROM users WHERE id=%s;', (id,))
            return cursor.fetchone()


def get_cities_ids():
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT id FROM cities;')
            return cursor.fetchall()


def add_users_to_db(users):
    count = 0
    for user in users:
        # check if user is already added to the db,
        # receantly online and
        # from the city from the db
        if get_user_by_id(user['id']):
            # print('user is already added to db')
            continue
        if user.get('last_seen', {}).get('time', 0) < 1704060060:
            # print('not active user')
            continue
        # if user['can_write_private_message'] != 1:
        #     # print('cannot write private messages')
        #     continue
        if user.get('city', {}).get('id') and\
           not (user.get('city', {}).get('id'),) in get_cities_ids():
            # print(f"wrong city (id = {user.get('city', {}).get('id')})")
            continue
        add_user_to_db(user)
        count += 1
    return count


def add_city_to_db(city):
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO cities\
            VALUES (%s, %s, %s, %s);',
                           (city['id'],
                            city['title'],
                            city.get('area', ''),
                            city.get('region', '')
                            )
                           )


def get_city_by_id(id):
    with connect() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT * FROM cities WHERE id=%s;', (id,))
            return cursor.fetchone()
