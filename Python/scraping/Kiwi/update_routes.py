#!/home/azureuser/ChipTripData/Python/scraping/Kiwi/.venv38/bin/python3.8
import pandas as pd
from pathlib import Path
import traceback
from datetime import date


from config import OUTPUTS_DIR, ROUTES_PATH, EXTRACTED_ROUTES_FILE_NAME
from logger import logger_setup


logger = logger_setup(Path(__file__).stem, 'w')


def merge_routes(source: str):
    columns_names = ('path_id', 'from_id', 'to_id', 'transport_id', 'price_EUR', 'duration_min')
    dict_dtypes = {k:'Int32' for k in columns_names} # allows to save data as integer not as float (by default)
    
    df_routes = pd.read_csv(Path(ROUTES_PATH), usecols=columns_names, dtype=dict_dtypes)
    df_extracted_routes = pd.read_csv(Path(f'{OUTPUTS_DIR}/{source}/{EXTRACTED_ROUTES_FILE_NAME}'), usecols=columns_names, 
                                      dtype=dict_dtypes)
    
    # updating via merge and following combine_first
    df_merged = pd.merge(df_routes, df_extracted_routes, how='outer', on=['from_id', 'to_id', 'transport_id'])
    df_merged['price_EUR'] = df_merged['price_EUR_y'].combine_first(df_merged['price_EUR_x'])
    df_merged['duration_min'] = df_merged['duration_min_y'].combine_first(df_merged['duration_min_x'])
    df_merged['path_id'] = df_merged['path_id_y'].combine_first(df_merged['path_id_x'])
    df_merged.drop(['price_EUR_x', 'price_EUR_y', 'duration_min_x', 'duration_min_y', 'path_id_x', 'path_id_y'], axis=1, inplace=True)
    df_merged.sort_values(by=['from_id', 'to_id', 'transport_id', 'price_EUR'], ascending=True, inplace=True)
    df_merged.drop_duplicates(['from_id', 'to_id', 'transport_id'], inplace=True)
    df_merged.drop(df_merged.query('from_id == to_id').index, inplace=True)
    
    df_merged = df_merged[['path_id', 'from_id', 'to_id', 'transport_id', 'price_EUR', 'duration_min']]    
    
    print(df_merged)
    df_merged.to_csv(Path(f'{OUTPUTS_DIR}/{source}/routes_upd_{date.today().strftime("%d%m%y")}.csv'), index=False)


def del_same_id():
    df_routes_upd = pd.read_csv('/home/azureuser/ChipTripData/Python/scraping/Kiwi/outputs/run_2/routes_upd_250124.csv')
    df_same_id = df_routes_upd.query('from_id == to_id')
    print(df_same_id)


def main():
    merge_routes()


if __name__ == '__main__':
    main()
    

    
  
    