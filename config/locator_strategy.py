from selenium.webdriver.common.by import By

LOCATOR_MAP = {
    "id": By.ID,
    "name": By.NAME,
    "css": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "link_text": By.LINK_TEXT,
    "partial_link_text": By.PARTIAL_LINK_TEXT,
    "tag_name": By.TAG_NAME,
    "class_name": By.CLASS_NAME,
}


def get_by(locator_type: str) -> str:
    if not locator_type:
        raise ValueError("locator_type is required")
    key = locator_type.strip().lower()
    if key not in LOCATOR_MAP:
        raise ValueError(f"Unsupported locator_type: {locator_type}")
    return LOCATOR_MAP[key]
