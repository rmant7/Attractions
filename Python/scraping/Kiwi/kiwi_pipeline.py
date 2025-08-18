import requests
import pandas as pd
from itertools import product, permutations
from kiwi_api_key import key # is it a third party module or yours from some .env?
import json
import time

ids = pd.read_csv('new_full_list_with_countries.csv') # there is a param named use_cols=[] 
                                                      # to read particular columns['city_kiwi', 'country_code', 'id_city']
ids_sub = ids[['city_kiwi', 'country_code', 'id_city']] # so this is an extra line
ids_from = ids_sub.rename(columns={'city_kiwi': 'cityFrom', 'country_code': 'countryCodeFrom', 'id_city': 'id_from'})
ids_to = ids_sub.rename(columns={'city_kiwi': 'cityTo', 'country_code': 'countryCodeTo', 'id_city': 'id_to'})

country_link = 'http://api.travelpayouts.com/data/en/countries.json'
countries_resp = requests.get(country_link)
countries_json = countries_resp.json()
countries_df = pd.DataFrame(countries_json)[['code', 'name']]
routs_list = list(product(countries_df['code'], countries_df['code'])) # returns "bad" routes like: (1, 1) (2, 2) (3, 3) etc
                                                                       # instead of product() it's better to use 
                                                                       # permutations(countries_df['code'], 2) 
                                                                       # it returns all possible pairs excluding "bad" routes
route_df = pd.DataFrame(routs_list, columns=['from_code', 'to_code'])

links_plane = ["https://api.tequila.kiwi.com/v2/search?fly_from=" + from_code + "&fly_to=" + to_code 
               + "&date_from=01%2F10%2F2023&date_to=30%2F03%2F2024&curr=EUR&vehicle_type=aircraft&limit=1000" 
               for from_code, to_code in zip(route_df['from_code'], route_df['to_code'])] # the same can be done without zip, 
                                                                                          # just: route_df[['from_code', 'to_code']]

headers = {'accepts': 'application/json', 'apikey': key}

def api_call(url):
    query = requests.get(url, headers=headers)
    if query.status_code==200:
        resp = json.loads(query.content.decode('utf-8'))
        resp_data = resp['data']
        resp_df = pd.DataFrame(resp_data)
        if len(resp_df) != 0:
            return pd.DataFrame({
            'flyFrom': resp_df['flyFrom'],
            'flyTo': resp_df['flyTo'],
            'cityFrom': resp_df['cityFrom'],
            'cityTo': resp_df['cityTo'],
            'countryFrom': pd.json_normalize(resp_df['countryFrom']).name,
            'countryTo': pd.json_normalize(resp_df['countryTo']).name,
            'countryCodeFrom': pd.json_normalize(resp_df['countryFrom']).code,
            'countryCodeTo': pd.json_normalize(resp_df['countryTo']).code,
            'distance': resp_df['distance'],
            'duration': pd.json_normalize(resp_df['duration']).total,
            'price_EUR': pd.json_normalize(resp_df['conversion']).EUR,
            'UTCarrival': resp_df['utc_arrival'],
            'UTCdeparture': resp_df['utc_departure']
            })

dataset_of_flights = pd.DataFrame()
for i in range(1, len(links_plane)): # since links_plane is already a list itself, then you may just type:
                                     # for link in links_plane:
    data = api_call(links_plane[i])  #     data = api_call(link)
    time.sleep(2.0)
    dataset_of_flights = pd.concat([dataset_of_flights, data])
    
dataset_fl = dataset_of_flights.dropna()
grouped_flights = dataset_fl.groupby(['cityFrom', 'cityTo'])
min_price_flights = grouped_flights.apply(lambda x: x.loc[x['price_EUR'].idxmin()])
min_price_flights.reset_index(drop=True, inplace=True)
    
adding_ids = pd.merge(min_price_flights, ids_from, 'left', on = ['cityFrom', 'countryCodeFrom'])
adding_ids = pd.merge(adding_ids, ids_to, 'left', on = ['cityTo', 'countryCodeTo'])
ids_na = adding_ids[adding_ids['id_from'].isna() | adding_ids['id_to'].isna()]
ids_not_na = adding_ids[adding_ids['id_from'].notna() & adding_ids['id_to'].notna()]
ids_not_na['id_from'] = ids_not_na['id_from'].astype('int')
ids_not_na['id_to'] = ids_not_na['id_to'].astype('int')
final_df = ids_not_na[['id_from', 'id_to', 'duration', 'price_EUR']]
final_df['transport_id'] = 1

final_df.to_csv("ready_to_use.csv", index = False)
ids_na.to_csv("for_me_to_work_with.csv", index = False)