"""F008 Level 1: Create Calendar Event - data-driven automation.

Workflow discovered from Project 2 Katalon recordings:
- Navigate to /calendar/view.php?view=month
- Click "New event" to open the Moodle calendar modal
- Fill id=id_name, id=id_eventtype, start time, and duration controls
- Save inside the visible modal
- Verify successful events in /calendar/view.php?view=upcoming
- Verify negative cases by requiring a visible validation selector
"""

import os
import time
import uuid
from datetime import datetime, timedelta

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

CALENDAR_URL_PATH = "/calendar/view.php?view=month"
CALENDAR_UPCOMING_PATH = "/calendar/view.php?view=upcoming"
CALENDAR_WAIT_CSS = "#page-calendar-view, .calendartable, .calendarwrapper"
UPCOMING_WAIT_CSS = "#page-calendar-view, .eventlist, .calendarwrapper, #region-main"

NEW_EVENT_XPATH = (
    "//button[contains(.,'New event')] | //a[contains(.,'New event')] | "
    "//*[contains(@class,'btn') and contains(.,'New event')]"
)
MODAL_FORM_CSS = ".modal.show form, form[data-region='event-form'], #id_name"
EVENT_NAME_ID = "id_name"
EVENT_TYPE_ID = "id_eventtype"
COURSE_ID_SELECT = "id_courseid"
MODAL_SAVE_XPATH = (
    "//div[contains(@class,'modal') and contains(@class,'show')]"
    "//button[normalize-space()='Save']"
)
MODAL_SHOW_CSS = ".modal.show"
ERROR_SELECTORS = (
    "#id_error_name, #id_error_durationminutes, #id_error_durationuntil, "
    ".alert-danger, .text-danger, .form-control-feedback, .invalid-feedback, .error"
)

DURATION_RADIO_XPATH_TEMPLATE = "//input[@type='radio' and @name='duration' and @value='{}']"
DURATION_MINUTES_ID = "id_timedurationminutes"
TIME_START_HOUR_ID = "id_timestart_hour"
TIME_START_MINUTE_ID = "id_timestart_minute"


def _xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"


def _select_option(select_element, value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    candidates = [value, value.zfill(2)]
    for candidate in candidates:
        try:
            Select(select_element).select_by_visible_text(candidate)
            return True
        except Exception:
            pass
    for candidate in candidates:
        try:
            Select(select_element).select_by_value(str(int(candidate)) if candidate.isdigit() else candidate)
            return True
        except Exception:
            pass
    return False


def navigate_to_calendar(driver):
    driver.get(BASE_URL.rstrip("/") + CALENDAR_URL_PATH)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CALENDAR_WAIT_CSS))
    )


def open_new_event_form(driver):
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, NEW_EVENT_XPATH))
    )
    button.click()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, MODAL_FORM_CSS))
    )


def _set_event_title(driver, row):
    title = row.get("event_title", "").strip()
    mode = row.get("event_title_mode", "").strip().lower()

    name_field = driver.find_element(By.ID, EVENT_NAME_ID)
    name_field.clear()

    if mode == "empty" or not title:
        return

    unique_title = make_unique_name(title)
    name_field.send_keys(unique_title)
    row["_actual_event_title"] = unique_title


def _set_event_date(driver, date_mode: str):
    mode = (date_mode or "").strip().lower()
    if not mode:
        return
    target_date = datetime.now()
    if mode == "future":
        target_date = target_date + timedelta(days=1)
    elif mode == "invalid":
        target_date = target_date.replace(year=target_date.year + 20)

    fields = {
        "day": str(target_date.day),
        "month": str(target_date.month),
        "year": str(target_date.year),
    }
    for part, value in fields.items():
        try:
            select_element = driver.find_element(By.ID, f"id_timestart_{part}")
            _select_option(select_element, value)
        except Exception:
            continue


def _set_start_time(driver, hour: str, minute: str):
    try:
        _select_option(driver.find_element(By.ID, TIME_START_HOUR_ID), hour)
    except Exception:
        pass
    try:
        _select_option(driver.find_element(By.ID, TIME_START_MINUTE_ID), minute)
    except Exception:
        pass


def _select_event_type(driver, event_type: str) -> str:
    event_type = (event_type or "").strip().lower()
    if not event_type:
        return ""

    try:
        select_element = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.ID, EVENT_TYPE_ID))
        )
        Select(select_element).select_by_value(event_type)
        time.sleep(0.5)
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, MODAL_FORM_CSS))
        )
    except Exception as exc:
        return f"BLOCKED: event type not available ({event_type}): {exc}"

    if event_type == "course":
        try:
            course_select = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, COURSE_ID_SELECT))
            )
            _select_option(course_select, "3")
        except Exception:
            pass

    return ""


def _choose_duration_radio(driver, value: str):
    radio_xpath = DURATION_RADIO_XPATH_TEMPLATE.format(value)
    try:
        driver.find_element(By.XPATH, radio_xpath).click()
    except Exception:
        driver.execute_script(
            """
            var r = document.querySelector("input[type='radio'][name='duration'][value='" + arguments[0] + "']");
            if (r) {
                r.checked = true;
                r.dispatchEvent(new Event('click', {bubbles: true}));
                r.dispatchEvent(new Event('change', {bubbles: true}));
            }
            """,
            value,
        )
    time.sleep(0.2)


def _set_duration_minutes(driver, minutes: str):
    _choose_duration_radio(driver, "2")
    try:
        field = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, DURATION_MINUTES_ID))
        )
        field.clear()
        field.send_keys(str(minutes))
    except Exception:
        pass
    driver.execute_script(
        """
        var e = document.getElementById('id_timedurationminutes')
            || document.getElementById('id_durationminutes')
            || document.querySelector("input[name='timedurationminutes']")
            || document.querySelector("input[name='durationminutes']");
        if (e) {
            e.removeAttribute('disabled');
            e.removeAttribute('aria-disabled');
            e.removeAttribute('readonly');
            e.focus();
            e.value = arguments[0];
            e.setAttribute('value', arguments[0]);
            e.dispatchEvent(new Event('input', {bubbles: true}));
            e.dispatchEvent(new Event('change', {bubbles: true}));
            e.blur();
        }
        """,
        str(minutes),
    )
    time.sleep(0.2)


def _set_duration_until(driver, hour: str, minute: str):
    _choose_duration_radio(driver, "1")
    selectors = [
        ("hour", hour),
        ("minute", minute),
    ]
    for part, value in selectors:
        try:
            element = driver.find_element(
                By.XPATH,
                f"//select[contains(@id,'durationuntil') and contains(@id,'{part}')]",
            )
            _select_option(element, value)
        except Exception:
            continue


def _set_duration(driver, row):
    mode = row.get("duration_mode", "").strip().lower()
    if mode == "none":
        _choose_duration_radio(driver, "0")
    elif mode == "minutes":
        _set_duration_minutes(driver, row.get("duration_minutes", "").strip())
    elif mode == "until":
        _set_duration_until(
            driver,
            row.get("duration_until_hour", "").strip(),
            row.get("duration_until_minute", "").strip(),
        )


def fill_event_form(driver, row):
    _set_event_title(driver, row)
    blocked = _select_event_type(driver, row.get("event_type", ""))
    if blocked:
        return blocked
    _set_event_date(driver, row.get("event_date_mode", ""))
    _set_start_time(
        driver,
        row.get("event_start_hour", "").strip(),
        row.get("event_start_minute", "").strip(),
    )
    _set_duration(driver, row)
    return ""


def submit_event_form(driver):
    save_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, MODAL_SAVE_XPATH))
    )
    save_btn.click()


def _visible_error_text(driver) -> str:
    errors = driver.find_elements(By.CSS_SELECTOR, ERROR_SELECTORS)
    visible_errors = []
    for error in errors:
        try:
            if error.is_displayed():
                text = error.text.strip()
                visible_errors.append(text or "validation selector visible")
        except Exception:
            continue
    return "; ".join(visible_errors)


def get_event_actual_result(driver, row):
    should_pass = row.get("should_pass", "").strip().upper() == "TRUE"
    event_title = row.get("_actual_event_title", row.get("event_title", "")).strip()

    time.sleep(1)
    if should_pass and event_title:
        try:
            WebDriverWait(driver, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, MODAL_SHOW_CSS))
            )
        except Exception:
            return "Validation error: modal still open"

        driver.get(BASE_URL.rstrip("/") + CALENDAR_UPCOMING_PATH)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, UPCOMING_WAIT_CSS))
            )
            search_text = event_title.split("_", 1)[0]
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(normalize-space(.), {_xpath_literal(search_text)})]")
                )
            )
            return "Event created"
        except Exception:
            return "Event not found"

    error_text = _visible_error_text(driver)
    if error_text:
        return f"Validation error: {error_text}"

    try:
        if driver.find_elements(By.CSS_SELECTOR, MODAL_SHOW_CSS):
            return "No validation error shown"
    except Exception:
        pass
    return "Event created unexpectedly"


def verify_event_result(row, actual_result):
    expected = row.get("expected_result", "").strip().lower()
    expected_message = row.get("expected_message", "").strip().lower()
    actual = actual_result.lower()

    if actual.startswith("blocked:"):
        return "SKIPPED" if "blocked" in expected else "FAIL"
    if "created" in expected and "event created" in actual:
        return "PASS"
    if "validation error" in expected and "validation error" in actual:
        if expected_message and not text_contains(expected_message, actual):
            return "FAIL"
        return "PASS"
    return "FAIL"


def run():
    rows = read_csv(DATA_PATH)
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")

    for row in rows:
        tc_id = row.get("tc_id", "").strip()
        expected = row.get("expected_result", "").strip()
        actual = ""
        status = "PASS"
        screenshot_path = ""
        error_message = ""
        driver = None

        try:
            driver = create_driver()
            login_to_moodle(driver)
            navigate_to_calendar(driver)
            open_new_event_form(driver)
            blocked = fill_event_form(driver, row)
            if blocked:
                actual = blocked
                status = verify_event_result(row, actual)
            else:
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
        finally:
            close_driver(driver)

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

    if os.path.exists(RESULT_PATH):
        os.remove(RESULT_PATH)
    write_results(RESULT_PATH, results)
    print(f"F008 Level 1 complete. Results: {RESULT_PATH}")


if __name__ == "__main__":
    run()
