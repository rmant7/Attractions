#!/usr/bin/env python3
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from threading import Lock

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# add CheapTripData/Python dir to PATH. str wrapping is a Windows specifics:
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scraping.common.logger import kiwi_logger as logger  # noqa: E402


seconds_wait_between_actions = 1
seconds_wait_result_rendered = 10

URL = "https://www.kiwi.com/en/search/results/-/-/anytime/anytime?sortBy=price"


def get_headless_options() -> Options:
    """Return chrome options for Selenium. Chrome options for a headless browser is enabled."""

    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"  # noqa: E501
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # disable images
    chrome_options.add_experimental_option("prefs", {"profile.default_content_settings.images": 2})
    # remove DevTools messages (Windows specific)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return chrome_options


def create_chrome_driver(headless: bool = True) -> webdriver.Chrome:
    """Create and return Chrome driver. Specify options corresponding to `headless` parameter."""

    if headless:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=get_headless_options()
        )
    else:
        options = Options()
        options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.maximize_window()
    return driver


def close_modal(driver: webdriver.Chrome) -> None:
    """Close a modal window."""

    try:
        driver.find_element(By.CSS_SELECTOR, 'button[data-test="ModalCloseButton"]').click()
        time.sleep(seconds_wait_between_actions)
    except NoSuchElementException:
        logger.warning("Unable to find modal window")


def choose_currency(driver: webdriver.Chrome, currency_code: str) -> None:
    """Choose a currency."""

    currency_code = currency_code.lower()
    try:
        driver.find_element(By.CSS_SELECTOR, 'button[data-test="RegionalSettingsButton"]').click()
        elem_select = driver.find_element(By.CSS_SELECTOR, 'select[data-test="CurrencySelect"]')
        elem_select.find_element(By.CSS_SELECTOR, f'option[value="{currency_code}"]').click()
        driver.find_element(
            By.CSS_SELECTOR, 'button[data-test="SubmitRegionalSettingsButton"]'
        ).click()
        time.sleep(seconds_wait_between_actions)
    except NoSuchElementException:
        logger.warning(f'Unable to choose a "{currency_code}" currency')
        driver.refresh()


def clear_city_fields(driver: webdriver.Chrome) -> None:
    """Clear city input fields if filled."""

    try:
        for i in range(2):
            driver.find_element(
                By.CSS_SELECTOR, 'div[data-test="PlacePickerInputPlace-close"]'
            ).click()
            time.sleep(seconds_wait_between_actions)
    except NoSuchElementException:
        pass

    # if kiwi.com could NOT recognize a city name, then clear input fields.
    # unfortunately .clear() method is not working for city fields, so just refresh the page source
    try:
        input_city_from = driver.find_element(
            By.CSS_SELECTOR,
            'div[data-test="PlacePickerInput-origin"] > input[data-test="SearchField-input"]',
        )
        input_city_to = driver.find_element(
            By.CSS_SELECTOR,
            'div[data-test="PlacePickerInput-destination"] > input[data-test="SearchField-input"]',
        )
    except NoSuchElementException:
        return
    if input_city_from.get_attribute("value") or input_city_to.get_attribute("value"):
        driver.refresh()


def fill_city_fields(driver: webdriver.Chrome, city_from: str, city_to: str):
    """Fill in the initial city and destination fields."""

    try:
        element_city_from = driver.find_element(
            By.CSS_SELECTOR, 'div[data-test="PlacePickerInput-origin"] > input'
        )
        element_city_to = driver.find_element(
            By.CSS_SELECTOR, 'div[data-test="PlacePickerInput-destination"] > input'
        )
    except NoSuchElementException:
        logger.warning("Unable to find city input fields")
        return

    # need to wait for a dynamic drop-down list between actions
    element_city_from.send_keys(city_from)
    time.sleep(seconds_wait_between_actions)
    element_city_from.send_keys(Keys.ENTER)
    time.sleep(seconds_wait_between_actions)
    element_city_to.send_keys(city_to)
    time.sleep(seconds_wait_between_actions)
    element_city_to.send_keys(Keys.ENTER)

    # unfocus the input field
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(seconds_wait_between_actions)


def convert_to_minutes(time_str) -> int:
    """Convert a string representation of hours and minutes into the total number of minutes."""

    pattern = r"(?:(\d+)h)?\s?(?:(\d+)m)?"
    match = re.match(pattern, time_str)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        return hours * 60 + minutes
    else:
        return time_str


def get_min_prices(
    df: pd.DataFrame,
    driver: webdriver.Chrome = None,
    currency_code: str = "eur",
    price_colname: str = None,
    duration_colname: str = "duration_minutes",
    transfers_colname: str = "num_transfers",
    default_value: str = "N/A",
) -> pd.DataFrame:
    """
    Scrape minimal prices for all flights in a passed dataframe `df`.
    Dataframe `df` must contain ['city_from'] and ['city_to'] columns.
    Return updated dataframe `df` including a new price column.
    """

    if price_colname is None:
        price_colname = f"price_min_{currency_code.upper()}"

    if driver is None:
        driver = create_chrome_driver()

    driver.get(URL)
    close_modal(driver)
    choose_currency(driver, currency_code)

    df[price_colname] = default_value
    df[duration_colname] = default_value
    df[transfers_colname] = default_value

    for row in df.itertuples():
        city_from, city_to = row.city_from, row.city_to

        logger.info(f"Started scraping {city_from}->{city_to}...")

        clear_city_fields(driver)
        fill_city_fields(driver, city_from, city_to)
        time.sleep(seconds_wait_result_rendered)  # ensure the site has time to process a request

        try:
            card_elem = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-test="ResultCardWrapper"]')
                )
            )
            elem_min_price = card_elem.find_element(
                By.CSS_SELECTOR, 'strong[data-test="ResultCardPrice"] > span'
            )
        except NoSuchElementException:
            logger.error(f"Failed to obtain the price for route {city_from}->{city_to}")
            continue
        except TimeoutException:
            logger.error(f"No such route found {city_from}->{city_to}")
            continue
        except Exception as exc:
            logger.error(
                f"Unexpected error occurred while scraping {city_from}->{city_to}. "
                f"{type(exc).__name__}: {exc}"
            )
            driver.refresh()
            continue

        # get only digits from the price string
        min_price = "".join([i for i in elem_min_price.text if i.isdigit()])
        if min_price:
            df[price_colname].at[row.Index] = min_price

        # get flight duration
        try:
            elem_duration = card_elem.find_element(
                By.CSS_SELECTOR, 'div[data-test="TripDurationBadge"]'
            )
            df[duration_colname].at[row.Index] = convert_to_minutes(elem_duration.text)
        except NoSuchElementException:
            logger.error(f"Failed to obtain the duration for route {city_from}->{city_to}")

        # get number of transfers
        try:
            transfers = card_elem.find_element(
                By.CSS_SELECTOR, 'div[data-test|="StopCountBadge"]'
            ).text
            df[transfers_colname].at[row.Index] = (
                "0" if transfers == "Direct" else transfers.split()[0]
            )
        except NoSuchElementException:
            logger.error(f"Failed to obtain transfers for route {city_from}->{city_to}")

        logger.info(f"Finished scraping {city_from}->{city_to}. Min price is {min_price}")
    return df


def thread_scrape_min_prices(thread_id: int, df: pd.DataFrame, driver: webdriver.Chrome = None):
    """Obtain the min prices and update a shared resource `results`."""

    logger.info(f"Thread #{thread_id} started")
    df_prices = get_min_prices(df, driver)
    with lock:
        results[thread_id] = df_prices
    logger.info(f"Thread #{thread_id} finished")


def join_routes_cities(filepath_routes: str, filepath_cities: str) -> pd.DataFrame:
    """Return flight routes including full city names."""

    df_routes = pd.read_csv(filepath_routes)
    df_cities = pd.read_csv(filepath_cities, index_col="id_city")[["city"]]

    # filter by transport_id and take only 'from_id' and 'to_id' columns
    df_flight_routes = df_routes[df_routes["transport_id"] == 1][
        ["path_id", "from_id", "to_id", "transport_id"]
    ]

    # join dataframes to get city names by ids
    return df_flight_routes.join(df_cities, on="from_id").join(
        df_cities, on="to_id", lsuffix="_from", rsuffix="_to"
    )


def main(
    df: pd.DataFrame, filepath: str = None, workers_num: int = 8, headless: bool = True
) -> None:
    """
    Execute parallel scraping of minimal prices for all flight routes.
    Save results to `filepath`.
    """

    if filepath is None:
        filepath = f"kiwi_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.csv"

    thread_ids = list(range(1, workers_num + 1))
    df_chunks = np.array_split(df, workers_num)
    drivers = [create_chrome_driver(headless) for _ in thread_ids]

    with ThreadPoolExecutor(max_workers=workers_num) as executor:
        executor.map(thread_scrape_min_prices, thread_ids, df_chunks, drivers)

    for driver in drivers:
        driver.close()
        driver.quit()

    df_merged = pd.concat(
        [chunk for chunk in results.values()], ignore_index=False, sort=False
    ).sort_index()
    # df_merged.drop(["city_from", "city_to"], axis=1, inplace=True)
    df_merged.to_csv(filepath, encoding="utf-8", index=False)

    logger.info("All threads have finished their tasks")


if __name__ == "__main__":
    results = {}
    lock = Lock()
    filepath_routes = "./test_routes.csv"
    filepath_cities = "../../files/csv/cities_countries.csv"

    df_joined = join_routes_cities(filepath_routes, filepath_cities)
    main(df_joined)
