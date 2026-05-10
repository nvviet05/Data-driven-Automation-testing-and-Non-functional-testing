"""F008 Reliability NFR: Repeated calendar event creation stability test."""

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
DATA_DIR = os.path.join(ROOT_DIR, "data", "non_functional")
RESULT_DIR = os.path.join(ROOT_DIR, "results", "non_functional")
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

# Locators from Katalon recordings
CALENDAR_URL_PATH = "/calendar/view.php?view=month"
CALENDAR_UPCOMING_PATH = "/calendar/view.php?view=upcoming"
CALENDAR_WAIT_CSS = "#page-calendar-view, .calendartable, .calendarwrapper"
NEW_EVENT_XPATH = "//button[contains(.,'New event')] | //a[contains(.,'New event')]"
MODAL_FORM_CSS = ".modal.show form, form[data-region='event-form'], #id_name"
MODAL_SAVE_XPATH = "//div[contains(@class,'modal') and contains(@class,'show')]//button[normalize-space()='Save']"
MODAL_SHOW_CSS = ".modal.show"
EVENT_NAME_ID = "id_name"
EVENT_TYPE_ID = "id_eventtype"


def _create_single_event(driver):
    # Navigate to calendar
    driver.get(BASE_URL.rstrip("/") + CALENDAR_URL_PATH)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CALENDAR_WAIT_CSS))
    )

    # Open new event modal
    btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, NEW_EVENT_XPATH))
    )
    btn.click()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, MODAL_FORM_CSS))
    )

    # Fill title
    unique_title = make_unique_name("ReliabilityTest")
    name_field = driver.find_element(By.ID, EVENT_NAME_ID)
    name_field.clear()
    name_field.send_keys(unique_title)

    # Select user event type
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//select[@id='{EVENT_TYPE_ID}']/option[@value='user']")
            )
        )
        Select(driver.find_element(By.ID, EVENT_TYPE_ID)).select_by_value("user")
    except Exception:
        pass

    # Click Save
    save_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, MODAL_SAVE_XPATH))
    )
    save_btn.click()
    time.sleep(1)

    # Check for errors
    try:
        errors = driver.find_elements(
            By.CSS_SELECTOR,
            "#id_error_name, .alert-danger, .invalid-feedback, .error",
        )
        for err in errors:
            if err.is_displayed() and err.text.strip():
                return False, f"Validation error: {err.text.strip()}"
    except Exception:
        pass

    # Verify modal closed
    try:
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, MODAL_SHOW_CSS))
        )
        return True, "Event created"
    except Exception:
        return False, "Modal did not close after save"


def _take_screenshot(driver, prefix):
    if not driver:
        return ""
    try:
        return save_screenshot(driver, SCREENSHOT_DIR, prefix)
    except Exception:
        return ""


def _parse_repeat_count(row):
    input_2 = row.get("input_2", "").strip()
    if "repeat_count=" in input_2:
        try:
            return int(input_2.split("=")[1])
        except (ValueError, IndexError):
            pass
    return 5


def run() -> None:
    data_path = os.path.join(DATA_DIR, "f008_event_reliability_data.csv")
    result_path = os.path.join(RESULT_DIR, "f008_event_reliability_results.csv")
    rows = read_csv(data_path)
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")
    driver = None

    try:
        driver = create_driver()
        login_to_moodle(driver)

        repeat_count = _parse_repeat_count(rows[0]) if rows else 5
        pass_count = 0
        fail_count = 0
        run_errors = []

        for i in range(repeat_count):
            try:
                success, msg = _create_single_event(driver)
                if success:
                    pass_count += 1
                else:
                    fail_count += 1
                    run_errors.append(f"Run {i + 1}: {msg}")
                    _take_screenshot(driver, f"F008_reliability_run{i + 1}")
            except Exception as exc:
                fail_count += 1
                run_errors.append(f"Run {i + 1}: {exc}")
                _take_screenshot(driver, f"F008_reliability_run{i + 1}")

        total = pass_count + fail_count
        pass_rate = (pass_count / total * 100) if total > 0 else 0

        for row in rows:
            tc_id = row.get("tc_id", "").strip()
            member = row.get("member", "").strip()
            feature_id = row.get("feature_id", "").strip()
            nfr_type = row.get("non_functional_type", "").strip()
            requirement = row.get("requirement", "").strip()
            metric = row.get("metric", "").strip()
            expected = row.get("expected_result", "").strip()

            if "pass_rate" in metric:
                actual = f"pass_rate={pass_rate:.1f}%"
                status = "PASS" if pass_rate == 100.0 else "FAIL"
            elif "failure_count" in metric:
                actual = f"failure_count={fail_count}"
                status = "PASS" if fail_count == 0 else "FAIL"
            else:
                actual = f"pass_rate={pass_rate:.1f}%; failure_count={fail_count}"
                status = "PASS" if pass_rate == 100.0 else "FAIL"

            screenshot_path = ""
            error_message = ""
            if status == "FAIL":
                error_message = "; ".join(run_errors) if run_errors else "Some runs failed"
                screenshot_path = _take_screenshot(driver, f"F008_reliability_{tc_id}")

            results.append(
                {
                    "run_id": run_id,
                    "run_date": run_date,
                    "member": member,
                    "feature_id": feature_id,
                    "tc_id": tc_id,
                    "non_functional_type": nfr_type,
                    "requirement": requirement,
                    "metric": metric,
                    "expected_result": expected,
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

    write_results(result_path, results, NFR_RESULT_COLUMNS)
    print(f"F008 Reliability NFR complete. Results: {result_path}")


if __name__ == "__main__":
    run()
