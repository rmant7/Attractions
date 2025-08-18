#!/home/azureuser/ChipTripData/Python/scraping/Kiwi/.venv38/bin/python3.8
from csv import writer
import gzip
import json
import pandas as pd
from pathlib import Path
import traceback


from config import OUTPUTS_DIR, COUNTRIES_PATH, TRANSPORT_TYPES_ID, EXTRACTED_ROUTES_FILE_NAME, LOCATIONS_EXT_PATH, \
                    ROUTES_PATH
from logger import logger_setup


logger = logger_setup(Path(__file__).stem, 'w')


def gen_routes_data(source: str):
    source_folder = Path(f'{OUTPUTS_DIR}/{source}')
    for file_path in (fp for fp in source_folder.rglob('*.json.gz') if fp.parent.name != 'inner_jsons_1'):
        with gzip.open(file_path, 'r') as f:
            routes = json.load(f)
        yield routes['data']


def extract_routes(source: str) -> None:
    df_locations_ext = pd.read_csv(Path(LOCATIONS_EXT_PATH), index_col='id')
    df_routes = pd.read_csv(Path(ROUTES_PATH), index_col='path_id')
    df_countries = pd.read_csv(Path(COUNTRIES_PATH), index_col='id')
    
    inner_jsons_dir = Path(f'{OUTPUTS_DIR}/{source}/inner_jsons_raw')
    inner_jsons_dir.mkdir(parents=True, exist_ok=True)
    
    from_id_unique = df_routes['from_id'].unique()
    path_id = {id: 10000 * id  if id not in from_id_unique 
               else df_routes.query('from_id == @id').index.values.max() for id in df_locations_ext.index.values}
    
    triples = set()
    csv_path = Path(f'{OUTPUTS_DIR}/{source}/{EXTRACTED_ROUTES_FILE_NAME}')
    with open(csv_path, 'w', newline='') as csvfile:
        csv_writer = writer(csvfile)
        for route_data in gen_routes_data(source):
            for route in route_data:
                try:
                    city_name_From, city_name_To = route['cityFrom'], route['cityTo']
                    country_id_From, country_id_To = (df_countries.query("name == @name").index.values[0] 
                                                      for name in (route['countryFrom']['name'], route['countryTo']['name']))
                    kiwi_code_From, kiwi_code_To = route['cityCodeFrom'], route['cityCodeTo'] 
                    
                    from_id_query = df_locations_ext.query('name == @city_name_From and country_id == @country_id_From')
                    # if from_id_query.empty: continue
                    if from_id_query.shape[0] == 1:
                        from_id = from_id_query.index.values[0]
                    else:
                        if kiwi_code_From != None:
                            from_id = from_id_query.query('kiwi_code == @kiwi_code_From').index.values[0]
                        else:
                            continue
                    
                    to_id_query = df_locations_ext.query('name == @city_name_To and country_id == @country_id_To')
                    # if to_id_query.empty: continue
                    if to_id_query.shape[0] == 1:
                        to_id = to_id_query.index.values[0]
                    else:
                        if kiwi_code_To != None:
                            to_id = to_id_query.query('kiwi_code == @kiwi_code_To').index.values[0]
                        else:
                            continue
                    
                    vehicle_id = TRANSPORT_TYPES_ID[route['route'][0]['vehicle_type']]
                    
                    if from_id == to_id or (from_id, to_id, vehicle_id) in triples: 
                        continue
                        
                    triples.add((from_id, to_id, vehicle_id))
                    
                    with gzip.open(Path(f'{inner_jsons_dir}/{path_id[from_id]}.json.gz'), 'wt', encoding='utf-8') as jsonfile:
                        json.dump(route, jsonfile, indent=4, ensure_ascii=False)
                    
                    path_id[from_id] += 1
                    price = route['price']
                    duration = route['duration']['total'] // 60                     
                    csv_writer.writerow((path_id[from_id], from_id, to_id, vehicle_id, price, duration))
                    
                except IndexError:
                    continue
    
    
def process_csv(source: str) -> None:
    csv_path = Path(f'{OUTPUTS_DIR}/{source}/{EXTRACTED_ROUTES_FILE_NAME}')
    df_extracted_routes = pd.read_csv(csv_path, header=None,
                                       names=['path_id', 'from_id', 'to_id', 'transport_id', 'price_EUR', 'duration_min'])
    df_extracted_routes.sort_values(by=['from_id', 'to_id', 'transport_id', 'price_EUR'], ascending=True, inplace=True)
    df_extracted_routes.drop_duplicates(subset=['from_id', 'to_id', 'transport_id'], inplace=True, ignore_index=True)
    df_extracted_routes.to_csv(csv_path, index=False)            
    

def main(source: str):
    extract_routes(source)
    process_csv(source)


if __name__ == '__main__':
    main('run_2')
     