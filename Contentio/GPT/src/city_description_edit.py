from datetime import datetime
from pathlib import Path
from config import SEO_CITY_DESCRIPTIONS_DIR
import json

from data_provider import CSVDataProvider
from logger import logger_setup


dp = CSVDataProvider()
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
logger = logger_setup(f'{Path(__file__).stem}_{timestamp}')


def edit():
    for city, country in dp.gen_data():
        city_ = city.replace(' ', '_').replace('-', '_')
        
        with open(f'{SEO_CITY_DESCRIPTIONS_DIR}_copy/{city_}.json', 'r') as fp:
            content = json.load(fp)
            
        data = dict()
        data['id'] = dp.get_city_id(city)
        data['name'] = city
        data['location'] = country
        data['meta'] = content['meta']
        data['keywords'] = content['keywords']
        data['title'] = content['title']
        data['text'] = content['description']
        data['links'] = list()
        if content['link']: data['links'].append(content['link'])
        data['images'] = content['images']
        data['to_id'] = content['destinations_id']
        
        with open(f'{SEO_CITY_DESCRIPTIONS_DIR}/{city_}.json', 'w') as fp:
            json.dump(data, fp, indent=4)


if __name__ == '__main__':
    edit()