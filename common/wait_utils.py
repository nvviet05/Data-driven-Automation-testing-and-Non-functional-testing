from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.locator_strategy import get_by


def wait_for_element_present(driver, locator_type: str, locator_value: str, timeout: int = 10):
    by = get_by(locator_type)
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, locator_value))
    )


def wait_for_element_visible(driver, locator_type: str, locator_value: str, timeout: int = 10):
    by = get_by(locator_type)
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, locator_value))
    )
