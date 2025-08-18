from bs4 import BeautifulSoup
from pathlib import Path
import json
import pandas as pd

df_city_country_path = '/home/andrii/code/projects/CheapTripData/Python/files/csv/cities_countries.csv'
df_city_country = pd.read_csv(df_city_country_path, index_col='id_city')


def get_content(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)


def get_city_country_by_id(id_: int):
    return df_city_country.loc[id_, ['city', 'country']]


def make_divs(orig_id: int, orig_city: str, dest_ids: list) -> str:
    source_folder = '/home/andrii/code/projects/CheapTripData/ContentAutomator/Contentio/GPT/content/seo/texts/city_descriptions/en'
    
    div_template_path = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/html_templates/routes/en/div.html'
    with open(div_template_path, 'r') as f:
        div = f.read()
    
    target_go_url = 'https://cheaptrip.guru/en-US/#/search/myPath?'
    orig_city = orig_city.replace(' ', '%20')
    divs= ''
    for dest_id in dest_ids:
        try:
            dest_city, dest_country = get_city_country_by_id(dest_id)
            dest_city_ = dest_city.replace(' ', '_').replace('-', '_')
            content = get_content(Path(f'{source_folder}/{dest_city_}.json'))
            image_path = content['images'][0].replace('http://20.240.63.21', 'https://cheaptrip.guru')
            divs += div.format(image = image_path,
                            header_city = dest_city,
                            header_country = dest_country,
                            text = f'{content["text"][:200]}...',
                            target_read_more = f'../../city_descriptions/en/{dest_city_}.html',
                            target_go = f'{target_go_url}from={orig_city}&fromID={orig_id}&to={dest_city.replace(" ", "%20")}&toID={dest_id}')
        except Exception as err:
            print(type(err).__name__, orig_city, dest_city)
            continue
    return divs
   
    
def get_booking_link(city: str) -> str:
    description_path = f'/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/tree/city_descriptions/en/{city}.html'
    with open(description_path, 'r') as f:
        description = f.read()
    soup = BeautifulSoup(description, 'html.parser')
    booking_link = next(a_tag_booking['href'] for a_tag_booking in soup.find_all('a', class_='action-btn') if 'Booking.com' == a_tag_booking.string.strip())
    return booking_link


def make_list_page(divs: str, city_name_for_path :str, city_name: str, template_path: str) -> str:  
    with open(template_path, 'r') as f:
        template = f.read()
        
    soup = BeautifulSoup(template, 'html.parser')
    
    title_tag = soup.find('title')
    if title_tag: title_tag.string = city_name
    
    meta_description_tag = soup.find('meta', {'name': 'description'})
    if meta_description_tag: meta_description_tag['content'] = meta_description_tag['content'].format(city_name=city_name)
    
    meta_keywords_tag = soup.find('meta', {'name': 'keywords'})
    if meta_keywords_tag: meta_keywords_tag['content'] = meta_keywords_tag['content'].format(city_name=city_name)
    
    og_description_tag = soup.find('meta', {'property': 'og:description'})
    if og_description_tag: og_description_tag['content'] = og_description_tag['content'].format(city_name=city_name)
        
    h1_section_title_tag = soup.find('h2', {'class': 'section-title'})
    if h1_section_title_tag: h1_section_title_tag.string = h1_section_title_tag.string.format(city_name=city_name)
    
    a_tag_booking = soup.find('a', class_='action-btn', href='https://www.booking.com')
    if a_tag_booking: a_tag_booking['href'] = get_booking_link(city_name_for_path)
    
    a_tag_routes = soup.find('a', class_='action-btn-active', href='{city_name}.html')
    if a_tag_routes: a_tag_routes.string = a_tag_routes.string.format(city_name=city_name)
    
    for a_tag in soup.find_all('a', class_='action-btn-active'):
        a_tag['href'] = a_tag['href'].format(city_name=city_name_for_path)
    
    for a_tag in soup.find_all('a', class_='action-btn'):
        a_tag['href'] = a_tag['href'].format(city_name=city_name_for_path)
    
    div_events_tag = soup.find('div', class_='main-container')
    div_events_tag.append(divs)
        
    return soup.prettify(formatter=None)
    
    
def save_to_html(page: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(page)
    

if __name__ == '__main__':
    source_folder = '/home/andrii/code/projects/CheapTripData/ContentAutomator/Contentio/GPT/content/seo/texts/city_descriptions/en'
    target_folder = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/tree/routes/en'
    template_path = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/html_templates/routes/en/list.html'
    
    for path in Path(source_folder).glob('*.json'):
        try:
            content = get_content(path)
            divs, city_name = make_divs(content['id'], content['name'], content['to_id']), content['name']
            list_page = make_list_page(divs, path.stem, city_name, template_path)
            save_to_html(list_page, Path(f'{target_folder}/{path.stem}.html'))
        except Exception as err:
            print(type(err).__name__, err, path.name)
            continue
            