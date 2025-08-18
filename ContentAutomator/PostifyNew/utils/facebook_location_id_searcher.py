import re
import json
from pathlib import Path
import logging

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

FACEBOOK_EMAIL = ""
FACEBOOK_PASSWORD = ""

CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument('--disable-notifications')
CHROME_OPTIONS.add_argument("--enable-cookies")

ID_PATTERN = r'/(\d+)'

loger = logging.getLogger(__name__)
loger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

loger.addHandler(file_handler)


def pars_json_files(path: Path) -> dict:
    """
    Take path to json file ,
    get data and create specific dictionary
    :return: dict, like:
    {
        'location': location from json: String,
        'location_id': id number :  String,
    }
    """

    with open(path, "r") as f:
        data_for_scraping = {
            "location": json.load(f)['location'],
            "location_id": "",
        }

    return data_for_scraping


def scraping_page(location: str) -> str:
    """
    Take location name, use selenium for
    parse page_id for this location on Facebook
    :param location: string with location , e.g. "tallinn estonia"
    :return: str with id, e.g. "123456789098765"
    """

    driver = webdriver.Chrome(options=CHROME_OPTIONS)

    driver.get(f"https://www.facebook.com/search/places/?q={location}")

    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "_al65")))

        button = driver.find_element(By.CLASS_NAME, "_al65")
        button.click()

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "_yl8")))

        email = driver.find_element(By.ID, "email")
        email.clear()
        email.send_keys(FACEBOOK_EMAIL)

        password = driver.find_element(By.ID, "pass")
        password.clear()
        password.send_keys(FACEBOOK_PASSWORD)

        login_button = driver.find_element(By.ID, "loginbutton")
        login_button.click()

        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.TAG_NAME, "body")))

        driver.get(f"https://www.facebook.com/search/places/?q={location}")

        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="x9f619'
                                                                                           ' x193iq5w x1miatn0'
                                                                                           ' xqmdsaz x1gan7if'
                                                                                           ' x1xfsgkm"]')))

        top_place = driver.find_element(By.CLASS_NAME, "x1yztbdb")

        link = top_place.find_element(By.TAG_NAME, "a").get_attribute('href')

        match = re.search(ID_PATTERN, str(link))

        if match:
            place_id = match.group(1)

        else:
            link = link[:link.index("?")]

            driver.get(link + "/about_profile_transparency")

            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.TAG_NAME, "body")))

            info_block = driver.find_element(By.CSS_SELECTOR, 'div[class="x78zum5 x19xhxss"]')
            id_block = info_block.find_element(By.CSS_SELECTOR, 'div[class="x1yztbdb"]')
            place_id = id_block.find_element(By.TAG_NAME, "span").text

        return place_id

    except WebDriverException as e:
        print("Error.Check 'app.log' file!")
        loger.error(f"Something wrong happens: {e}")
        return ""
    finally:
        driver.close()


def add_data_to_json_files(path: Path, data: dict) -> None:
    """
    Open file on path and update data
    :param path: absolute path to file
    :param data: dict like {
                    'location': location from json: String,
                    'location_id': id number :  String,
    }
    :return: None
    """

    with open(path, "r+") as f:
        json_file = json.load(f)

        f.seek(0)
        f.truncate()

        json_file["location_id"] = data["location_id"]
        json.dump(json_file, f, indent=4)


def find_location_id(path: Path) -> None:
    """
    Take path of json file, after modify him
    :param path: path to json file
    :return: None
    """

    loger.info("Program is starting\n")

    data = pars_json_files(path)

    place_id = scraping_page(data['location'].lower().replace(",", ""))

    if not place_id:
        loger.warning(f"File {path} have incorrect attraction name. Field 'location_id' is empty")
        print("Program ended with error, check log file")
        return

    data['location_id'] = place_id

    add_data_to_json_files(path, data)

    loger.info("Program is ending\n")
