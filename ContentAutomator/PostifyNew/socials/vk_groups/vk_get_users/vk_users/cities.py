from vk_users.vk_users_db import (
    get_city_by_id,
    add_city_to_db,
    )
from vk_users.requests_to_vk import get_cities_info


def main():
    cities = get_cities_info()
    for city in cities:
        # check if city is already added to the db
        if not get_city_by_id(city['id']):
            add_city_to_db(city)
            print('New city added!')

    print('finished')


if __name__ == '__main__':
    main()
