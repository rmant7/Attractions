from pathlib import Path
import json
from datetime import datetime
from data_provider import CSVDataProvider


from logger import logger_setup
from config import POSTS_DIR, SMM_CITY_ATTRACTIONS_FP_DIR, CITY_ATTRACTIONS_IMG_DIR
    

dp = CSVDataProvider()
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
logger = logger_setup(f'{Path(__file__).stem}_{timestamp}')


posts_dir = Path(f'{POSTS_DIR}/city_attractions/en')
base_url = 'http://20.240.63.21/files/images/city_attractions'


def get_texts(city: str) -> dict:
    city = city.replace(' ', '_').replace('-', '_')
    logger.info(f'Getting texts...')
    file_path = f'{SMM_CITY_ATTRACTIONS_FP_DIR}/{city}.json'
    try:
        with open(file_path, 'r') as fp:
            return json.load(fp)
    except FileNotFoundError as err:
        logger.error(err)


def get_images(city: str) -> list:
    city = city.replace(' ', '_').replace('-', '_')
    logger.info(f'Getting images...')
    folder_path = f'{CITY_ATTRACTIONS_IMG_DIR}/{city}'
    try:
        images = list(Path(folder_path).glob('[0-9]*.jpg'))
        if not images: raise FileNotFoundError(images)
        return images
    except FileNotFoundError as err:
        logger.error(f'No images were found: {err}')


def post_to_json(count: int, data: dict, city_id: int) -> None:
    post_number = city_id * 100 + count
    file_path = f'{posts_dir}/{post_number}.json'
    try:
        with open(file_path, 'w', encoding='utf-8') as fp:
            logger.info(f'posting data to: {post_number}.json')
            json.dump(data, fp, indent=4, ensure_ascii=False)
    except FileNotFoundError as err:
        logger.error(f'Disable posting to {file_path} because of error: {err}')


def compose_post(city: str, country: str, images: list, texts: dict) -> None:
    if not texts or not images: return None
    city_ = city.replace(' ', '_').replace('-', '_')
    logger.info(f'Composing posts...')
    data = dict()
    for image in images:        
        url = f'{base_url}/{city_}/{image.name}'
        index = image.name.split('_')[0]
        data[index] = dict()
        try:
            # find hashtags and links in the 'text' and remove them
            paragraphs = texts[index]['text'].split('\n\n')
            for paragraph in texts[index]['text'].split('\n\n'):
                if '#' in paragraph or 'http' in paragraph:
                    paragraphs.remove(paragraph)
            texts[index]['text'] = '\n\n'.join(paragraphs)
            # make hashtags as a list if aren't
            if not isinstance(texts[index]['hashtags'], list):
                texts[index]['hashtags'] = texts[index]['hashtags'].split(" ")                              
        except KeyError as err:
            logger.error(err)
            continue
        except TypeError as err:
            logger.error(err)
            continue
        data[index] = {'name': texts[index]['name'],
                       'location': f'{city}, {country}',
                       'title': texts[index]['text'].split('\n')[0],
                       'text': '\n'.join(texts[index]['text'].split('\n')[1:]),
                       'hashtags': texts[index]['hashtags'],
                       'links': [],
                       'images': [url]}
    return data
           
                      
def main():
    posts_dir.mkdir(parents=True, exist_ok=True)
    j = 1
    for city, country in dp.gen_data():
        city_id = dp.get_city_id(city)
        logger.info(f'Starting...{city.upper()} {city_id}')
        # city = city.replace(' ', '_').replace('-', '_')
        try:
            posts = compose_post(city, country, get_images(city), get_texts(city))
            for key, post in posts.items():
                post_to_json(int(key), post, city_id)
        except AttributeError as err:
            logger.error(f'No posts for {city} {city_id} were composed because of error: {err}')
            continue
        logger.info(f'completed successfully...{city.upper()} {city_id}, total processed: {j}/{dp.get_numrows()}')
        j += 1        

                
if __name__ == '__main__':
    main()