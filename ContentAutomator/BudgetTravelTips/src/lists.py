from bs4 import BeautifulSoup
from pathlib import Path
import json


def get_content(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)


def make_divs(content: dict) -> str:
    div = """
    <div class="item-container">
        <div class="item-content">
            <img src="{image}" alt="Popular direction Image">
            <h3 class="text-header">{name}</h3>
            <p class="text">{text}</p>
        </div>
        <div>
            <a class="action-btn" href="{target}">Read more...</a>
        </div>
    </div>"""
    divs, city_name = '', ''
   
    for v in content.values():
        image_path = v['images'][0].replace('http://20.240.63.21', 'https://cheaptrip.guru')
        divs += div.format(image=image_path, name=v['name'], text=v['meta'], target=f'{Path(image_path).stem}.html')
        # divs += div.format(image='', name=v['name'], text=v['description'], target='#') # for transportations
        if city_name != '': continue
        city_name = v['location'].split(', ')[0]
    
    return divs.strip(), city_name
   
    
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
    
    a_tag_routes = soup.find('a', class_='action-btn', href='../../routes/en/{city_name}.html')
    if a_tag_routes: a_tag_routes.string = a_tag_routes.string.format(city_name=city_name)
    
    for a_tag in soup.find_all('a', class_='action-btn'):
        a_tag['href'] = a_tag['href'].format(city_name=city_name_for_path)
        
    for a_tag in soup.find_all('a', class_='action-btn-active'):
        a_tag['href'] = a_tag['href'].format(city_name=city_name_for_path)
    
    div_events_tag = soup.find('div', class_='main-container')
    div_events_tag.append(divs)
        
    return soup.prettify(formatter=None)
    
    
def save_to_html(page: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(page)
    

if __name__ == '__main__':
    source = '/home/andrii/code/projects/CheapTripData/ContentAutomator/Contentio/GPT/content/seo/texts/accomodations/en'
    target = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/tree/accomodations/en'
    template_path = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/html_templates/accomodations/en/list.html'
    for path in Path(source).glob('Tbilisi.json'):
        content = get_content(path)
        divs, city_name = make_divs(content), path.stem.replace('_', ' ')
        list_page = make_list_page(divs, path.stem, city_name, template_path)
        save_to_html(list_page, Path(f'{target}/{path.stem}.html'))