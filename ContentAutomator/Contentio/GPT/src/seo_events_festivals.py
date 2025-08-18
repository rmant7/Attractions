import json
from pathlib import Path
from datetime import datetime

from logger import logger_setup
from functions import get_response_GPT, get_prompts_GPT, is_valid_link, elapsed_time
from config import PROMPTS_DIR, IMG_DIR, OPTION_LISTS_DIR, SEO_FESTIVALS_DIR
from data_provider import CSVDataProvider


timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
logger = logger_setup(f'{Path(__file__).stem}_{timestamp}')
dp = CSVDataProvider()


@elapsed_time    
def change_to():
    base_url = 'http://20.240.63.21/files/images/events_festivals'
    prompts = get_prompts_GPT(f'{PROMPTS_DIR}/events_festivals_pmt.json')
    # cities countries loop
    j = 0
    for city, country in dp.gen_data(from_=21):
        logger.info(f'Processing {city.upper()}, {country.upper()}...')
        city_ = city.replace('-', '_').replace(' ', '_')
        try:
            # getting options list for given city
            evafs_path = f'{OPTION_LISTS_DIR}/events_festivals/{city_}.json'
            with open(evafs_path, 'r') as fp:
                evafs = json.load(fp)
            logger.info(f'Events and Festivals list is retrieved for {city} successfully')
            # getting json with seo content for the same city
            seo_path = f'{SEO_FESTIVALS_DIR}_copy/{city_}.json' 
            with open(seo_path, 'r') as fp:
                seo_content = json.load(fp)
                logger.info(f'Seo content is retrieved for {city} successfully')
            data = dict()
            for number, option in evafs.items():
                logger.info(f'Starting {number}:{option}...')
                try:                 
                    # generating links
                    logger.info(f'Crafting prompt for generating links using ChatGPT...')
                    prompt = prompts['links'].format(event=option, city=city, country=country)
                    logger.info(f'Prompt crafted successfully')
                    # getting response from GPT
                    logger.info(f'Getting response from ChatGPT...')
                    response = get_response_GPT(prompt)
                    if not response:
                        logger.warning(f'No response got for {number}:{option}. No links wll be added')
                        parsed = {'links':[]}
                    else:
                        logger.info(f'Got response successfully')
                        # parsing response
                        logger.info(f'Parsing response...')
                        response = response.replace(']]', ']}').replace('}.', '}').replace('}"', '}')
                        parsed = json.loads(response)
                        logger.info(f'Response is parsed successfully')
                        logger.info(f'Links checking...')
                        parsed['links'] = [link for link in parsed['links'] if is_valid_link(link)]
                    
                    # adding all keys
                    data[number] = dict()
                    data[number]['name'] = option
                    data[number]['location'] = f'{city}, {country}'
                    data[number]['meta'] = seo_content[number]['meta']
                    data[number]['keywords'] = seo_content[number]['keywords'].split(', ')
                    data[number]['title'] = seo_content[number]['title']
                    data[number]['text'] = seo_content[number]['description']
                    data[number]['links'] = parsed['links']
                    logger.info(f"{data[number]['links']} added successfully")
                   
                    # adding images     
                    logger.info('Adding image urls...')               
                    image_path = next(Path(f'{IMG_DIR}/events_festivals/{city_}').glob(f'{number}_*.jpg'))
                    image_url = [f'{base_url}/{city_}/{image_path.name}']
                    data[number]['images'] = image_url
                    logger.info('Image urls are added successfully')
                    logger.info(f'Completed {number}: {option}...SUCCESS')
                     
                except KeyError as err:
                    logger.error(f'KeyError: {err} while {number}:{option} in {city}, {country}')
                    del data[number]
                    continue
                except AttributeError as err:
                    logger.error(f'AttributeError: {err} while {number}:{option} in {city}, {country}')
                    del data[number]
                    continue
                except TypeError as err:
                    logger.error(f'TypeError: {err} while {number}:{option} in {city}, {country}')
                    logger.error(f'data{[number]} was deleted in TypeError except')
                    del data[number]
                    continue   
                except StopIteration as err:
                    logger.error(f'{err} for {number}:{option} in {city}, {country}')
                    logger.error(f'data{[number]} was deleted in StopIteration except')
                    del data[number]
                    continue
                except json.decoder.JSONDecodeError as err:
                    # logger.error(f'Error character: " {response[err.colno - 1]} "')
                    logger.error(f'JSONDecodeError: {err} while {number}:{option} in {city}, {country}')
                    parsed = {'links':[]}
                    pass
                except Exception as err:
                    logger.error(err)
                    logger.error(f'data{[number]} was deleted in Exception')
                    del data[number]
                    continue
        except FileNotFoundError as err:
            logger.error(err)
            continue
        # saving data to json
        with open(f'{SEO_FESTIVALS_DIR}/{city_}.json', 'w') as fp:
            json.dump(data, fp, indent=4)
        logger.info(f'Finish processing {city}, {country}...SUCCESS, total score {j + 1}/{dp.get_numrows()}')
        j += 1
    
    
if __name__ == '__main__':
    change_to()