import pandas as pd
import json
from time import perf_counter
from pathlib import Path

from functions import get_response_GPT, get_prompts_GPT, elapsed_time, is_valid_link, get_cities, get_city_id
from config import PROMPTS_DIR, SEO_CITY_DESCRIPTIONS_DIR, IMG_DIR
from logger import logger_setup


logger = logger_setup(Path(__file__).stem)


@elapsed_time
def complete_seo_description():
    prompts_path = Path(f'{PROMPTS_DIR}/city_descriptions_pmt.json')
    img_dir = Path(f'{IMG_DIR}/city_descriptions')
    base_url = 'http://20.240.63.21/files/images/city_descriptions'
    missing = {'cities':[]}
    # with open('missing_cities.json', 'r') as f:
    #     missing_cities = json.load(f)
    for json_ in SEO_CITY_DESCRIPTIONS_DIR.glob('*.json'):
        with open(json_, 'r') as f:
            json_content = json.load(f)
        prompts = get_prompts_GPT(prompts_path)
        try:
            response = json.loads(get_response_GPT(prompts['city_description'].format(description=json_content['description'])))
            for k, v in response.items(): json_content[k] = v
            if not is_valid_link(json_content['link']): json_content['link'] = ''
            json_content['images'] = [f'{base_url}/{json_.stem}/{image.name}' 
                                      for image in list(Path(f'{img_dir}/{json_.stem}').glob("*.jpg"))]
            with open(json_, 'w') as f:
                json.dump(json_content, f, indent=4)
        except Exception as err:
            print('\nSomething went wrong: ', err)
            missing['cities'].append(json_.stem)
            continue
    with open('missing_cities', 'w') as f:
        json.dump(missing, f, indent=4)


@elapsed_time
def add_directions():
    cities = get_cities()
    logger.info('Getting list of cities...SUCCESS')
    prompts_path = Path(f'{PROMPTS_DIR}/city_descriptions_pmt.json')
    prompts = get_prompts_GPT(prompts_path)
    logger.info('Prompts loading...SUCCESS')
    j = 0
    for city in cities:
        city_ = city.replace('-', '_').replace(' ', '_')
        logger.info(f'Starting {city}...')
        try:
            descr_path = f'{SEO_CITY_DESCRIPTIONS_DIR}/{city_}.json'
            with open(descr_path, 'r') as fp:
                content = json.load(fp)
                logger.info(f'Loading {descr_path}...SUCCESS')
            prompt = prompts['popular_directions'].format(city=city, city_list=[c for c in cities if c != city])    
            response = json.loads(get_response_GPT(prompt))
            logger.info(f'Getting response from ChatGPT...{response}...SUCCESS')
            content['destinations_id'] = [get_city_id(c) for c in response['destinations_id']]
            logger.info(f'Adding the key "destinations_id":{content["destinations_id"]} for {city}...SUCCESS')
            with open(descr_path, 'w') as fp:
                json.dump(content, fp, indent=4)
        except FileNotFoundError as err:
            logger.error(f'There was an error while processing {city}: {err}')
            continue
        except Exception as err:
            logger.error(f'An unexpected error occurred: {err}')
            continue
        logger.info(f'Completed {city}...SUCCESS, total score {j + 1}/{len(cities)}')
        j += 1
        

if __name__ == '__main__':
    # complete_seo_description()
    add_directions()