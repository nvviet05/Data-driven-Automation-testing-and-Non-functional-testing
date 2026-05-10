"""F003 Level 1: Create Quiz — data-driven automation.

Workflow discovered from Project 2 Katalon recordings:
- Navigate directly to /course/modedit.php?add=quiz&course=3&section=1&return=0&sr=0
- Fill quiz name into id=id_name
- Optionally enable time limit via id=id_timelimit_enabled checkbox + id=id_timelimit_number
- Optionally select attempts via id=id_attempts dropdown
- Submit via name=submitbutton2 (Save and display)
- Verify by navigating to /mod/quiz/index.php?id=3 and checking quiz name presence
- Error check via #id_error_name or .invalid-feedback
"""

import os
import time
import uuid
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from common.assertions import text_contains
from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.moodle_helpers import login_to_moodle, make_unique_name
from common.result_writer import write_results
from common.screenshot import save_screenshot
from config.settings import BASE_URL

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "level1", "f003_level1_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level1", "f003_level1_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "level1")

FEATURE_ID = "F003"
LEVEL = "level1"

# Direct URL to add a quiz to course id=3, section=1
ADD_QUIZ_URL_PATH = "/course/modedit.php?add=quiz&course=3&section=1&return=0&sr=0"

# Locators verified from Project 2 Katalon recordings
QUIZ_FORM_WAIT = "css=#id_name, form#mform1, form.mform"
QUIZ_NAME_ID = "id_name"
SUBMIT_BUTTON_NAME = "submitbutton2"
QUIZ_INDEX_PATH = "/mod/quiz/index.php?id=3"
QUIZ_INDEX_WAIT = "css=#page-mod-quiz-index, table.generaltable, #region-main"
ERROR_SELECTORS = "#id_error_name, .alert-danger, .text-danger, .form-control-feedback, .invalid-feedback, .error"
TIMELIMIT_ENABLED_ID = "id_timelimit_enabled"
TIMELIMIT_NUMBER_ID = "id_timelimit_number"
TIMELIMIT_UNIT_ID = "id_timelimit_timeunit"
ATTEMPTS_ID = "id_attempts"


def navigate_to_quiz_form(driver):
    url = BASE_URL.rstrip("/") + ADD_QUIZ_URL_PATH
    driver.get(url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#id_name, form#mform1, form.mform"))
    )


def fill_quiz_form(driver, row):
    quiz_name = row.get("quiz_name", "").strip()
    time_limit = row.get("time_limit", "").strip()
    attempts_allowed = row.get("attempts_allowed", "").strip()

    name_field = driver.find_element(By.ID, QUIZ_NAME_ID)
    name_field.clear()
    if quiz_name:
        unique_name = make_unique_name(quiz_name)
        name_field.send_keys(unique_name)
        row["_actual_quiz_name"] = unique_name

    if time_limit:
        _set_time_limit(driver, time_limit)

    if attempts_allowed:
        _set_attempts(driver, attempts_allowed)


def _set_time_limit(driver, minutes_str):
    try:
        # Enable time limit checkbox
        cb = driver.find_element(By.ID, TIMELIMIT_ENABLED_ID)
        if not cb.is_selected():
            cb.click()
        time.sleep(0.5)

        # Use JavaScript to reliably set the value (Moodle may disable the field)
        driver.execute_script("""
            var cb = document.getElementById('id_timelimit_enabled');
            if (cb && !cb.checked) {
                cb.checked = true;
                cb.dispatchEvent(new Event('change', {bubbles: true}));
            }
            var e = document.getElementById('id_timelimit_number');
            if (e) {
                e.removeAttribute('disabled');
                e.removeAttribute('readonly');
                e.value = arguments[0];
                e.dispatchEvent(new Event('input', {bubbles: true}));
                e.dispatchEvent(new Event('change', {bubbles: true}));
            }
        """, str(minutes_str))
        time.sleep(0.3)

        # Set unit to minutes
        try:
            unit_select = Select(driver.find_element(By.ID, TIMELIMIT_UNIT_ID))
            unit_select.select_by_visible_text("minutes")
        except Exception:
            pass
    except Exception:
        pass


def _set_attempts(driver, attempts_str):
    try:
        attempts_select = Select(driver.find_element(By.ID, ATTEMPTS_ID))
        if attempts_str == "0":
            attempts_select.select_by_visible_text("Unlimited")
        else:
            try:
                attempts_select.select_by_visible_text(str(attempts_str))
            except Exception:
                attempts_select.select_by_value(str(attempts_str))
    except Exception:
        pass


def submit_quiz_form(driver):
    submit_btn = driver.find_element(By.NAME, SUBMIT_BUTTON_NAME)
    submit_btn.click()


def get_quiz_actual_result(driver, row):
    should_pass = row.get("should_pass", "").strip().upper() == "TRUE"
    quiz_name = row.get("_actual_quiz_name", row.get("quiz_name", "")).strip()

    time.sleep(1)

    # Check for error messages on the form
    try:
        errors = driver.find_elements(By.CSS_SELECTOR, ERROR_SELECTORS)
        for err in errors:
            if err.is_displayed() and err.text.strip():
                return f"Validation error: {err.text.strip()}"
    except Exception:
        pass

    if should_pass and quiz_name:
        # Navigate to quiz index to verify
        index_url = BASE_URL.rstrip("/") + QUIZ_INDEX_PATH
        driver.get(index_url)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#page-mod-quiz-index, table.generaltable, #region-main")
                )
            )
            # Check short prefix of the unique name
            search_text = quiz_name.split("_")[0] if "_" in quiz_name else quiz_name[:20]
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(normalize-space(.), '{search_text}')]")
                )
            )
            return "Quiz created"
        except Exception:
            return "Quiz not found in index"
    elif not should_pass:
        # For negative tests, stay on form — check if still on form page
        try:
            driver.find_element(By.ID, QUIZ_NAME_ID)
            return "Validation error"
        except Exception:
            return "Unknown result"

    return "Unknown result"


def verify_quiz_result(row, actual_result):
    expected = row.get("expected_result", "").strip()
    should_pass = row.get("should_pass", "").strip().upper() == "TRUE"
    expected_message = row.get("expected_message", "").strip()

    actual_lower = actual_result.lower()
    expected_lower = expected.lower()

    if should_pass:
        if "created" in expected_lower and "created" in actual_lower:
            return "PASS"
    else:
        if "error" in expected_lower and "error" in actual_lower:
            return "PASS"
        if expected_message and text_contains(expected_message.lower(), actual_lower):
            return "PASS"

    return "FAIL"


def run():
    rows = read_csv(DATA_PATH)
    driver = create_driver()
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")

    try:
        for row in rows:
            tc_id = row.get("tc_id", "").strip()
            expected = row.get("expected_result", "").strip()
            actual = ""
            status = "PASS"
            screenshot_path = ""
            error_message = ""

            try:
                login_to_moodle(driver)
                navigate_to_quiz_form(driver)
                fill_quiz_form(driver, row)
                submit_quiz_form(driver)
                actual = get_quiz_actual_result(driver, row)
                status = verify_quiz_result(row, actual)

                if status == "FAIL":
                    screenshot_path = save_screenshot(
                        driver, SCREENSHOT_DIR, f"{FEATURE_ID}_{tc_id}"
                    )
            except Exception as exc:
                status = "ERROR"
                error_message = str(exc)
                actual = "ERROR"
                try:
                    screenshot_path = save_screenshot(
                        driver, SCREENSHOT_DIR, f"{FEATURE_ID}_{tc_id}"
                    )
                except Exception:
                    pass

            results.append(
                {
                    "run_id": run_id,
                    "run_date": run_date,
                    "feature_id": FEATURE_ID,
                    "tc_id": tc_id,
                    "level": LEVEL,
                    "expected_result": expected,
                    "actual_result": actual,
                    "status": status,
                    "screenshot_path": screenshot_path,
                    "error_message": error_message,
                }
            )
    finally:
        close_driver(driver)

    write_results(RESULT_PATH, results)
    print(f"F003 Level 1 complete. Results: {RESULT_PATH}")


if __name__ == "__main__":
    run()
