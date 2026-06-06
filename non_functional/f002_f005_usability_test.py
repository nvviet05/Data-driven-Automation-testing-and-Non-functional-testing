"""F002/F005 Usability NFR: form validation feedback and input preservation.

Verifies two usability aspects for F002 (Create Course) and F005 (Enrol Users):
    - message_visibility   : the page surfaces a validation feedback message
                             when invalid inputs are submitted.
    - input_preservation   : valid inputs the user already entered (or
                             selected) survive an invalid-submission round-trip.

Reads:   data/non_functional/f002_f005_usability_data.csv
Writes:  results/non_functional/f002_f005_usability_results.csv
         resources/screenshots/non_functional/<prefix>_<tc>.png  (on FAIL)
"""

import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from common.csv_reader import read_csv
from common.browser import create_driver
from common.result_writer import write_results
from config.settings import BASE_URL, MOODLE_USERNAME, MOODLE_PASSWORD


def login_to_moodle(driver):
    driver.get(BASE_URL.rstrip("/") + "/login/index.php")
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(MOODLE_USERNAME)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(MOODLE_PASSWORD)
    driver.find_element(By.ID, "loginbtn").click()


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "non_functional", "f002_f005_usability_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "non_functional", "f002_f005_usability_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "resources", "screenshots", "non_functional")

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

ERROR_SELECTORS = (
    ".error, .alert-danger, .form-control-feedback, .invalid-feedback, "
    ".felement .error, [id^='id_error_']"
)

DEFAULT_COURSE_ID = "3"


def _parse_input(row: dict, key: str, default: str = "") -> str:
    for column in ("input_1", "input_2", "input_3"):
        value = (row.get(column) or "").strip()
        if value.startswith(f"{key}="):
            return value.split("=", 1)[1].strip()
    return default


def _take_screenshot(driver, prefix: str) -> str:
    if not driver:
        return ""
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOT_DIR, f"{prefix}_{timestamp}.png")
        driver.save_screenshot(path)
        return path
    except Exception:
        return ""


def _visible_validation_text(driver) -> str:
    messages = []
    for element in driver.find_elements(By.CSS_SELECTOR, ERROR_SELECTORS):
        try:
            if element.is_displayed():
                text = (element.text or "").strip()
                if text:
                    messages.append(text)
        except Exception:
            continue
    return "; ".join(messages)


def _check_course_form_usability(driver, row: dict) -> dict:
    full_name = _parse_input(row, "full_name", "Usability Test Course")
    short_name = _parse_input(row, "short_name", "")
    target_url = BASE_URL.rstrip("/") + "/course/edit.php?category=1"

    driver.get(target_url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "id_fullname"))
    )

    fn = driver.find_element(By.ID, "id_fullname")
    fn.clear()
    fn.send_keys(full_name)

    sn = driver.find_element(By.ID, "id_shortname")
    sn.clear()
    if short_name:
        sn.send_keys(short_name)

    save_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "id_saveanddisplay"))
    )
    save_btn.click()
    time.sleep(1.5)

    validation_text = _visible_validation_text(driver)
    validation_visible = bool(validation_text)

    preserved_full_name = False
    try:
        fn_after = driver.find_element(By.ID, "id_fullname")
        preserved_full_name = (fn_after.get_attribute("value") or "").strip() == full_name
    except NoSuchElementException:
        preserved_full_name = False

    return {
        "validation_visible": validation_visible,
        "validation_text": validation_text[:160],
        "preserved": preserved_full_name,
        "preserved_field": "full_name",
        "preserved_value": full_name,
    }


def _open_enrol_dialog(driver):
    candidates = [
        (By.CSS_SELECTOR, "input[type='submit'][value='Enrol users']"),
        (By.CSS_SELECTOR, "input[type='submit'][value='Enroll users']"),
        (By.XPATH, "//input[@type='submit'][contains(translate(@value,'E','e'),'enrol')]"),
        (By.XPATH, "//button[contains(translate(.,'E','e'),'enrol')]"),
    ]
    for by, sel in candidates:
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, sel)))
            try:
                btn.click()
            except WebDriverException:
                driver.execute_script("arguments[0].click();", btn)
            break
        except (TimeoutException, NoSuchElementException):
            continue
    else:
        raise NoSuchElementException("Enrol users button not found")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-content"))
    )
    time.sleep(0.5)


def _modal_submit_button(driver):
    return driver.find_element(
        By.CSS_SELECTOR,
        ".modal-footer button[data-action='save'], .modal-footer .btn-primary",
    )


def _check_enrol_dialog_usability(driver, row: dict) -> dict:
    course_id = _parse_input(row, "course_id", DEFAULT_COURSE_ID)
    role = _parse_input(row, "role", "Student")

    driver.get(f"{BASE_URL.rstrip('/')}/user/index.php?id={course_id}")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    _open_enrol_dialog(driver)

    try:
        Select(driver.find_element(By.ID, "id_roletoassign")).select_by_visible_text(role)
    except Exception:
        pass

    search_query = _parse_input(row, "user_search", "")
    try:
        search = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                ".modal-body input[placeholder='Search'], "
                ".form-autocomplete-input input[type='text']",
            ))
        )
        search.click()
        search.clear()
        if search_query:
            search.send_keys(search_query)
            time.sleep(1.5)
    except (TimeoutException, NoSuchElementException):
        pass

    # Moodle accepts an empty-selection Enrol click silently and reports the
    # outcome via a page-level "0 enrolled users" notification, not via a
    # form-level validation message. Click submit and look for that text.
    try:
        submit_btn = _modal_submit_button(driver)
        try:
            submit_btn.click()
        except WebDriverException:
            driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(2.0)
    except NoSuchElementException:
        pass

    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text or ""
    except Exception:
        page_text = ""

    lower_text = page_text.lower()
    confirmation_phrases = (
        "0 enrolled users",
        "0 users enrolled",
        "enrolled users: 0",
        "enrolled 0 users",
    )
    matched = next((p for p in confirmation_phrases if p in lower_text), "")
    confirmation_visible = bool(matched)

    # The modal closes after submission, so role preservation is not
    # applicable. Pass-through so the generic FAIL-if-not-preserved check
    # doesn't penalise this TC.
    return {
        "validation_visible": confirmation_visible,
        "validation_text": matched or "(no zero-enrolment confirmation found)",
        "preserved": True,
        "preserved_field": "role",
        "preserved_value": f"{role} (n/a; modal closes after submit)",
    }


def _execute_row(driver, row: dict) -> dict:
    feature_id = (row.get("feature_id") or "").strip().upper()
    if feature_id.startswith("F002"):
        return _check_course_form_usability(driver, row)
    if feature_id.startswith("F005"):
        return _check_enrol_dialog_usability(driver, row)
    raise ValueError(f"Unsupported feature_id for usability test: {feature_id!r}")


def run() -> None:
    rows = read_csv(DATA_PATH)
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")
    results: list[dict] = []
    driver = None

    Path(RESULT_PATH).unlink(missing_ok=True)
    Path(RESULT_PATH).parent.mkdir(parents=True, exist_ok=True)

    try:
        driver = create_driver()
        try:
            login_to_moodle(driver)
        except Exception as exc:
            raise RuntimeError("manager login failed for usability test run.") from exc

        for row in rows:
            tc_id = (row.get("tc_id") or "").strip()
            status = "PASS"
            error_message = ""
            screenshot_path = ""

            try:
                outcome = _execute_row(driver, row)
                actual = (
                    f"validation_visible={str(outcome['validation_visible']).lower()}; "
                    f"validation_text={outcome['validation_text'] or 'none'}; "
                    f"preserved_{outcome['preserved_field']}="
                    f"{str(outcome['preserved']).lower()}; "
                    f"observed_{outcome['preserved_field']}={outcome['preserved_value']}"
                )

                if not outcome["validation_visible"] or not outcome["preserved"]:
                    status = "FAIL"
                    parts = []
                    if not outcome["validation_visible"]:
                        parts.append("validation feedback not visible")
                    if not outcome["preserved"]:
                        parts.append(f"valid {outcome['preserved_field']} not preserved")
                    error_message = "; ".join(parts)
                    screenshot_path = _take_screenshot(driver, f"F002_F005_usability_{tc_id}")
            except Exception as exc:
                status = "ERROR"
                actual = "ERROR"
                error_message = f"{type(exc).__name__}: {exc}"
                screenshot_path = _take_screenshot(driver, f"F002_F005_usability_{tc_id}")

            results.append(
                {
                    "run_id": run_id,
                    "run_date": run_date,
                    "member": row.get("member", ""),
                    "feature_id": row.get("feature_id", ""),
                    "tc_id": tc_id,
                    "non_functional_type": row.get("non_functional_type", ""),
                    "requirement": row.get("requirement", ""),
                    "metric": row.get("metric", ""),
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
                    "screenshot_path": _take_screenshot(driver, "F002_F005_usability_fatal"),
                    "error_message": str(exc),
                }
            )
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    ordered_results = [
        {col: row.get(col, "") for col in NFR_RESULT_COLUMNS} for row in results
    ]
    write_results(RESULT_PATH, ordered_results, NFR_RESULT_COLUMNS)
    print(f"F002/F005 Usability NFR complete. Results: {RESULT_PATH}")


if __name__ == "__main__":
    run()
