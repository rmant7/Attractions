import json
import requests
from pathlib import Path
import random
import sys
from datetime import datetime
import re
from asyncio import run, gather

from logger import logger_setup
from env import ACCESS_TOKEN, TARGET_URL, DEFAULT_POST_FOLDER, FILES_FOLDER, COMPANY_ID, GROUP_ID, PERSON_ID


timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
logger = logger_setup(f'{Path(__file__).stem}')

# custom Exceptions to apart them from the exceptions raised in main()
class FuncException(Exception):
    pass


def remove_non_alphanumeric(raw: str) -> str:
    try:
        invalid_symbols = r'[^a-zA-Z0-9äöüÄÖÜßàáâãäåæçèéêëìíîïðòóôõöøùúûüýÿ]'
        return re.sub(invalid_symbols, '', raw)
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        raise FuncException from err 


def get_request_data(request_data_path: str) -> tuple:
    try:
        with open(Path(request_data_path), 'r') as f:
            request_data = json.load(f)
            
        return request_data['api_url'], request_data['headers'], request_data['request_body']
    
    except FileNotFoundError as err:
        file_path = Path(err.filename)
        logger.critical(f'Input file: "../{file_path.parent.name}/{file_path.name}" is not found')
        raise FuncException from err
        
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        raise FuncException from err
        

def get_json_path(post_folder: str) -> Path:
    try:
        post_folder = Path(post_folder)
        posted_path = Path(f'{FILES_FOLDER}/linkedin_posted.json')
        with open(posted_path, 'r') as f:
            posted = json.load(f)
        
        json_ids = set(v.stem for v in post_folder.glob('*.json'))
        random_json_id = random.choice(list(json_ids.difference(posted['posted'])))
        to_post_path = next(post_folder.glob(f'{random_json_id}.json'))
        
        return to_post_path
    
    except FileNotFoundError as err:
        if err.filename == str(posted_path):
            with open(posted_path, 'w') as f:
                json.dump({'posted':[]}, f, indent=4)
            logger.warning(f'File "{posted_path.parent.name}/{posted_path.name}" was created from scratch')
        
            return get_json_path(post_folder)
        
        logger.error(f'{type(err).__name__}: {err.filename}')
        raise FuncException from err
                
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        raise FuncException from err
        

def get_content(file_path: Path) -> dict:
    try:
        with open(file_path, 'r') as f:
            post_content=json.load(f)
            
        if not all(key in ('name', 'location', 'title', 'text', 'hashtags', 'links', 'images') 
                   for key in post_content.keys()): 
            raise Exception(f'Unexpected data structure in: {file_path.name}')
        if len(post_content['images']) == 0:
            raise Exception(f'There is no image in the "images" list in: {file_path.name}')
        
        return post_content
    
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        raise FuncException from err
    
    
def prepare_text_to_post(name: str, location: str, title: str, text: str, hashtags: list, **_) -> str:
    try:
        const_hashtags = {'#CheapTripGuru', '#travel', '#cheaptrip', '#budgettravel', '#travelonabudget', '#lowcosttravel',
                            '#affordabletravel', '#backpackerlife', '#cheapholidays', '#travelbudgeting', '#frugaltravel', 
                            '#savvytraveler', '#travelblogger', '#traveltips', '#traveladvice', '#travelhacks',
                            '#travelinspiration', '#wanderlust', '#explore', '#seetheworld'}
               
        hashtags_top = f'#{" #".join(map(remove_non_alphanumeric, (name, *location.split(", "))))}'
        hashtags_bottom = ' '.join(const_hashtags.union(hashtags))
        
        if text.endswith('\n'): text = text.rstrip('\n')
    
        return '\n\n'.join((hashtags_top, title, text, f"Find out more at {TARGET_URL}", hashtags_bottom))
    
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        raise FuncException from err
    
    
async def register_image() -> tuple():
    try:
        api_url, headers, request_body = get_request_data(f'{FILES_FOLDER}/schema_request_register_image.json')
        
        # insert credentials into request body
        headers['Authorization'] = headers['Authorization'].format(access_token = ACCESS_TOKEN)
        request_body['registerUploadRequest']['owner'] = request_body['registerUploadRequest']['owner'].format(company_id = COMPANY_ID)
        
        response = requests.post(api_url, json=request_body, headers=headers)
        response.raise_for_status()
       
        data = json.loads(response.text)
        upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset = data['value']['asset']
        
        return upload_url, asset
    
    except requests.HTTPError as err:
        logger.error(f'Post creation failed with status code: {response.status_code}')
        raise FuncException from err
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        raise FuncException from err
    
    
async def get_binary_image(images: list, **_) -> bytes:
    try:
        image_path = Path(images[0].replace(TARGET_URL, '/home/azureuser'))
        with open(image_path, 'rb') as f:
            return f.read()
        
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        raise FuncException from err
    
    
def upload_binary_image(upload_url: str, binary_image: bytes) -> None:
    try:                
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}', 
            'X-Restli-Protocol-Version': '2.0.0'
        }

        response = requests.post(upload_url, binary_image, headers=headers)
        response.raise_for_status()
    
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        raise FuncException from err
    
    
def post_text_and_image(text_to_share: str, image_url: str) -> str:
    try:
        api_url, headers, request_body = get_request_data(f'{FILES_FOLDER}/schema_request_groups_post.json')
              
        # insert credentials into request body
        headers['Authorization'] = headers['Authorization'].format(access_token = ACCESS_TOKEN)
        request_body['author'] = request_body['author'].format(person_id = PERSON_ID)
        request_body['containerEntity'] = request_body['containerEntity'].format(group_id=GROUP_ID)
        
        # assign input values
        request_body['specificContent']['com.linkedin.ugc.ShareContent']['shareCommentary']['text'] = text_to_share
        # request_body['specificContent']['com.linkedin.ugc.ShareContent']['media'][0]['media'] = asset
        request_body['specificContent']['com.linkedin.ugc.ShareContent']['media'][0]['thumbnails'][0]['resolvedUrl'] = image_url

        response = requests.post(api_url, headers=headers, json=request_body)
        response.raise_for_status()
        
        if response.status_code == 201:
            return 'Post from {} about {} in {} is shared SUCCESFULLY'
            
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}') 
        raise FuncException from err
        

def add_to_posted(post_id: str) -> None:
    try:
        posted_path = Path(f'{FILES_FOLDER}/linkedin_posted.json')
        with open(posted_path, 'r') as f:
            posted = json.load(f)
            
        posted['posted'].append(post_id)
        
        with open(posted_path, 'w') as f:
            json.dump(posted, f)
            
    except FileNotFoundError as err:
        file_path = Path(err.filename)
        logger.critical(f'Input file: "../{file_path.parent.name}/{file_path.name}" not found')
        raise FuncException from err
        
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}') 
        raise FuncException from err
        

async def main(lang: str='en'):
    try:
        # get random *.json from the jsons folder en/ (by default)
        json_path = get_json_path(f'{DEFAULT_POST_FOLDER}/{lang}')
        
        # get content of choiced json
        content = get_content(json_path)
        
        # forming text part of post, joining hashtags, removing the last line break, etc.
        text_to_post = prepare_text_to_post(**content)
        
        # get binary image from path and register image concurrently
        binary_image, (upload_url, asset) = await gather(get_binary_image(**content), register_image()) 
        
        # upload binary image file
        upload_binary_image(upload_url, binary_image)
            
        # share both the text and the image
        result = post_text_and_image(text_to_post, asset)
        result = post_text_and_image(text_to_post, content['images'][0])
        
        # add file name in posted file
        add_to_posted(json_path.stem)
        
        logger.info(result.format(json_path.name, content['name'], content['location']))
        
    except FuncException:
        pass
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
            

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print(f'Usage: python3 {Path(__file__).name} [ru]')
        sys.exit(1)
    elif len(sys.argv) == 2:
        run(main(sys.argv[1]))
    else:
        run(main())