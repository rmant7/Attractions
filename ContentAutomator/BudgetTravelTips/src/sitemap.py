from pathlib import Path
import xml.etree.ElementTree as ET


def get_xml_root(source_xml: str) -> ET.Element:
    tree = ET.parse(Path(source_xml))
    return tree.getroot()   


def get_processed_url(root: ET.Element) -> set:
    return
    for url in root.findall('url'):
        path = Path(url.find('loc').text)
        print(path.parent.name, '/', path.name, sep='')
    ...


def append_sitemap(root: ET.Element) -> None:
    
    ...




if __name__ == '__main__':
    site_tree_folder = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/tree'
    sitemap_xml_path = '/home/andrii/code/projects/CheapTripData/ContentAutomator/BudgetTravelTips/files/sitemap.xml'
    root = get_xml_root(sitemap_xml_path)
    processed_url = get_processed_url(root)
    # for path in Path(site_tree_folder).rglob('*.html'):
        
    ...
        
    # append_sitemap(root)