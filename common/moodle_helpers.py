"""Reusable Moodle helper functions for login, element interaction, and naming."""

import uuid
from datetime import datetime

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.locator_strategy import get_by
from config.settings import BASE_URL, MOODLE_PASSWORD, MOODLE_USERNAME


def login_to_moodle(driver, timeout=15):
    login_url = BASE_URL.rstrip("/") + "/login/index.php"
    driver.get(login_url)

    wait = WebDriverWait(driver, timeout)

    username_field = wait.until(EC.presence_of_element_located(("id", "username")))
    username_field.clear()
    username_field.send_keys(MOODLE_USERNAME)

    password_field = driver.find_element("id", "password")
    password_field.clear()
    password_field.send_keys(MOODLE_PASSWORD)

    login_btn = driver.find_element("id", "loginbtn")
    login_btn.click()

    # TODO: If Moodle Sandbox login page differs, update the logged-in check below.
    wait.until(
        EC.presence_of_element_located(("css selector", "body.loggedin, .usermenu"))
    )


def safe_find(driver, locator_type, locator_value, timeout=10):
    by = get_by(locator_type)
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, locator_value))
        )
    except TimeoutException:
        raise TimeoutException(
            f"Element not found: {locator_type}={locator_value} "
            f"(waited {timeout}s)"
        )


def safe_click(driver, locator_type, locator_value, timeout=10):
    element = safe_find(driver, locator_type, locator_value, timeout)
    element.click()
    return element


def safe_type(driver, locator_type, locator_value, value, timeout=10, clear_first=True):
    element = safe_find(driver, locator_type, locator_value, timeout)
    if clear_first:
        element.clear()
    element.send_keys(value)
    return element


def get_visible_text(driver, locator_candidates, timeout=5):
    for locator_type, locator_value in locator_candidates:
        try:
            by = get_by(locator_type)
            element = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((by, locator_value))
            )
            return element.text.strip()
        except Exception:
            continue
    return ""


def find_first_available(driver, locator_candidates, timeout=5):
    for locator_type, locator_value in locator_candidates:
        try:
            by = get_by(locator_type)
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, locator_value))
            )
            return element
        except Exception:
            continue
    tried = ", ".join(f"{t}={v}" for t, v in locator_candidates)
    raise TimeoutException(f"None of the candidate locators found: {tried}")


def make_unique_name(prefix):
    short_id = uuid.uuid4().hex[:6]
    ts = datetime.now().strftime("%H%M%S")
    return f"{prefix}_{ts}_{short_id}"
