import vk_api
import time


# Создаёт сессию, получает аргументом токен пользователя
def create_session(token):
    session = vk_api.VkApi(token=token)
    vk = session.get_api()

    return vk


# Поиск юзеров по городам
def search_users(token, city_name):
    vk = create_session(token=token)

    search_response = vk.users.search(
        city=city_name,
        can_write_private_message=1,
        v='5.131'  # используйте актуальную версию API на момент использования
    )

    return search_response['items']


# Получаем ID стран по идентификаторам
def get_countries(token):
    vk = create_session(token=token)

    search_response = vk.database.getCountries(
        need_all=1,
        # https://dev.vk.com/reference/country-codes - идентификаторы
        code='GB,DE,PL',
        count=1000,  # максимальное количество стран за один запрос
        v='5.131'
    )

    return search_response['items']


# Получаем ID города (нужен id страны и название города.
# Пример: get_city_id(token=token, country_id=49, city_name='London')
def get_city_id(token, country_id, city_name):
    vk = create_session(token=token)

    search_response = vk.database.getCities(
        country_id=country_id,
        q=city_name,
        need_all=1,
        v='5.131'
    )

    for city in search_response['items']:
        if city['title'].lower() == city_name.lower():
            return city['id']

    return None  # Если город не найден


# ищем жителей по городам. Нужен id города Пример: search_by_city(token=token, city_name=295)
def search_by_city(token, city_name, count=1000):
    session = vk_api.VkApi(token=token)
    vk = session.get_api()

    users = []
    offset = 0

    while True:
        search_response = vk.users.search(
            city=city_name,
            sex=2, # 2-мужчины, 1-женщины
            age_from=0,
            age_to=50,
            can_write_private_message=1,
            count=count,
            offset=offset,
            v='5.131'  # используйте актуальную версию API на момент использования
        )
        if not search_response['items']:
            break  # Если не осталось результатов, прекращаем поиск
        users.extend(search_response['items'])
        offset += count
        time.sleep(0.3)  # Необходимая задержка между запросами, чтобы не превысить лимиты API

    return users


# Ищем жителей по дням рождения. Принимает дату, месяц, год.
# Пример: search_by_birthday(token=token, birth_day=5, birth_month=8, birth_year=1990)
def search_by_birthday(token, birth_day, birth_month, birth_year, count=1000):
    session = vk_api.VkApi(token=token)
    vk = session.get_api()

    users = []
    offset = 0

    while True:
        search_response = vk.users.search(
            can_write_private_message=1,
            birth_day=birth_day,  # День рождения
            birth_month=birth_month,  # Месяц рождения
            birth_year=birth_year,  # Год рождения
            count=count,
            offset=offset,
            v='5.131'
        )
        if not search_response['items']:
            break  # Если не осталось результатов, прекращаем поиск
        users.extend(search_response['items'])
        offset += count
        time.sleep(0.3)  # Необходимая задержка между запросами, чтобы не превысить лимиты API

    return users






