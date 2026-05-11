"""F008 Reliability NFR: repeated calendar event creation stability."""

import os
import time
import uuid
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.moodle_helpers import login_to_moodle, make_unique_name
from common.result_writer import write_results
from common.screenshot import save_screenshot
from config.settings import BASE_URL

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "non_functional", "f008_event_reliability_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "non_functional", "f008_event_reliability_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "non_functional")

NFR_RESULT_COLUMNS = [
    "run_id",
    "run_date",
    "member",
    "feature_id",
    "tc_id",
    "non_functional_type",
    "requirement",
    "metric",
    "expected_result",
    "actual_result",
    "status",
    "screenshot_path",
    "error_message",
]

CALENDAR_URL_PATH = "/calendar/view.php?view=month"
CALENDAR_UPCOMING_PATH = "/calendar/view.php?view=upcoming"
CALENDAR_WAIT_CSS = "#page-calendar-view, .calendartable, .calendarwrapper"
UPCOMING_WAIT_CSS = "#page-calendar-view, .eventlist, .calendarwrapper, #region-main"
NEW_EVENT_XPATH = (
    "//button[contains(.,'New event')] | //a[contains(.,'New event')] | "
    "//*[contains(@class,'btn') and contains(.,'New event')]"
)
MODAL_FORM_CSS = ".modal.show form, form[data-region='event-form'], #id_name"
MODAL_SAVE_XPATH = (
    "//div[contains(@class,'modal') and contains(@class,'show')]"
    "//button[normalize-space()='Save']"
)
MODAL_SHOW_CSS = ".modal.show"
ERROR_SELECTORS = "#id_error_name, .alert-danger, .text-danger, .invalid-feedback, .error"


def _parse_input(row: dict, key: str, default: str = "") -> str:
    for column in ("input_1", "input_2", "input_3"):
        value = row.get(column, "").strip()
        if value.startswith(f"{key}="):
            return value.split("=", 1)[1].strip()
    return default


def _parse_repeat_count(rows: list[dict]) -> int:
    if not rows:
        return 5
    try:
        return int(_parse_input(rows[0], "repeat_count", "5"))
    except ValueError:
        return 5


def _xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"


def _take_screenshot(driver, prefix):
    try:
        return save_screenshot(driver, SCREENSHOT_DIR, prefix) if driver else ""
    except Exception:
        return ""


def _visible_errors(driver) -> str:
    messages = []
    for element in driver.find_elements(By.CSS_SELECTOR, ERROR_SELECTORS):
        try:
            if element.is_displayed():
                messages.append(element.text.strip() or "validation selector visible")
        except Exception:
            continue
    return "; ".join(messages)


def _verify_in_upcoming(driver, event_title: str) -> bool:
    last_error = None
    for _ in range(3):
        try:
            driver.get(BASE_URL.rstrip("/") + CALENDAR_UPCOMING_PATH)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, UPCOMING_WAIT_CSS))
            )
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(normalize-space(.), {_xpath_literal(event_title)})]")
                )
            )
            return True
        except Exception as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


def _create_single_event(driver, title_prefix: str):
    driver.get(BASE_URL.rstrip("/") + CALENDAR_URL_PATH)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CALENDAR_WAIT_CSS))
    )

    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, NEW_EVENT_XPATH))
    )
    button.click()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, MODAL_FORM_CSS))
    )

    unique_title = make_unique_name(title_prefix)
    name_field = driver.find_element(By.ID, "id_name")
    name_field.clear()
    name_field.send_keys(unique_title)

    try:
        event_type = Select(driver.find_element(By.ID, "id_eventtype"))
        values = [option.get_attribute("value") for option in event_type.options]
        if "user" in values:
            event_type.select_by_value("user")
    except Exception:
        pass

    save_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, MODAL_SAVE_XPATH))
    )
    save_btn.click()
    time.sleep(1)

    error_text = _visible_errors(driver)
    if error_text:
        return False, unique_title, f"Validation error: {error_text}"

    try:
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, MODAL_SHOW_CSS))
        )
    except Exception:
        return False, unique_title, "Modal did not close after save"

    try:
        _verify_in_upcoming(driver, unique_title)
    except Exception as exc:
        return False, unique_title, f"Event not found in upcoming: {exc}"

    return True, unique_title, "Event created"


def run() -> None:
    rows = read_csv(DATA_PATH)
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")
    driver = None

    try:
        driver = create_driver()
        login_to_moodle(driver)

        repeat_count = _parse_repeat_count(rows)
        title_prefix = _parse_input(rows[0], "event_title", "ReliabilityTest") if rows else "ReliabilityTest"
        pass_count = 0
        failure_count = 0
        run_errors = []

        for index in range(1, repeat_count + 1):
            try:
                success, title, message = _create_single_event(driver, title_prefix)
                if success:
                    pass_count += 1
                else:
                    failure_count += 1
                    run_errors.append(f"Run {index} ({title}): {message}")
                    _take_screenshot(driver, f"F008_reliability_run{index}")
            except Exception as exc:
                failure_count += 1
                run_errors.append(f"Run {index}: {exc}")
                _take_screenshot(driver, f"F008_reliability_run{index}")

        total = pass_count + failure_count
        pass_rate = (pass_count / total * 100.0) if total else 0.0

        for row in rows:
            metric = row.get("metric", "").strip()
            if "failure_count" in metric:
                actual = (
                    f"repeat_count={repeat_count}; pass_count={pass_count}; "
                    f"failure_count={failure_count}"
                )
                status = "PASS" if failure_count == 0 else "FAIL"
            else:
                actual = (
                    f"repeat_count={repeat_count}; pass_count={pass_count}; "
                    f"failure_count={failure_count}; pass_rate={pass_rate:.1f}%"
                )
                status = "PASS" if pass_rate == 100.0 and failure_count == 0 else "FAIL"

            screenshot_path = ""
            error_message = ""
            if status == "FAIL":
                error_message = "; ".join(run_errors) if run_errors else "One or more repeated runs failed"
                screenshot_path = _take_screenshot(driver, f"F008_reliability_{row.get('tc_id', '')}")

            results.append(
                {
                    "run_id": run_id,
                    "run_date": run_date,
                    "member": row.get("member", ""),
                    "feature_id": row.get("feature_id", ""),
                    "tc_id": row.get("tc_id", ""),
                    "non_functional_type": row.get("non_functional_type", ""),
                    "requirement": row.get("requirement", ""),
                    "metric": metric,
                    "expected_result": row.get("expected_result", ""),
                    "actual_result": actual,
                    "status": status,
                    "screenshot_path": screenshot_path,
                    "error_message": error_message,
                }
            )
    except Exception as exc:
        for row in rows:
            results.append(
                {
                    "run_id": run_id,
                    "run_date": run_date,
                    "member": row.get("member", ""),
                    "feature_id": row.get("feature_id", ""),
                    "tc_id": row.get("tc_id", ""),
                    "non_functional_type": row.get("non_functional_type", ""),
                    "requirement": row.get("requirement", ""),
                    "metric": row.get("metric", ""),
                    "expected_result": row.get("expected_result", ""),
                    "actual_result": "ERROR",
                    "status": "ERROR",
                    "screenshot_path": _take_screenshot(driver, "F008_reliability_fatal"),
                    "error_message": str(exc),
                }
            )
    finally:
        close_driver(driver)

    if os.path.exists(RESULT_PATH):
        os.remove(RESULT_PATH)
    write_results(RESULT_PATH, results, NFR_RESULT_COLUMNS)
    print(f"F008 Reliability NFR complete. Results: {RESULT_PATH}")


if __name__ == "__main__":
    run()
