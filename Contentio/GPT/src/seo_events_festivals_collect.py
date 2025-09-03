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
    prompts = get_prompts_GPT(f'{PROMPTS_DIR}/events_festivals_pmt.json')

    # cities countries loop
    j = 0
    for city, country in [cc for cc in dp.gen_data() if cc[0] == 'Naypyidaw']:
        logger.info(f'\nProcessing {city.upper()}, {country.upper()}...')
        city_ = city.replace('-', '_').replace(' ', '_')
        try:
            # getting children options list for given city
            evafs_path = f'{OPTION_LISTS_DIR}/events_festivals/{city_}.json'
            with open(evafs_path, 'r') as fp:
                evafs = json.load(fp)
            logger.info(f'Events and Festivals list is retrieved for {city} successfully')
            # getting json with seo content for the same city
            seo_path = f'{SEO_FESTIVALS_DIR}_copy/{city_}.json' 
            with open(seo_path, 'r') as fp:
                seo_content = json.load(fp)
            logger.info(f'Seo content is retrieved for {city} successfully')
            if not seo_content:
                logger.warning(f'SEO_content is empty. Trying to generate it...')
                data = dict()
                for number, option in evafs.items():
                    logger.info(f'Starting {number}:{option}...')
                    try:
                        logger.info(f'Crafting prompt for generating content using ChatGPT...')
                        prompt = prompts['content'].format(event=option, city=city, country=country)
                        response = get_response_GPT(prompt)
                        if not response:
                            logger.warning(f'No response got for {number}:{option}. Continue with next option')
                            continue
                        logger.info(f'Got response successfully')
                        # parsing response
                        logger.info(f'Parsing response...')
                        response = response.replace(']]', ']}').replace('}.', '}').replace('}"', '}')
                        parsed = json.loads(response)
                        logger.info(f'Response is parsed successfully')
                        # saving value into a new key 'number'
                        data[number] = dict()
                        data[number]['name'] = option
                        data[number]['meta'] = parsed['summary']
                        data[number]['keywords'] = parsed['keywords']
                        data[number]['title'] = parsed['title']
                        data[number]['description'] = parsed['text']
                        
                        logger.info(f'Completed {number}: {option}...SUCCESS')
                        
                    except KeyError as err:
                        logger.error(f'{err} while {number}:{option} in {city}, {country}')
                        del data[number]
                        logger.error(f'data{[number]} was deleted in KeyError except')
                        continue
                    except AttributeError as err:
                        logger.error(f'{err} while {number}:{option} in {city}, {country}')
                        logger.error(f'data{[number]} was deleted in AttributeError except')
                        del data[number]
                        continue
                    except TypeError as err:
                        logger.error(f'{err} while {number}:{option} in {city}, {country}')
                        logger.error(f'data{[number]} was deleted in TypeError except')
                        del data[number]
                        continue   
                    except StopIteration as err:
                        logger.error(f'{err} for {number}:{option} in {city}, {country}')
                        logger.error(f'data{[number]} was deleted in StopIteration except')
                        del data[number]
                        continue
                    except json.decoder.JSONDecodeError as err:
                        logger.error(f'Error character: " {response[err.colno - 1]} "')
                        logger.error(f'{err} for {number}:{option} in {city}, {country}')
                        logger.error(f'data{[number]} was deleted in JSONDecodeErrors')
                        # del data[number]
                        continue
                    except Exception as err:
                        logger.error(err)
                        logger.error(f'data{[number]} was deleted in Exception')
                        del data[number]
                        continue
            
                # saving renewed date to json
                with open(f'{SEO_FESTIVALS_DIR}_copy/{city_}.json', 'w') as fp:
                    json.dump(data, fp, indent=4)
    
        except FileNotFoundError as err:
            logger.error(err)
            continue
        
        logger.info(f'Finish processing {city}, {country}...SUCCESS, total score {j + 1}/{dp.get_numrows()}')
        j += 1
    
    
if __name__ == '__main__':
    change_to()