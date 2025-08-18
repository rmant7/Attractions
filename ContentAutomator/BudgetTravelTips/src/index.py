from bs4 import BeautifulSoup
from pathlib import Path



def href_modify():
    source_folder = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/tree/city_descriptions/en'
    with open('../index.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    city_in_page_list = set(Path(li_tag.find('a')["href"]).stem for li_tag in soup.find_all('li'))
    city_in_descriptions_folder = set(f.stem for f in Path(source_folder).glob('*.html'))
    diff_in_lists = set(city_in_descriptions_folder).difference(city_in_page_list)
    # for li_tag in soup.find_all('li'):
    #     a_tag = li_tag.find('a')
    #     city_in_list.add(Path(a_tag["href"]).stem)
        # a_tag['href'] = f'tree/city_descriptions/en/{Path(a_tag["href"]).name}'

    # with open('../index.html', 'w', encoding='utf-8') as file:
    #     file.write(str(soup))
    print(len(diff_in_lists), diff_in_lists, sep='\n')
    

if __name__ == '__main__':
    href_modify()