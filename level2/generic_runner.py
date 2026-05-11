import os
import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from common.screenshot import save_screenshot
from config.locator_strategy import get_by
from config.settings import BASE_URL, MOODLE_PASSWORD, MOODLE_USERNAME

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


def _locator_candidates(locator_type: str, locator_value: str) -> list[str]:
    value = (locator_value or "").strip()
    if not value:
        return []

    if ";;" in value:
        return [part.strip() for part in value.split(";;") if part.strip()]

    if locator_type.strip().lower() == "css" and ";" in value:
        return [part.strip() for part in value.split(";") if part.strip()]

    # First try a valid XPath union as-is. If it fails, each side becomes a
    # fallback candidate for older CSV rows that used union syntax informally.
    if locator_type.strip().lower() == "xpath" and " | " in value:
        parts = [part.strip() for part in value.split(" | ") if part.strip()]
        return [value, *parts]

    return [value]


def _resolve_input_value(input_value: str) -> str:
    value = input_value or ""
    if value == "ENV_MOODLE_USERNAME":
        return MOODLE_USERNAME
    if value == "ENV_MOODLE_PASSWORD":
        return MOODLE_PASSWORD
    if value.startswith("UNIQUE:"):
        prefix = value.split(":", 1)[1].strip() or "DataDriven"
        stamp = time.strftime("%Y%m%d%H%M%S")
        return f"{prefix}_{stamp}"
    return value


def _wait_for_candidate(driver, locator_type: str, locator_value: str, condition, timeout=10):
    by = get_by(locator_type)
    errors = []
    for candidate in _locator_candidates(locator_type, locator_value):
        try:
            return WebDriverWait(driver, timeout).until(condition((by, candidate)))
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")
    raise RuntimeError("No locator candidate matched. " + " | ".join(errors))


def _find_element(driver, locator_type: str, locator_value: str, timeout=10):
    return _wait_for_candidate(
        driver,
        locator_type,
        locator_value,
        EC.presence_of_element_located,
        timeout=timeout,
    )


def _select_value(element, input_value: str):
    selector = Select(element)
    value = input_value.strip()
    if value.startswith("value="):
        selector.select_by_value(value.split("=", 1)[1])
        return
    if value.startswith("label="):
        selector.select_by_visible_text(value.split("=", 1)[1])
        return
    try:
        selector.select_by_visible_text(value)
    except Exception:
        selector.select_by_value(value)


def _should_continue(row: dict) -> bool:
    return row.get("continue_on_error", "").strip().upper() == "TRUE"


def _result_row(tc_id, step_id, expected, actual, status, screenshot_path="", error_message=""):
    return {
        "tc_id": tc_id,
        "step_id": step_id,
        "expected_result": expected,
        "actual_result": actual,
        "status": status,
        "screenshot_path": screenshot_path,
        "error_message": error_message,
    }


def run_data_driven_steps(driver, rows: list[dict]) -> list[dict]:
    results = []
    blocked_tc_ids = set()

    for row in rows:
        tc_id = row.get("tc_id", "").strip()
        step_id = row.get("step_id", "").strip()
        expected = row.get("expected_result", "").strip()
        action_type = row.get("action_type", "").strip().lower()
        locator_type = row.get("locator_type", "").strip()
        locator_value = row.get("locator_value", "").strip()
        page_url = row.get("page_url", "").strip()
        input_value = _resolve_input_value(row.get("input_value", ""))

        actual = ""
        status = "PASS"
        screenshot_path = ""
        error_message = ""
        screenshot_prefix = f"{tc_id}_{step_id}" if step_id else tc_id

        if tc_id in blocked_tc_ids:
            results.append(
                _result_row(
                    tc_id,
                    step_id,
                    expected,
                    "SKIPPED: earlier required step failed",
                    "SKIPPED",
                )
            )
            continue

        try:
            if action_type == "open":
                driver.get(_build_url(page_url))
                actual = "OPENED"
            elif action_type == "wait":
                if locator_type and locator_value:
                    _find_element(driver, locator_type, locator_value)
                else:
                    time.sleep(_parse_wait_seconds(input_value))
                actual = "WAITED"
            else:
                if not locator_type or not locator_value:
                    raise ValueError("locator_type and locator_value are required")

                if action_type == "click":
                    element = _wait_for_candidate(
                        driver,
                        locator_type,
                        locator_value,
                        EC.element_to_be_clickable,
                    )
                    element.click()
                    actual = "CLICKED"
                elif action_type == "verify_visible":
                    element = _wait_for_candidate(
                        driver,
                        locator_type,
                        locator_value,
                        EC.visibility_of_element_located,
                    )
                    actual = "VISIBLE" if element.is_displayed() else "HIDDEN"
                    if not element.is_displayed():
                        status = "FAIL"
                else:
                    element = _find_element(driver, locator_type, locator_value)
                    if action_type == "type":
                        element.clear()
                        element.send_keys(input_value)
                        actual = "TYPED"
                    elif action_type == "select":
                        _select_value(element, input_value)
                        actual = "SELECTED"
                    elif action_type == "upload":
                        element.send_keys(input_value)
                        actual = "UPLOADED"
                    elif action_type == "verify_text":
                        actual = element.text
                        if expected and expected.strip() not in actual.strip():
                            status = "FAIL"
                    else:
                        raise ValueError(f"Unsupported action_type: {action_type}")

            if expected and expected in {"OPENED", "WAITED", "TYPED", "CLICKED", "SELECTED", "UPLOADED", "VISIBLE"}:
                if actual != expected:
                    status = "FAIL"

            if status != "PASS":
                screenshot_path = save_screenshot(
                    driver, SCREENSHOT_DIR, f"{screenshot_prefix}"
                )
                if not _should_continue(row):
                    blocked_tc_ids.add(tc_id)
        except Exception as exc:
            status = "ERROR"
            error_message = str(exc)
            actual = "ERROR"
            screenshot_path = save_screenshot(
                driver, SCREENSHOT_DIR, f"{screenshot_prefix}"
            )
            if not _should_continue(row):
                blocked_tc_ids.add(tc_id)

        results.append(
            _result_row(
                tc_id,
                step_id,
                expected,
                actual,
                status,
                screenshot_path,
                error_message,
            )
        )

    return results
