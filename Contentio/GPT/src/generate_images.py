import requests
from pathlib import Path 
import json
from io import BytesIO
from PIL import Image

from functions import get_prompts_GPT, get_images_DALLE, get_cities, elapsed_time
from logger import logger_setup
from config import IMG_DIR, PROMPTS_DIR, CHILDREN_ATTRACTIONS_LIST_DIR


logger = logger_setup(Path(__file__).stem)


def download_image(url: str, city: str, number: str, attraction: str) -> None:
    save_dir = Path(f'{IMG_DIR}/children_attractions/{city}')
    save_dir.mkdir(parents=True, exist_ok=True)
    image_name = Path(f'{number}_{attraction}.jpg')
    save_path = save_dir/image_name
    try:
        response = requests.get(url)
        # Open the downloaded image using PIL
        with Image.open(BytesIO(response.content)) as image:
            # define the desired size and save
            new_size = (1024, 1024)
            resized_image = image.resize(new_size)
            resized_image.save(save_path, format='JPEG')
            logger.info(f"Resized and saved succcessfully to {save_path}")
    except IOError as err:
        logger.error(f'An error occurred while saving the file: {err}')
    except Exception as err:
        logger.error(f'An unexpected error occurred: {err}')
        

@elapsed_time
def generate_image():
    prompts = get_prompts_GPT(PROMPTS_DIR/'children_attractions_images_pmt.json')
    cities = get_cities()
    j = 0
    for city in cities:
        logger.info(f'Processing...{city.upper()}')
        city_ = city.replace(' ', '_').replace('-', '_')
        try:
            file_path = Path(f'{CHILDREN_ATTRACTIONS_LIST_DIR}/{city_}.json')
            with open(file_path, 'r') as fp:
                attractions = json.load(fp)
            logger.info(f'Got attraction list succesfully...')    
            for number, attraction in attractions.items():
                prompt = prompts['child_attractions'].format(attraction=attraction, city=city)
                try:
                    url = get_images_DALLE(prompt)
                    if not url: raise Exception(f'No image generated for {number}:"{attraction}"')
                    logger.info(f'Generated succesfully: {number}:"{attraction}"')
                    attraction = attraction.replace(' ', '_').replace('-', '_').replace("'", "")
                    download_image(url[0], city, number, attraction)
                except Exception as err:
                    logger.error(err)
                    continue        
        except FileNotFoundError as err:
            logger.error(err)
            continue
        
        logger.info(f'Processed successfully...{city}, total score: {j + 1}/{len(cities)}')
        j += 1


if __name__ == '__main__':
    generate_image()
    
