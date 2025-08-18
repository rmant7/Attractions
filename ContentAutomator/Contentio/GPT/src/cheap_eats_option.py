from data_provider import CSVDataProvider
import functions 
from config import PROMPTS_DIR, OPTION_LISTS_DIR, SEO_TEXTS_DIR
import json
from pathlib import Path
from logger import logger_setup
from datetime import datetime


dp = CSVDataProvider()
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
logger = logger_setup(f'{Path(__file__).stem}_{timestamp}')


def get_cheap_eats_options():
    save_dir = Path(f'{OPTION_LISTS_DIR}/cheap_eats')
    save_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f'Making output dir...SUCCESSFULLY')
    prompts = functions.get_prompts_GPT(f'{PROMPTS_DIR}/cheap_eats.json')
    logger.info(f'Getting prompts...SUCCESSFULLY')
    j = 1
    for city, country in dp.gen_data():
        city_ = city.replace(' ', '_').replace('-', '_')
        # if city_ in [c.stem for c in save_dir.glob('*.json')]: continue
        logger.info(f'Processing {city}, {country}...')
        prompt = prompts['options'].format(city=city, country=country)
        try:
            response = functions.get_response_GPT(prompt)
            logger.info(f'Getting response...SUCCESSFULLY')
            parsed = json.loads(response)
            logger.info(f'Parsing response...SUCCESSFULLY')
            with open(Path(f'{save_dir}/{city_}.json'), 'w') as fp:
                json.dump(parsed, fp, indent=4)
            logger.info(f'Saving data...SUCCESSFULLY')
        except Exception as err:
            logger.error(f'Error: {err} while processing {city}, {country}')
            continue
        logger.info(f'Completed {city}, {country} SUCCESSFULLY. Total score: {j}/{dp.numrows}')
        j += 1


@functions.elapsed_time
def gen_content():
    category = 'cheap_eats'
    base_url = f'http://20.240.63.21/files/images/{category}'
    save_dir = Path(f'{SEO_TEXTS_DIR}/{category}')
    save_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f'Making output dir...SUCCESSFULLY')
    prompts = functions.get_prompts_GPT(f'{PROMPTS_DIR}/{category}.json')
    logger.info(f'Getting prompts...SUCCESSFULLY')
    j = 1
    for city, country in dp.gen_data():
        logger.info(f'Processing {city}, {country} started...')
        city_ = city.replace(' ', '_').replace('-', '_')
        # getting option list for the given city
        try:
            options = functions.load_json(f'{OPTION_LISTS_DIR}/{category}/{city_}.json')
            logger.info(f'Category options loading...SUCCESS')
        except Exception as err:
            logger.error(f'\t{type(err).__name__}: {err} while getting options. Continue to process with next city')
            continue
        # looping over the options
        data = dict()
        for num, option in options.items():
            logger.info(f'Processing for {num}.{option} starting...')
            data[num] = dict()
            # composing prompt for the given option
            prompt = prompts['content'].format(option=option, city=city, country=country)
            # getting response from ChatGPT
            try:
                response = functions.get_response_GPT(prompt)
                logger.info(f'Response for {num}.{option} generating...SUCCESS')
                parsed = json.loads(response)
                logger.info(f'Response for {num}.{option} parsing...SUCCESS')
            except Exception as err:
                logger.error(f'{type(err).__name__}: {err} while getting ChatGPT response. Continue to process with next option')
                del data[num]
                continue
            prompt = prompts['images'].format(text=parsed['text'])
            try:
                url = functions.get_images_DALLE(prompt)
                logger.info(f'Image of option {num}.{option} generating...SUCCESS')
                img_name = functions.download_image(url[0], category, city, num, option)
                logger.info(f'Image of option {num}.{option} saving...SUCCESS')
            except Exception as err:
                logger.error(f'{type(err).__name__}: {err} while generating or downloading image. Continue to process with next option')
                del data[num]
                continue
            # Compose a data[num] subdict
            data[num]['name'] = option
            data[num]['location'] = f'{city}, {country}'
            data[num]['meta'] = parsed['meta']
            data[num]['keywords'] = parsed['keywords'].split(', ')
            data[num]['title'] = parsed['title']
            data[num]['text'] = parsed['text']
            data[num]['links'] = [link for link in parsed['links'] if functions.is_valid_link(link)]
            data[num]['images'] = [f'{base_url}/{city_}/{img_name}']
            logger.info(f'Option {option} adding...SUCCESS')
        # saving data dict to json
        with open(Path(f'{save_dir}/{city_}.json'), 'w') as fp:
            json.dump(data, fp, indent=4)
        logger.info(f'Processing {city}, {country} completed SUCCESSFULLY. Total score {j}/{dp.get_numrows()}')
        j += 1        
                
      
def get_missing_cities():
    category = 'cheap_eats'
    base_url = f'http://20.240.63.21/files/images/{category}'
    for city, _ in dp.gen_data():
        city_ = city.replace(' ', '_').replace('-', '_')
        content = functions.load_json(f'{SEO_TEXTS_DIR}/{category}/{city_}.json')
        for key in content.keys():
            option = content[key]['images'][0].split('/')[-1]
            content[key]['images'] = [f'{base_url}/{city_}/{option}']
        with open(f'{SEO_TEXTS_DIR}/{category}/{city_}.json', 'w') as fp:
            json.dump(content, fp, indent=4)
    
    
            
if __name__ == '__main__':
    # gen_content()
    get_missing_cities()
    pass