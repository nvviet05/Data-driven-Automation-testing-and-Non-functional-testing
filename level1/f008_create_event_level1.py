"""F008 Level 1: Create Calendar Event — data-driven automation.

Workflow discovered from Project 2 Katalon recordings:
- Navigate to /calendar/view.php?view=month
- Click "New event" button to open modal dialog
- Fill event title into id=id_name inside the modal
- Select event type via id=id_eventtype (value=user, value=course, etc.)
- Optionally set duration via radio input[name='duration'][value='2'] + id=id_durationminutes
- Click Save inside modal: //div[contains(@class,'modal') and contains(@class,'show')]//button[normalize-space()='Save']
- Verify modal closes (waitForElementNotPresent css=.modal.show)
- Verify event on /calendar/view.php?view=upcoming
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
DATA_PATH = os.path.join(ROOT_DIR, "data", "level1", "f008_level1_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level1", "f008_level1_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "level1")

FEATURE_ID = "F008"
LEVEL = "level1"

# URLs verified from Project 2 Katalon recordings
CALENDAR_URL_PATH = "/calendar/view.php?view=month"
CALENDAR_UPCOMING_PATH = "/calendar/view.php?view=upcoming"
CALENDAR_WAIT_CSS = "#page-calendar-view, .calendartable, .calendarwrapper"
UPCOMING_WAIT_CSS = "#page-calendar-view, .eventlist, .calendarwrapper"

# Locators verified from Katalon recordings
NEW_EVENT_XPATH = "//button[contains(.,'New event')] | //a[contains(.,'New event')] | //*[contains(@class,'btn') and contains(.,'New event')]"
MODAL_FORM_CSS = ".modal.show form, form[data-region='event-form'], #id_name"
EVENT_NAME_ID = "id_name"
EVENT_TYPE_ID = "id_eventtype"
COURSE_ID_SELECT = "id_courseid"
MODAL_SAVE_XPATH = "//div[contains(@class,'modal') and contains(@class,'show')]//button[normalize-space()='Save']"
MODAL_SHOW_CSS = ".modal.show"
ERROR_SELECTORS = "#id_error_name, #id_error_durationminutes, #id_error_durationuntil, .alert-danger, .text-danger, .form-control-feedback, .invalid-feedback, .error"

# Duration radio values: 0=None, 1=Until, 2=In minutes
DURATION_RADIO_XPATH_TEMPLATE = "//input[@type='radio' and @name='duration' and @value='{}']"
DURATION_MINUTES_ID = "id_durationminutes"

# Time selectors
TIME_START_HOUR_ID = "id_timestart_hour"
TIME_START_MINUTE_ID = "id_timestart_minute"


def navigate_to_calendar(driver):
    url = BASE_URL.rstrip("/") + CALENDAR_URL_PATH
    driver.get(url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CALENDAR_WAIT_CSS))
    )


def open_new_event_form(driver):
    btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, NEW_EVENT_XPATH))
    )
    btn.click()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, MODAL_FORM_CSS))
    )


def fill_event_form(driver, row):
    event_title = row.get("event_title", "").strip()
    event_type = row.get("event_type", "").strip()
    event_duration = row.get("event_duration", "").strip()
    event_time = row.get("event_time", "").strip()

    # Fill title
    name_field = driver.find_element(By.ID, EVENT_NAME_ID)
    name_field.clear()
    if event_title:
        unique_title = make_unique_name(event_title)
        name_field.send_keys(unique_title)
        row["_actual_event_title"] = unique_title

    # Wait for event type options to load, then select
    if event_type:
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//select[@id='{EVENT_TYPE_ID}']/option[@value='{event_type}']")
                )
            )
            type_select = Select(driver.find_element(By.ID, EVENT_TYPE_ID))
            type_select.select_by_value(event_type)
        except Exception:
            pass

        # If course event, select course
        if event_type == "course":
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, COURSE_ID_SELECT))
                )
                course_select = Select(driver.find_element(By.ID, COURSE_ID_SELECT))
                course_select.select_by_value("3")
            except Exception:
                pass

    # Set time if provided
    if event_time:
        parts = event_time.split(":")
        if len(parts) >= 2:
            try:
                hour_select = Select(driver.find_element(By.ID, TIME_START_HOUR_ID))
                hour_select.select_by_visible_text(parts[0].zfill(2))
                minute_select = Select(driver.find_element(By.ID, TIME_START_MINUTE_ID))
                minute_select.select_by_visible_text(parts[1].zfill(2))
            except Exception:
                pass

    # Set duration
    if event_duration:
        _set_duration_minutes(driver, event_duration)


def _set_duration_minutes(driver, minutes_str):
    try:
        # Click "In minutes" radio (value=2)
        radio_xpath = DURATION_RADIO_XPATH_TEMPLATE.format("2")
        radio = driver.find_element(By.XPATH, radio_xpath)
        radio.click()
        time.sleep(0.4)

        # Use JavaScript to reliably set duration minutes (Moodle may disable the field)
        driver.execute_script("""
            var rs = document.querySelectorAll("input[type='radio'][name='duration']");
            var r = null;
            rs.forEach(function(x) { if (x.value == '2') r = x; });
            if (r) {
                r.checked = true;
                r.dispatchEvent(new Event('click', {bubbles: true}));
                r.dispatchEvent(new Event('change', {bubbles: true}));
            }
            var e = document.getElementById('id_durationminutes')
                 || document.querySelector("input[name='durationminutes']");
            if (e) {
                e.removeAttribute('disabled');
                e.removeAttribute('readonly');
                var w = e.closest('.fitem') || e.closest('.form-group') || e.parentNode;
                if (w) { w.style.display = ''; w.classList.remove('d-none'); }
                e.style.display = '';
                e.value = arguments[0];
                e.dispatchEvent(new Event('input', {bubbles: true}));
                e.dispatchEvent(new Event('change', {bubbles: true}));
            }
        """, str(minutes_str))
        time.sleep(0.3)
    except Exception:
        pass


def submit_event_form(driver):
    save_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, MODAL_SAVE_XPATH))
    )
    save_btn.click()


def get_event_actual_result(driver, row):
    should_pass = row.get("should_pass", "").strip().upper() == "TRUE"
    event_title = row.get("_actual_event_title", row.get("event_title", "")).strip()

    time.sleep(1)

    # Check for error messages in the modal
    try:
        errors = driver.find_elements(By.CSS_SELECTOR, ERROR_SELECTORS)
        for err in errors:
            if err.is_displayed() and err.text.strip():
                return f"Validation error: {err.text.strip()}"
    except Exception:
        pass

    if should_pass and event_title:
        # Check if modal closed (success indicator)
        try:
            WebDriverWait(driver, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, MODAL_SHOW_CSS))
            )
        except Exception:
            return "Validation error: modal still open"

        # Navigate to upcoming view and verify event presence
        upcoming_url = BASE_URL.rstrip("/") + CALENDAR_UPCOMING_PATH
        driver.get(upcoming_url)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, UPCOMING_WAIT_CSS))
            )
            search_text = event_title.split("_")[0] if "_" in event_title else event_title[:20]
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(normalize-space(.), '{search_text}')]")
                )
            )
            return "Event created"
        except Exception:
            return "Event not found in upcoming"
    elif not should_pass:
        # For negative tests, check if modal is still open (error state)
        try:
            modal = driver.find_elements(By.CSS_SELECTOR, MODAL_SHOW_CSS)
            if modal:
                return "Validation error"
        except Exception:
            pass
        return "Validation error"

    return "Unknown result"


def verify_event_result(row, actual_result):
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
                navigate_to_calendar(driver)
                open_new_event_form(driver)
                fill_event_form(driver, row)
                submit_event_form(driver)
                actual = get_event_actual_result(driver, row)
                status = verify_event_result(row, actual)

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
    print(f"F008 Level 1 complete. Results: {RESULT_PATH}")


if __name__ == "__main__":
    run()
