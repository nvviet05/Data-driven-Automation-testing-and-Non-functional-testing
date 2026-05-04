from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config.settings import HEADLESS


def create_driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


def close_driver(driver):
    if driver:
        driver.quit()
