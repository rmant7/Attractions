#!/home/azureuser/ChipTripData/Python/scraping/Kiwi/.venv312/bin/python3.12
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import pandas as pd
from pathlib import Path
import requests


from functions import rate_limited, elapsed_time
from config import INPUTS_DIR, OUTPUTS_DIR, BASE_URL, HEADERS, \
                    API_LOCATIONS_SUBENTITY, API_LOCATIONS_DUMP, \
                    EXCLUDED_COUNTRIES, COUNTED_COUNTRIES, LOCATIONS_EXT_PATH
from logger import logger_setup


timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
logger = logger_setup(f'{Path(__file__).stem}')

SESSION = requests.session()


def save_json(data: dict, filename: str) -> None:
    with open(f'{OUTPUTS_DIR}/{filename}.json', 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    logger.info(f'{filename}.json saved')
            

def get_all_countries():
    try:
        response = SESSION.get(BASE_URL + API_LOCATIONS_DUMP,
                                headers=HEADERS,
                                params={
                                   'locale': 'en-US',
                                   'location_types': 'country',
                                   'limit': 300,
                                   'sort': 'name',                                
                                }
                            )
        response.raise_for_status()
        return response.json()
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')    
   
        
def gen_country_id_name_pairs():
    with open(f'{INPUTS_DIR}/kiwi_countries.json', 'r') as f:
        countries = json.load(f)
        for country in countries['locations']:
            # if country['id'] in EXCLUDED_COUNTRIES: continue
            logger.info(f'Processing: {country["id"], country["name"]}')
            yield country['id'], country['name']
    
    
def data_filter(data: dict, country_id: str) -> None:
    data['locations'] = [{k: v for k, v in item.items() if k != 'alternative_departure_points'} 
                         for item in data['locations']]
    save_json(data, country_id)
    
            
@rate_limited(limit=20, per=60)
def get_cities_by_country(country_id_name: tuple) -> None:
    country_id, country_name = country_id_name
    logger.info(f'Getting cities for: {country_name}')
    try:
        response = SESSION.get(BASE_URL + API_LOCATIONS_SUBENTITY,
                                headers=HEADERS,
                                params={
                                   'term': country_id,
                                   'location_types': 'city',
                                   'limit': 1000,
                                   'sort': 'name',                                
                                }
                            )
        response.raise_for_status()
        data_filter(response.json(), country_id)
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')


def gen_data(source: str, key_name: str) -> dict:
    for file_path in Path(source).glob('*.json'):
        with open(file_path, 'r') as jsonfile:
            data = json.load(jsonfile)
        yield data[key_name]


def gen_kiwi_locations_data() -> tuple:
    source = f'{INPUTS_DIR}/kiwi_cities_by_country'
    df_countries = pd.read_csv('/home/azureuser/ChipTripData/Python/files/csv/countries.csv', index_col='id')
    no_code = []
    for locations in gen_data(source, 'locations'):
        for location in locations:
            # if location['code'] == None:
            #     no_code.append((location['name'], location['dst_popularity_score']))
            #     print(location['name'], location['code'])
            #     continue
            if location['country']['id'] in EXCLUDED_COUNTRIES:
                continue
            country_name_query = df_countries.query('name == @location["country"]["name"]')
            if country_name_query.empty:
                continue
            data = (location['name'], 
                    location['location']['lat'], 
                    location['location']['lon'],
                    country_name_query.index.values[0],
                    location['id'],
                    location['code'])
            yield data
    # print(no_code, len(no_code))

def extend_locations():
    df_locations = pd.read_csv('/home/azureuser/ChipTripData/Python/files/csv/locations.csv', index_col='id')
    df_locations.insert(len(df_locations.columns), 'kiwi_id', None)
    df_locations.insert(len(df_locations.columns), 'kiwi_code', None)
    location_id = 1001
    accuracy = 0.5
    for city_name, lat, lon, country_id, kiwi_id, kiwi_code in gen_kiwi_locations_data():
        match_query = df_locations.query('name == @city_name and country_id == @country_id and \
                @lat - @accuracy <= latitude <= @lat + @accuracy and \
                @lon - @accuracy <= longitude <= @lon + @accuracy')
        if not match_query.empty: 
            df_locations.loc[match_query.index, ['kiwi_id', 'kiwi_code']] = kiwi_id, kiwi_code
            continue
        df_locations.loc[location_id] = city_name, lat, lon, country_id, kiwi_id, kiwi_code
        location_id += 1
    df_locations.sort_values(by=['country_id', 'name'], inplace=True)
    df_locations.to_csv(LOCATIONS_EXT_PATH)
    print(df_locations)
        
        
def same_city_same_country():
    df_locations_ext = pd.read_csv(LOCATIONS_EXT_PATH, index_col='id')
    scsc = df_locations_ext[df_locations_ext.duplicated(subset=['name', 'country_id'], keep=False)]
    scsc = scsc[scsc['kiwi_code'].isna()]
    scsc.sort_values(by=['country_id', 'name'], inplace=True)
    scsc.to_csv('/home/azureuser/ChipTripData/Python/files/csv/same_locations_ext.csv')
    print(scsc)
           
    
def match_city_names():
    df_locations = pd.read_csv('/home/azureuser/ChipTripData/Python/files/csv/locations.csv', index_col='id')
    source = f'{INPUTS_DIR}/kiwi_cities_by_country'
    diff_list = []
    accuracy = 0.05
    for locations in gen_data(source, 'locations'):
        for location in locations:
            existing_name = df_locations.query('@location["location"]["lat"] - @accuracy <= latitude <= @location["location"]["lat"] + @accuracy and \
                                          @location["location"]["lon"] - @accuracy <= longitude <= @location["location"]["lon"] + @accuracy')
            kiwi_name = location['name']
            if existing_name.empty: continue
            if existing_name['name'].values[0] != kiwi_name:
                diff_list.append((existing_name['name'].values[0], kiwi_name))
    print(diff_list, len(diff_list))
    


@elapsed_time
def main():
    try:
        logger.info('Process is started...')
        with ThreadPoolExecutor() as executor:
            executor.map(get_cities_by_country, gen_country_id_name_pairs())
        logger.info('Process is completed: SUCCESS')
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')


if __name__ == '__main__':
    # main()
    # gen_locations_csv()
    # match_city_names()
    # get_kiwi_cities()
    extend_locations()
    # same_city_same_country()