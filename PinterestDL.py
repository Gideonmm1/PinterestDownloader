import logging
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
from multiprocessing import cpu_count
from os import makedirs
from os.path import exists, join, dirname, abspath
from time import sleep

from requests import get
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

if not (exists(config.DL_LOCATION)):
    logger.info("Creating default download location")
    makedirs(config.DL_LOCATION)


def launch():
    logger.info("Opening browser...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, '
                         f'like Gecko) Version/11.1.2 Safari/605.1.15')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return Chrome(options=options, service=Service(ChromeDriverManager().install()))


def fetch(search_term_string, driver: WebDriver):
    """ Searches pinterest for the given word
    """
    logger.info("Searching...")
    search_string = f"https://www.pinterest.com/search/pins/?q={search_term_string}&rs=rs"
    driver.get(search_string)

def get_image_links_and_titles(html) -> list:
    """
    Finds the links to each image
    """
    logger.debug("Finding image links...")
    
    soup = BeautifulSoup(html, "lxml")
    image_links = list()
    search_term = soup.find("input", {"name": "q"})['value']
    search_term = search_term.replace(" ", "_")
    content = soup.find("div", {"class": "gridCentered"})
    pins = content.find_all(
        "div", {"class": "PinGridInner__brioPin GrowthUnauthPin_brioPinLego"})
    for pin in pins:
        link = pin.find("div", {"class": "GrowthUnauthPinImage"})

        is_video = pin.find("div", {"data-test-id": "PinTypeIdentifier"})
        if is_video and ("." not in is_video.text):
            continue
        try:
            url = link.a.img['src'].split("x/")[1]
            url = f"https://i.pinimg.com/originals/{url}"

            title = link.a['href'].replace("/", "")[:15]

            image_links.append(
                {"Link": url, "Title": title, "Folder": search_term})
        except Exception as ex:
            logger.exception(ex)

    logger.debug(f"Found {len(image_links)} images")
    return image_links


def scroll_to_load_more_images(driver: WebDriver):
    """
    The site uses JavaScript to load the images. This function imitates a user scrolling to the bottom of the results,
    triggering new images to be fetched.
    """
    logger.debug("Loading more images...")
    for i in range(7):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        sleep(2)


def get_all_images(search_term_string, driver: WebDriver):
    fetch(search_term_string, driver)
    scroll_to_load_more_images(driver)

    # {"Link": "", "Title": "", "Folder": }
    image_links_titles_and_folder = get_image_links_and_titles(
        driver.page_source)

    download_all_images(image_links_titles_and_folder[:100])

    image_folder = search_term_string.replace(" ", "_")
    image_path = abspath(join(config.DL_LOCATION, image_folder))
    logger.info(f"Your images have been downloaded to: {image_path}")


def download_all_images(image_links_titles_and_folder):
    limit = 2 * cpu_count() + 1
    all_futures = list()
    with ThreadPoolExecutor(max_workers=limit) as executor:
        for image_link_title_and_folder in image_links_titles_and_folder:
            future = executor.submit(
                download_image, image_link_title_and_folder)
            all_futures.append(future)

        for future in all_futures:
            try:
                _ = future.result(timeout=90)
            except Exception as ex:
                logger.exception(ex)
    
def download_image(image_link_and_title: dict):
    """ Downloads the image using requests library. The image is renamed accordingly.
    """
    # {"Link": "", "Title": "", "Folder": }
    image_url = image_link_and_title.get("Link")
    image_name = image_link_and_title.get("Title")
    image_folder = image_link_and_title.get("Folder")

    logger.debug(f"Working on: {image_url}")

    ext = image_url.split(".")[-1]

    image_path = join(config.DL_LOCATION, image_folder, f"{image_name}.{ext}")

    basedir = dirname(image_path)
    if not exists(basedir):
        try:
            makedirs(basedir)
        except FileExistsError as er:
            logger.warning("Folder exists")
    try:
        r = get(image_url)
        if r.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(r.content)
        else:
            logger.debug(f"{r.status_code} when downloading: {image_url}")
            if r.status_code == 403:
                new_image_URL = image_url.replace("originals", "736x")
                logger.debug(f"Retrying with the URL: {new_image_URL}")
                sleep(2.5)
                r = get(new_image_URL)
                if r.status_code == 200:
                    with open(image_path, 'wb') as f:
                        f.write(r.content) 
                else:
                    logger.debug(f"{r.status_code} when retrying downloading: {new_image_URL}")
    except ConnectionError:
        logger.error("Could not connect. Please check your internet connection")


def main():
    file_handler = RotatingFileHandler(
        './logs/PinterestDL.log', maxBytes=10485760, backupCount=5, encoding='utf-8')
    logging.basicConfig(handlers=[file_handler], level=logging.DEBUG,
                        format='%(asctime)s [%(module)s-%(lineno)d] %(levelname)s: %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s [%(module)s] %(levelname)s: %(message)s')
    console.setFormatter(formatter)

    logging.getLogger(__name__).addHandler(console)

    for module in ['urllib', 'selenium', 'urllib3', 'connectionpool']:
        logging.getLogger(module).setLevel(logging.ERROR)

    logger.info("Starting up...")

    try:
        driver = launch()
        # fetch("LED lights", driver)
        with open("./search_terms.txt", 'r') as f:
            search_terms = f.readlines()
        
        for search_term in search_terms:
            search_term = search_term.strip()
            if search_term:
                get_all_images(search_term, driver)

        # get_all_images("Spiderman PS5", driver)
        logger.info("Finished. Cleaning up and exiting...")
    except KeyboardInterrupt:
        logger.info("CTRL + C pressed!")
    except Exception as ex:
        logger.exception(ex)
    finally:
        driver.close()
        logger.info("Exiting....")


if __name__ == "__main__":
    main()