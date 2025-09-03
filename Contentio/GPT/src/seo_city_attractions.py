import json
from pathlib import Path

from logger import logger_setup
from functions import get_response_GPT, get_prompts_GPT, get_cities_countries, is_valid_link
from config import PROMPTS_DIR, SEO_CITY_ATTRACTIONS_DIR, CITY_ATTRACTIONS_LIST_DIR, IMG_DIR


logger = logger_setup(Path(__file__).stem)

    
def change_to():
    base_url = "http://20.240.63.21/files/images/city_attractions"
    # getting inputs
    try:
        cities_countries = get_cities_countries()
        if not cities_countries: raise Exception(f'No cities_countries list provided: {cities_countries}')
        logger.info(f'Getting cities and countries list...SUCCESS')
        prompts = get_prompts_GPT(f'{PROMPTS_DIR}/city_attractions_pmt.json')
        logger.info(f'Getting prompts...SUCCESS')
    except FileNotFoundError as err:
        logger.critical(err)
        exit()
    except Exception as err:
        logger.critical(err)
        exit()
    # cities countries loop
    j = 0
    corrects = ('Ohrid', 'Pescara', 'Stuttgart', 'Constanta', 'Malmö', 'Mumbai', 'Zagreb')
    cities_countries = [cc for cc in cities_countries if cc[0] in corrects]
    for city, country in cities_countries:
        logger.info(f'Start processing {city.upper()}, {country.upper()}...SUCCESS')
        city_ = city.replace('-', '_').replace(' ', '_')
        try:
            # getting city attractions list for given city
            attr_path = f'{CITY_ATTRACTIONS_LIST_DIR}/{city_}.json'
            with open(attr_path, 'r') as fp:
                attractions = json.load(fp)
                logger.info(f'Getting attraction list for {city}...SUCCESS')
            # getting json with seo content for the same city
            seo_path = f'{SEO_CITY_ATTRACTIONS_DIR}_copy/{city_}.json' 
            with open(seo_path, 'r') as fp:
                seo_content = json.load(fp)
                logger.info(f'Getting seo content for {city}...SUCCESS')
            data = dict()
            for number, attraction in attractions.items():
                logger.info(f'Starting {number}: {attraction}')
                try:
                    # saving value into a new key 'number'
                    data[number] = dict()
                    # adding some keys
                    data[number]['name'] = attraction
                    data[number]['location'] = f'{city}, {country}'
                    data[number]['meta'] = seo_content[attraction]['summary']
                    data[number]['keywords'] = seo_content[attraction]['keywords']
                    logger.info(f"Adding keys: 'name', 'location', 'meta', 'keywords' to data[{number}]...SUCCESS")
                    # crafting the prompt for GPT
                    logger.info(f'Crafting prompt for ChatGPT')
                    prompt = prompts['title_links'].format(attraction=attraction, city=city, 
                                                           country=country, text=seo_content[attraction]['text'])
                    logger.info(f'SUCCESS')
                    # getting response from GPT
                    logger.info(f'Getting response from ChatGPT...')
                    response = get_response_GPT(prompt).replace(']]', ']}').replace('}.', '}').replace('}"', '}')
                    logger.info(f'SUCCESS')
                    # parsing response
                    logger.info(f'Parsing response...')
                    parsed = json.loads(response)
                    logger.info(f'SUCCESS')
                    # adding some keys
                    data[number]['title'] = parsed['title']
                    data[number]['text'] = seo_content[attraction]['text']
                    logger.info(f"Adding keys: 'title', 'text' to data[{number}]...SUCCESS")
                    logger.info(f'Starting response["links"] checking...')
                    data[number]['links'] = [link for link in parsed['links'] if is_valid_link(link)]
                    logger.info(f"Adding key: {data[number]['links']} to data[{number}]...SUCCESS")
                    # setting up image path                    
                    image_path = next(Path(f'{IMG_DIR}/city_attractions/{city_}').glob(f'{number}_*.jpg'))
                    image_url = [f'{base_url}/{city_}/{image_path.name}']
                    data[number]['images'] = image_url
                    logger.info(f'Completed {number}: {attraction}...SUCCESS')
                    # del seo_content[attraction]   
                except KeyError as err:
                    logger.error(f'{err} while {number}:{attraction} in {city}, {country}')
                    del data[number]
                    logger.error(f'data{[number]} was deleted in KeyError except')
                    continue
                except AttributeError as err:
                    logger.error(f'{err} while {number}:{attraction} in {city}, {country}')
                    logger.error(f'data{[number]} was deleted in AttributeError except')
                    del data[number]
                    continue
                except TypeError as err:
                    logger.error(f'{err} while {number}:{attraction} in {city}, {country}')
                    logger.error(f'data{[number]} was deleted in TypeError except')
                    del data[number]
                    continue   
                except StopIteration as err:
                    logger.error(f'{err} for {number}:{attraction} in {city}, {country}')
                    logger.error(f'data{[number]} was deleted in StopIteration except')
                    del data[number]
                    continue
                except json.decoder.JSONDecodeError as err:
                    logger.error(f'Error character: " {response[err.colno - 1]} "')
                    logger.error(f'{err} for {number}:{attraction} in {city}, {country}')
                    logger.error(f'data{[number]} was deleted in JSONDecodeErrors')
                    del data[number]
                except Exception as err:
                    logger.error(err)
                    logger.error(f'data{[number]} was deleted in Exception')
                    del data[number]
                    continue
        except FileNotFoundError as err:
            logger.error(err)
            continue
        # saving renewed date to json
        with open(f'{SEO_CITY_ATTRACTIONS_DIR}/{city_}.json', 'w') as fp:
            json.dump(data, fp, indent=4)
        logger.info(f'Finish processing {city}, {country}...SUCCESS, total score {j + 1}/{len(cities_countries)}')
        j += 1
    
    
if __name__ == '__main__':
    change_to()