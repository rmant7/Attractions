import json
import requests
from pathlib import Path


from config import CITY_ATTRACTIONS_LIST_DIR, PROMPTS_DIR, SMM_DIR
from functions import get_cities, get_prompts_GPT, get_response_GPT, elapsed_time


def get_options(city: str) -> dict:    
    with open(f'{CITY_ATTRACTIONS_LIST_DIR}/{city}.json', 'r') as f:
        options = json.load(f)
    return options


def is_valid_link(url: str, timeout: int=10) -> bool:
    try:
        requests.head(url, timeout=timeout, allow_redirects=False).raise_for_status()
        return True
    except requests.exceptions.RequestException as err:
        print("An error occurred during the request:", err)
        return False


def output_data(data: dict, city: str, output_path: Path | str) -> None:
    if any([' ' in city, '-' in city]):
        city = city.replace(' ', '_').replace('-', '_')
    with open(f'{output_path}/{city}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def generate_texts(city: str, options: dict, prompt: str) -> dict:
    data = dict()
    for i, option in options.items():
        print(i, option)
        try:
            response = get_response_GPT(prompt.format(option=option, city=city))
            content = json.loads(response, strict=False)
            if not is_valid_link(content['link']): content['link'] = ''
            data[i] = content
        except TypeError as err:
            print("TypeError:", err)
            continue
        except json.JSONDecodeError as err:
            print(err)
            continue
        except Exception as err:
            print("TypeError:",err)
    return data


@elapsed_time
def main(index: int=0, prompts_file: str='', output_dir: str='.'):
    prompts = get_prompts_GPT(f'{PROMPTS_DIR}/{prompts_file}')
    output_path = Path(f'{SMM_DIR}/{output_dir}')
    output_path.mkdir(parents=True, exist_ok=True)
    for city in get_cities():
        options = get_options(city)
        texts = generate_texts(city, options, prompts['prompt_ru'])
        output_data(texts, city, output_path)


if __name__ == "__main__":
    # from_city_index = 0
    prompts_file = 'smm_city_attractions_fp_pmt_ru.json'
    output_dir = 'city_attractions_first_person_ru'
    main(prompts_file, output_dir)