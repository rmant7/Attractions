import json
from pathlib import Path
from data_provider import CSVDataProvider
from datetime import datetime
from logger import logger_setup
import functions
from config import PROMPTS_DIR
import asyncio
import requests
from io import BytesIO
from PIL import Image


dp = CSVDataProvider()
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
logger = logger_setup(f'{Path(__file__).stem}_{timestamp}')

cards_path = Path('../output/game/cards')
prompts = functions.get_prompts_GPT(f'{PROMPTS_DIR}/game_pmt.json')


@functions.elapsed_time
def gen_cases():
    output_path = Path(f'../output/game')
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f'Making output dir...SUCCESSFULLY')
    prompts = functions.get_prompts_GPT(f'{PROMPTS_DIR}/game_pmt.json')
    logger.info(f'Getting prompts...SUCCESSFULLY')
    for i, option in enumerate(prompts['options'], start=1):
        prompt = prompts['cases'].format(option=option)
        try:
            response = functions.get_response_GPT(prompt)
            logger.info(f'Generating response for "{option}"...SUCCESS')
            parsed = json.loads(response)
            logger.info(f'Parsing response for "{option}"...SUCCESS')
            cases = {'option': option, 'cases':parsed}
            with open(Path(output_path/f'option_{i}.json'), 'w') as f:
                json.dump(cases, f, indent=4, ensure_ascii=False)
                logger.info(f'Saving option "{option}"...SUCCESS')
            cases = dict()
        except Exception as err:
            logger.error(f'{type(err).__name__}: {err}. Continue with next option...')
            continue


def gen_cases_2():
    output_path = Path(f'../output/game')
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f'Making output dir...SUCCESSFULLY')
    prompts = functions.get_prompts_GPT(f'{PROMPTS_DIR}/game_pmt.json')
    logger.info(f'Getting prompts...SUCCESSFULLY')
    for i in range(10):
        try:
            response = functions.get_response_GPT(prompts['cases_2'])
            logger.info(f'Generating response...SUCCESS')
            parsed = json.loads(response)
            logger.info(f'Parsing response...SUCCESS')
            cases = {'option':i, 'cases':parsed}
            with open(Path(output_path/f'cases_{i + 1}.json'), 'w') as f:
                json.dump(cases, f, indent=4, ensure_ascii=False)
                logger.info(f'Saving cases...SUCCESS')
            cases = dict()
        except Exception as err:
            logger.error(f'{type(err).__name__}: {err}. Exit.')
            continue


def save_to_json(id: str, card: dict) -> None:
    card_path = Path(cards_path/id)
    card_path.mkdir(parents=True, exist_ok=True)
    save_path = Path(f'{card_path}/{id}.json')
    with open(save_path, 'w') as f:
        json.dump(card, f, indent=4, ensure_ascii=False)
        logger.info(f'Saving case {id}...SUCCESS')


def save_image(id: str, url: str) -> None:
    card_path = Path(cards_path/id)
    card_path.mkdir(parents=True, exist_ok=True)
    save_path = Path(f'{card_path}/{id}.jpeg')
    try:
        response = requests.get(url)
        with Image.open(BytesIO(response.content)) as image:
            image = image.resize(size=(1024, 1024))
            image.save(save_path, format='JPEG')
            logger.info(f'Saving image of option {id}...SUCCESS')  
    except IOError as err:
        print(f'An error {err} was occured while downloading image of card #{id}')
    except Exception as err:
        print(f'Unexpected error was occured while downloading image of card #{id}')


def gen_image(case_: str) -> None:
    id, case_ = case_.split('. ')
    try:
        url = functions.get_images_DALLE(prompts['image_en'].format(case=case_))
        logger.info(f'Generating image of option {id}...SUCCESS')
        save_image(id, url[0])
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err} while generating or downloading image.')
    

def gen_options(case_: str) -> None:
    id, case_ = case_.split('. ')
    try:
        response = functions.get_response_GPT(prompts['options'].format(case=case_))
        logger.info(f'Generating response for case {id}...SUCCESS')
        parsed = json.loads(response)
        logger.info(f'Parsing response for case {id}...SUCCESS')
        save_to_json(id, parsed)
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}. Exit.')
    
  
def set_ids_cases() -> None:
    source_path = Path('../output/game/cases')
    for file in source_path.glob('*.json'):
        id = int(file.stem.split('_')[1])
        with open(file, 'r') as f:
            cases = json.load(f)
        for i, case_ in enumerate(cases['cases']):
            cases['cases'][i] = '. '.join([str(id * 100 + i), case_])
        with open(file, 'w') as f:
            json.dump(cases, f, indent=4, ensure_ascii=False)
    

def main() -> None:
    cases_path = Path('../output/game/cases')
    files = sorted(list(cases_path.glob('*.json')))
    for file in files:
        if int(file.stem.split('_')[1]) < 19: continue
        with open(file, 'r') as f:
            cases = json.load(f)
        for case_ru, case_en in zip(cases['cases'], cases['cases_en']):
            if int(case_ru.split('. ')[0]) < 1919 and int(case_en.split('. ')[0]) < 1919: continue
            print('\n', case_ru)
            gen_options(case_ru)
            gen_image(case_en)
            
    
if __name__ == '__main__':
    main()