from bs4 import BeautifulSoup
from pathlib import Path
import json


def get_content(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)
   
    
def get_booking_link(city: str) -> str:
    description_path = f'/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/tree/city_descriptions/en/{city}.html'
    with open(description_path, 'r') as f:
        description = f.read()
    soup = BeautifulSoup(description, 'html.parser')
    booking_link = next(a_tag_booking['href'] for a_tag_booking in soup.find_all('a', class_='action-btn') if 'Booking.com' == a_tag_booking.string.strip())
    return booking_link


def make_target_page(template_path: str, city_name_for_path :str,
                     name: str, location: str, meta: str, keywords: list, title: str, text: str, links: list, images: list) -> str:  
    with open(template_path, 'r') as f:
        template = f.read()
        
    soup = BeautifulSoup(template, 'html.parser')
    
    city_name, _ = location.split(', ')
    
    meta_description_tag = soup.find('meta', {'name': 'description'})
    if meta_description_tag: meta_description_tag['content'] = meta_description_tag['content'].format(meta=meta)
    
    meta_keywords_tag = soup.find('meta', {'name': 'keywords'})
    if meta_keywords_tag: meta_keywords_tag['content'] = meta_keywords_tag['content'].format(keywords=', '.join(keywords))
    
    og_description_tag = soup.find('meta', {'property': 'og:description'})
    if og_description_tag: og_description_tag['content'] = og_description_tag['content'].format(meta=meta)
    
    title_tag = soup.find('title')
    if title_tag: title_tag.string = title_tag.string.format(city_name=city_name)
    
    h2_section_title_tag = soup.find('h2', {'class': 'section-title'})
    if h2_section_title_tag: h2_section_title_tag.string = h2_section_title_tag.string.format(name=name)
    
    img_tag = soup.find('img', id='image')
    if img_tag: img_tag['src'] = images[0].replace('http://20.240.63.21', 'https://cheaptrip.guru')
    
    h3_tag = soup.find('h3', id='title')
    if h3_tag: h3_tag.string = h3_tag.string.format(title=title)
    
    p_tag = soup.find('p', id='text')
    if p_tag: p_tag.string = p_tag.string.format(text=text)
    
    for i, link in enumerate(links):
        link_tag = soup.find('a', id=f'link_{i + 1}')
        if link_tag: 
            link_tag['href'], link_tag.string = link, 'Visit related site'
    
    a_tag_booking = soup.find('a', class_='action-btn', href='https://www.booking.com')
    if a_tag_booking: a_tag_booking['href'] = get_booking_link(city_name_for_path)
    
    a_tag_routes = soup.find('a', class_='action-btn', href='../../../routes/en/{city_name}.html')
    if a_tag_routes: a_tag_routes.string = a_tag_routes.string.format(city_name=city_name)
    
    for a_tag in soup.find_all('a', class_='action-btn'):
        a_tag['href'] = a_tag['href'].format(city_name=city_name_for_path)
        
    for a_tag in soup.find_all('a', class_='action-btn-active'):
        a_tag['href'] = a_tag['href'].format(city_name=city_name_for_path)
    
    return soup.prettify(formatter=None)
    
    
def save_to_html(page: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(page)
    

if __name__ == '__main__':
    source_jsons_folder = '/home/andrii/code/projects/CheapTripData/ContentAutomator/Contentio/GPT/content/seo/texts/city_attractions/en'
    template_path = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/html_templates/city_attractions/en/city/target.html'
    target_folder = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/tree/city_attractions/en'
    for path in Path(source_jsons_folder).glob('*.json'):
        for v in get_content(path).values():
            target_page = make_target_page(template_path, path.stem, **v)
            save_to_html(target_page, Path(f'{target_folder}/{path.stem}/{Path(v['images'][0]).stem}.html'))
                