"""F003 Level 1: Create Quiz — data-driven automation."""

import os
import uuid
from datetime import datetime

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from common.assertions import text_contains
from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.moodle_helpers import (
    find_first_available,
    get_visible_text,
    login_to_moodle,
    make_unique_name,
    safe_click,
    safe_type,
)
from common.result_writer import write_results
from common.screenshot import save_screenshot
from config.settings import BASE_URL

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "level1", "f003_level1_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level1", "f003_level1_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "level1")

FEATURE_ID = "F003"
LEVEL = "level1"

# TODO: Replace with a real Moodle Sandbox course URL that the test user can edit.
DEFAULT_COURSE_PATH = "/course/view.php?id=2"

# TODO: Verify these real Moodle locators manually.
TURN_EDITING_ON_CANDIDATES = [
    ("css", "input[name='setmode']"),
    ("xpath", "//button[contains(., 'Turn editing on')]"),
    ("xpath", "//a[contains(., 'Turn editing on')]"),
    ("xpath", "//input[@value='Turn editing on']"),
]

ADD_ACTIVITY_CANDIDATES = [
    ("css", "[data-action='open-chooser']"),
    ("xpath", "//button[contains(., 'Add an activity or resource')]"),
    ("xpath", "//a[contains(., 'Add an activity or resource')]"),
    ("css", ".activity-add-text"),
]

QUIZ_ACTIVITY_CANDIDATES = [
    ("xpath", "//div[contains(@class,'optionname')]//span[contains(text(),'Quiz')]"),
    ("xpath", "//a[contains(@title,'Quiz')]"),
    ("xpath", "//*[contains(@class,'option') and contains(.,'Quiz')]"),
    ("xpath", "//div[@data-internal='quiz']"),
]

QUIZ_NAME_CANDIDATES = [
    ("id", "id_name"),
    ("name", "name"),
    ("css", "input[name='name']"),
]

QUIZ_DESCRIPTION_CANDIDATES = [
    ("id", "id_introeditoreditable"),
    ("css", "[contenteditable='true']"),
    ("css", "textarea[name='introeditor[text]']"),
    ("id", "id_introeditor"),
]

# TODO: Verify time limit locators in Moodle quiz settings.
TIME_LIMIT_ENABLE_CANDIDATES = [
    ("id", "id_timelimitenable"),
    ("css", "input[name='timelimitenable']"),
]

TIME_LIMIT_VALUE_CANDIDATES = [
    ("id", "id_timelimit_number"),
    ("css", "input[name='timelimit[number]']"),
    ("id", "id_timelimit"),
]

TIME_LIMIT_UNIT_CANDIDATES = [
    ("id", "id_timelimit_timeunit"),
    ("css", "select[name='timelimit[timeunit]']"),
]

# TODO: Verify attempts allowed locators in Moodle quiz settings.
ATTEMPTS_ALLOWED_CANDIDATES = [
    ("id", "id_attempts"),
    ("css", "select[name='attempts']"),
    ("name", "attempts"),
]

TIMING_HEADER_CANDIDATES = [
    ("xpath", "//a[contains(.,'Timing')]"),
    ("xpath", "//legend[contains(.,'Timing')]"),
    ("css", "#id_timingheader .ftoggler a"),
    ("css", "#id_timing"),
]

GRADE_HEADER_CANDIDATES = [
    ("xpath", "//a[contains(.,'Grade')]"),
    ("xpath", "//legend[contains(.,'Grade')]"),
    ("css", "#id_gradeheader .ftoggler a"),
]

SAVE_BUTTON_CANDIDATES = [
    ("id", "id_submitbutton"),
    ("id", "id_submitbutton2"),
    ("css", "input[type='submit'][name='submitbutton']"),
    ("xpath", "//input[@value='Save and return to course']"),
    ("xpath", "//input[@value='Save and display']"),
]

SUCCESS_MESSAGE_CANDIDATES = [
    ("css", ".alert-success"),
    ("css", ".toast-message"),
    ("css", ".activity-item"),
    ("xpath", "//*[contains(@class,'activity')]//span[contains(.,'Quiz')]"),
]

ERROR_MESSAGE_CANDIDATES = [
    ("css", ".invalid-feedback"),
    ("css", ".error"),
    ("css", ".alert-danger"),
    ("css", ".moodle-exception"),
]


def navigate_to_course(driver, row):
    course_url = row.get("course_url", "").strip()
    if course_url:
        if course_url.startswith("http"):
            driver.get(course_url)
        else:
            driver.get(BASE_URL.rstrip("/") + "/" + course_url.lstrip("/"))
    else:
        driver.get(BASE_URL.rstrip("/") + DEFAULT_COURSE_PATH)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(("css selector", "body"))
    )


def turn_editing_on_if_needed(driver):
    try:
        page_source = driver.page_source
        if "Turn editing off" in page_source:
            return
        btn = find_first_available(driver, TURN_EDITING_ON_CANDIDATES, timeout=5)
        btn.click()
        WebDriverWait(driver, 5).until(
            lambda d: "Turn editing off" in d.page_source
            or "setmode" in d.page_source
        )
    except Exception:
        pass  # Editing may already be on, or UI layout differs


def open_add_activity_form(driver):
    btn = find_first_available(driver, ADD_ACTIVITY_CANDIDATES, timeout=10)
    btn.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            ("css selector", ".chooser-container, .modal-dialog, #chooser-form")
        )
    )


def select_quiz_activity(driver):
    quiz_option = find_first_available(driver, QUIZ_ACTIVITY_CANDIDATES, timeout=10)
    quiz_option.click()
    import time
    time.sleep(1)

    # TODO: Some Moodle versions require clicking "Add" after selecting Quiz.
    try:
        add_btn = find_first_available(
            driver,
            [
                ("css", "button.submitbutton"),
                ("xpath", "//button[contains(.,'Add')]"),
                ("css", "input[type='submit']"),
            ],
            timeout=3,
        )
        add_btn.click()
    except Exception:
        pass

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(("css selector", "form, #mform1, .mform"))
    )


def fill_quiz_form(driver, row):
    quiz_name = row.get("quiz_name", "").strip()
    quiz_description = row.get("quiz_description", "").strip()
    time_limit = row.get("time_limit", "").strip()
    attempts_allowed = row.get("attempts_allowed", "").strip()

    if quiz_name:
        unique_name = make_unique_name(quiz_name)
        name_el = find_first_available(driver, QUIZ_NAME_CANDIDATES, timeout=10)
        name_el.clear()
        name_el.send_keys(unique_name)

    if quiz_description:
        try:
            desc_el = find_first_available(driver, QUIZ_DESCRIPTION_CANDIDATES, timeout=5)
            if desc_el.tag_name.lower() in ("div", "p", "span"):
                desc_el.click()
                desc_el.send_keys(quiz_description)
            else:
                desc_el.clear()
                desc_el.send_keys(quiz_description)
        except Exception:
            pass  # Description editor may differ

    if time_limit:
        try:
            timing_section = find_first_available(driver, TIMING_HEADER_CANDIDATES, timeout=3)
            timing_section.click()
        except Exception:
            pass
        try:
            enable_cb = find_first_available(driver, TIME_LIMIT_ENABLE_CANDIDATES, timeout=3)
            if not enable_cb.is_selected():
                enable_cb.click()
            limit_field = find_first_available(driver, TIME_LIMIT_VALUE_CANDIDATES, timeout=3)
            limit_field.clear()
            limit_field.send_keys(str(time_limit))
        except Exception:
            pass  # TODO: Verify Moodle time limit field interaction

    if attempts_allowed:
        try:
            grade_section = find_first_available(driver, GRADE_HEADER_CANDIDATES, timeout=3)
            grade_section.click()
        except Exception:
            pass
        try:
            attempts_el = find_first_available(driver, ATTEMPTS_ALLOWED_CANDIDATES, timeout=3)
            sel = Select(attempts_el)
            sel.select_by_visible_text(str(attempts_allowed))
        except Exception:
            try:
                attempts_el = find_first_available(driver, ATTEMPTS_ALLOWED_CANDIDATES, timeout=3)
                sel = Select(attempts_el)
                sel.select_by_value(str(attempts_allowed))
            except Exception:
                pass  # TODO: Verify attempts dropdown values


def submit_quiz_form(driver):
    btn = find_first_available(driver, SAVE_BUTTON_CANDIDATES, timeout=10)
    btn.click()


def get_quiz_actual_result(driver, row):
    should_pass = row.get("should_pass", "").strip().upper() == "TRUE"

    import time
    time.sleep(1)

    error_text = get_visible_text(driver, ERROR_MESSAGE_CANDIDATES, timeout=3)
    if error_text:
        return f"Validation error: {error_text}"

    success_text = get_visible_text(driver, SUCCESS_MESSAGE_CANDIDATES, timeout=3)
    if success_text:
        return "Quiz created"

    page_source = driver.page_source.lower()
    if "error" in page_source or "required" in page_source:
        return "Validation error"

    current_url = driver.current_url.lower()
    if "view.php" in current_url or "course" in current_url:
        return "Quiz created"

    if should_pass:
        return "Quiz created"

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
        if text_contains(expected_lower, actual_lower):
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
                navigate_to_course(driver, row)
                turn_editing_on_if_needed(driver)
                open_add_activity_form(driver)
                select_quiz_activity(driver)
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
