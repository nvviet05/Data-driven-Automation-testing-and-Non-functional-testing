import os
import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from common.screenshot import save_screenshot
from config.locator_strategy import get_by
from config.settings import BASE_URL

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "level2")


def _build_url(page_url: str) -> str:
    if not page_url:
        return BASE_URL
    if page_url.startswith("http://") or page_url.startswith("https://"):
        return page_url
    return f"{BASE_URL.rstrip('/')}/{page_url.lstrip('/')}"


def _parse_wait_seconds(value: str, default: int = 2) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def run_data_driven_steps(driver, rows: list[dict]) -> list[dict]:
    results = []

    for row in rows:
        tc_id = row.get("tc_id", "").strip()
        step_id = row.get("step_id", "").strip()
        expected = row.get("expected_result", "").strip()
        action_type = row.get("action_type", "").strip().lower()
        locator_type = row.get("locator_type", "").strip()
        locator_value = row.get("locator_value", "").strip()
        page_url = row.get("page_url", "").strip()
        input_value = row.get("input_value", "")

        actual = ""
        status = "PASS"
        screenshot_path = ""
        error_message = ""
        screenshot_prefix = f"{tc_id}_{step_id}" if step_id else tc_id

        try:
            if action_type == "open":
                driver.get(_build_url(page_url))
                actual = "OPENED"
            elif action_type == "wait":
                if locator_type and locator_value:
                    by = get_by(locator_type)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((by, locator_value))
                    )
                else:
                    time.sleep(_parse_wait_seconds(input_value))
                actual = "WAITED"
            else:
                if not locator_type or not locator_value:
                    raise ValueError("locator_type and locator_value are required")

                by = get_by(locator_type)
                element = driver.find_element(by, locator_value)

                if action_type == "type":
                    element.clear()
                    element.send_keys(input_value)
                    actual = "TYPED"
                elif action_type == "click":
                    element.click()
                    actual = "CLICKED"
                elif action_type == "select":
                    Select(element).select_by_visible_text(input_value)
                    actual = "SELECTED"
                elif action_type == "upload":
                    element.send_keys(input_value)
                    actual = "UPLOADED"
                elif action_type == "verify_text":
                    actual = element.text
                    if actual.strip() != expected.strip():
                        status = "FAIL"
                elif action_type == "verify_visible":
                    actual = "VISIBLE" if element.is_displayed() else "HIDDEN"
                    if not element.is_displayed():
                        status = "FAIL"
                else:
                    raise ValueError(f"Unsupported action_type: {action_type}")

            if status != "PASS":
                screenshot_path = save_screenshot(
                    driver, SCREENSHOT_DIR, f"{screenshot_prefix}"
                )
        except Exception as exc:
            status = "ERROR"
            error_message = str(exc)
            actual = "ERROR"
            screenshot_path = save_screenshot(
                driver, SCREENSHOT_DIR, f"{screenshot_prefix}"
            )

        results.append(
            {
                "tc_id": tc_id,
                "step_id": step_id,
                "expected_result": expected,
                "actual_result": actual,
                "status": status,
                "screenshot_path": screenshot_path,
                "error_message": error_message,
            }
        )

    return results
