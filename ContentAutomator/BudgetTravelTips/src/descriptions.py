from bs4 import BeautifulSoup
from pathlib import Path
import json


def make_city_descriptions():
    booking_ids_path = '/home/andrii/code/projects/CheapTripData/Python/files/hotels/booking_ids.json'
    with open(booking_ids_path, 'r') as f:
        booking_ids = json.load(f)
    
    with open('/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/html_templates/city_descriptions/en/description.html', 'r') as f:
        description = f.read()
    
    descriptions_folder = '/home/andrii/code/projects/CheapTripData/ContentAutomator/Contentio/GPT/content/seo/texts/city_descriptions/en'
    for path in Path(descriptions_folder).glob('*.json'):
        
        soup = BeautifulSoup(description, 'html.parser')
        
        with open(path, 'r') as f:
            content = json.load(f)
            
        content['text'] = content['text'].replace('\n', '<br><br>')
        content['images'] = [i.replace('http://20.240.63.21', 'https://cheaptrip.guru') for i in content['images']]
        
        booking_link = 'https://www.booking.com/searchresults.en.html?aid=7920152&city={}'
        booking_link = booking_link.format(booking_ids[str(content['id'])])
        
        title_tag = soup.find('title')
        if title_tag: title_tag.string = content['name']
        
        meta_description_tag = soup.find('meta', {'name': 'description'})
        if meta_description_tag: meta_description_tag['content'] = content['meta']
        
        meta_keywords_tag = soup.find('meta', {'name': 'keywords'})
        if meta_keywords_tag: meta_keywords_tag['content'] = ', '.join(content['keywords'])
        
        og_description_tag = soup.find('meta', {'property': 'og:description'})
        if og_description_tag: og_description_tag['content'] = content['meta']
            
        h1_section_title_tag = soup.find('h1', {'class': 'section-title'})
        if h1_section_title_tag: h1_section_title_tag.string = content['name']
            
        main_img_tag = soup.find('img', class_="city-img-attraction")
        if main_img_tag: main_img_tag['src'] = content['images'][0]

        p_tag = soup.find('p', {'id': 'text'})
        if p_tag: p_tag.string = content['text']
        
        a_tag_routes = soup.find('a', class_='action-btn', href='../../routes/en/{city_name}.html')
        if a_tag_routes: a_tag_routes.string += f' {content["name"]}'
        
        for a_tag in soup.find_all('a', class_='action-btn'):
            a_tag['href'] = a_tag['href'].format(city_name=path.stem)
        
        for a_tag in soup.find_all('a', class_='action-btn-active'):
            a_tag['href'] = a_tag['href'].format(city_name=path.stem)
            
        a_tag_booking = soup.find('a', class_='action-btn', href='https://www.booking.com')
        if a_tag_booking: a_tag_booking['href'] = booking_link
    
        output_folder = Path(f'../tree/city_descriptions/en')
        output_folder.mkdir(parents=True, exist_ok=True)
        with open(f'{output_folder}/{path.stem}.html', 'w') as f:
            f.write(soup.prettify(formatter=None))


if __name__ == '__main__':
    make_city_descriptions()