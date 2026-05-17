"""
f005_enroll_users_level1.py
---------------------------
Level 1 data-driven script for F005 - User Enrollment.

Reads:   data/level1/f005_enroll_users.csv
Writes:  results/level1/f005_results.csv
         resources/screenshots/<tc_id>.png  (on FAIL only)

CSV schema
----------
tc_id, scenario, technique, user_search, role, duration_days,
toggle_end_date, end_date_year, enrol_key, bypass_maxlength, expected_result

Action is inferred from the row (no explicit action column):
  - scenario contains "self-enrolment key"   -> enable_self_enrol
  - scenario contains "search string 0 chars" -> empty_search_check
  - scenario contains "search string"         -> search_only
  - otherwise                                  -> enroll

toggle_end_date = "Y"          -> tick id_timeend_enabled
end_date_year   = "<yyyy>"     -> set id_timeend_year (only if enabled)
bypass_maxlength = "enrol_key" -> set self-enrol key via JS (strip maxlength)
expected_result = "attr:false" -> assert the modal Enrol button is disabled

Course context:
  Auto-creates a temporary course at startup so the suite is self-contained.
  Override with env var MOODLE_TEST_COURSE_ID=<n> to use an existing course.
"""

import os
import sys
import time
import uuid
import traceback
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from common.browser import create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from config.settings import BASE_URL, MOODLE_USERNAME, MOODLE_PASSWORD

def login_to_moodle(driver):
    driver.get(BASE_URL.rstrip("/") + "/login/index.php")
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(MOODLE_USERNAME)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(MOODLE_PASSWORD)
    driver.find_element(By.ID, "loginbtn").click()


DATA_CSV = os.path.join("data", "level1", "f005_level1_data.csv")
RESULT_CSV = os.path.join("results", "level1", "f005_results.csv")
SCREENSHOT_DIR = os.path.join("resources", "screenshots")

FEATURE_ID = "F005"
LEVEL = "level1"
RUN_ID = uuid.uuid4().hex[:8]
RUN_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Click & input helpers
# ---------------------------------------------------------------------------
def safe_click(driver, element):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            element,
        )
        time.sleep(0.3)
    except Exception:
        pass
    try:
        element.click()
    except WebDriverException:
        driver.execute_script("arguments[0].click();", element)


def _set_via_js(driver, element, value: str):
    """Strip maxlength and set value via JS (bypass frontend cap)."""
    driver.execute_script(
        "arguments[0].removeAttribute('maxlength');"
        "arguments[0].value = arguments[1];"
        "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
        "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
        element, value,
    )


# ---------------------------------------------------------------------------
# Action inference
# ---------------------------------------------------------------------------
def infer_action(row) -> str:
    scenario = (row.get("scenario") or "").lower()
    if "self-enrolment key" in scenario or "self-enrol" in scenario:
        return "enable_self_enrol"
    if "search string 0 chars" in scenario or "empty search" in scenario:
        return "empty_search_check"
    if "search" in scenario:
        return "search_only"
    return "enroll"


# ---------------------------------------------------------------------------
# Course context
# ---------------------------------------------------------------------------
def ensure_test_course(driver) -> int:
    env_id = os.environ.get("MOODLE_TEST_COURSE_ID", "").strip()
    if env_id.isdigit():
        return int(env_id)

    stamp = datetime.now().strftime("%H%M%S")
    full = f"F005 Test Course {stamp}"
    short = f"F005TC{stamp}"

    driver.get(f"{BASE_URL}/course/edit.php?category=1")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "id_fullname"))
    )
    driver.find_element(By.ID, "id_fullname").send_keys(full)
    driver.find_element(By.ID, "id_shortname").send_keys(short)
    safe_click(driver, driver.find_element(By.ID, "id_saveanddisplay"))

    WebDriverWait(driver, 15).until(EC.url_contains("/course/view.php"))
    url = driver.current_url
    cid = url.split("id=")[-1].split("&")[0]
    print(f"[setup] Created test course {short} (id={cid})")
    return int(cid)


# ---------------------------------------------------------------------------
# Page navigation
# ---------------------------------------------------------------------------
def goto_participants(driver, course_id: int):
    driver.get(f"{BASE_URL}/user/index.php?id={course_id}")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )


def goto_enrolment_methods(driver, course_id: int):
    driver.get(f"{BASE_URL}/enrol/instances.php?id={course_id}")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )


# ---------------------------------------------------------------------------
# Enrol-dialog helpers
# ---------------------------------------------------------------------------
def _open_enrol_dialog(driver):
    candidates = [
        (By.CSS_SELECTOR, "input[type='submit'][value='Enrol users']"),
        (By.CSS_SELECTOR, "input[type='submit'][value='Enroll users']"),
        (By.XPATH, "//input[@type='submit'][contains(translate(@value, 'E', 'e'), 'enrol')]"),
        (By.CSS_SELECTOR, "button[data-action='enrol'], button[data-action='enroll']"),
        (By.XPATH, "//button[contains(translate(text(), 'E', 'e'), 'enrol') or contains(translate(text(), 'E', 'e'), 'enroll')]"),
    ]
    time.sleep(1)

    for by, sel in candidates:
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, sel)))
            safe_click(driver, btn)
            break
        except (TimeoutException, NoSuchElementException):
            continue
    else:
        raise NoSuchElementException("Enrol users button not found")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-content"))
    )
    time.sleep(0.5)


def _enrol_modal_submit_button(driver):
    return driver.find_element(
        By.CSS_SELECTOR,
        ".modal-footer button[data-action='save'], .modal-footer .btn-primary",
    )


def _type_user_search(driver, query: str):
    search = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            ".modal-body input[placeholder='Search'], "
            ".form-autocomplete-input input[type='text']",
        ))
    )
    driver.execute_script(
        "arguments[0].focus(); arguments[0].scrollIntoView({block: 'center'});",
        search,
    )
    time.sleep(0.2)
    search.click()
    search.clear()
    if query:
        search.send_keys(query)
        time.sleep(2.5)
    return search


# ---------------------------------------------------------------------------
# Action implementations
# ---------------------------------------------------------------------------
def action_enroll(driver, row, course_id: int):
    goto_participants(driver, course_id)
    _open_enrol_dialog(driver)

    user_search = (row.get("user_search") or "").strip()
    role = (row.get("role") or "Student").strip()

    _type_user_search(driver, user_search)

    try:
        suggestion = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                ".form-autocomplete-suggestions li, "
                ".form-autocomplete-suggestions [role='option']",
            ))
        )
        suggestion.click()
        time.sleep(0.5)
    except TimeoutException:
        print(f"   Warning: no suggestion dropdown for '{user_search}'")

    if role:
        try:
            Select(driver.find_element(By.ID, "id_roletoassign")).select_by_visible_text(role)
        except Exception as e:
            print(f"   Note: could not set role '{role}': {e}")

    _apply_advanced_options(driver, row)

    try:
        confirm_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                ".modal-footer button[data-action='save'], .modal-footer .btn-primary",
            ))
        )
        safe_click(driver, confirm_btn)
        time.sleep(2.0)
    except TimeoutException:
        raise NoSuchElementException("Modal-footer submit button not clickable")


def _apply_advanced_options(driver, row):
    duration_days = (row.get("duration_days") or "").strip()
    toggle_end_date = (row.get("toggle_end_date") or "").strip().upper() == "Y"
    end_year = (row.get("end_date_year") or "").strip()

    try:
        n_days = int(duration_days) if duration_days else None
    except ValueError:
        n_days = None

    # Zero duration is not expressible via id_duration (which is 1..365);
    # express it by snapping the start date to "Now".
    start_date_value = "4" if n_days == 0 else ""

    needs_advanced = bool(start_date_value) or (n_days is not None) or toggle_end_date

    if not needs_advanced:
        return

    try:
        toggler = driver.find_element(
            By.CSS_SELECTOR, "a.moreless-toggler[aria-controls='form-advanced-div']"
        )
        if "moreless-less" not in (toggler.get_attribute("class") or ""):
            safe_click(driver, toggler)
            time.sleep(0.5)
    except NoSuchElementException:
        pass

    if start_date_value:
        try:
            Select(driver.find_element(By.ID, "id_startdate")).select_by_value(start_date_value)
        except Exception as e:
            print(f"   Note: could not set start date: {e}")

    if n_days is not None and 1 <= n_days <= 365:
        try:
            Select(driver.find_element(By.ID, "id_duration")).select_by_visible_text(f"{n_days} days")
        except Exception as e:
            print(f"   Note: could not set duration '{duration_days}': {e}")

    if toggle_end_date:
        try:
            cb = driver.find_element(By.ID, "id_timeend_enabled")
            if not cb.is_selected():
                safe_click(driver, cb)
                time.sleep(0.3)
            if end_year:
                Select(driver.find_element(By.ID, "id_timeend_year")).select_by_value(end_year)
        except Exception as e:
            print(f"   Note: could not configure end date: {e}")


def action_search_only(driver, row, course_id: int):
    goto_participants(driver, course_id)
    _open_enrol_dialog(driver)
    _type_user_search(driver, (row.get("user_search") or "").strip())


def action_empty_search_check(driver, row, course_id: int):
    goto_participants(driver, course_id)
    _open_enrol_dialog(driver)
    _type_user_search(driver, "")


def action_unenroll(driver, row, course_id: int):
    goto_participants(driver, course_id)
    user_search = (row.get("user_search") or "").strip()
    if not user_search:
        return

    try:
        filter_input = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "input[name='search'], input[placeholder*='Search']",
            ))
        )
        filter_input.clear()
        filter_input.send_keys(user_search + Keys.RETURN)
        time.sleep(2.0)
    except Exception:
        pass

    try:
        rows = driver.find_elements(
            By.XPATH,
            "//*[@id='participants']/tbody/tr[starts-with(@id, 'user-index-participants-')]",
        )
        needle = user_search.lower()
        target = None
        for r in rows:
            try:
                badge = r.find_element(By.CSS_SELECTOR, "span.userinitials")
                title = (badge.get_attribute("title") or "").lower()
                aria = (badge.get_attribute("aria-label") or "").lower()
                if needle in title or needle in aria:
                    target = r
                    break
            except NoSuchElementException:
                continue
        if target is None:
            return

        trash = target.find_element(
            By.CSS_SELECTOR, "a[data-action='unenrol'], a.unenrollink"
        )
        safe_click(driver, trash)

        confirm_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[normalize-space()='Unenrol' or normalize-space()='Continue']",
            ))
        )
        safe_click(driver, confirm_btn)
        time.sleep(2.0)
    except NoSuchElementException:
        pass


def action_enable_self_enrol(driver, row, course_id: int):
    goto_enrolment_methods(driver, course_id)
    enrol_key = (row.get("enrol_key") or "").strip()
    bypass = (row.get("bypass_maxlength") or "").strip().lower()

    # Try to open the existing Self-enrolment edit form.
    edit_link = None
    try:
        edit_link = driver.find_element(
            By.XPATH,
            "//tr[.//td[contains(., 'Self enrolment')]]"
            "//a[contains(@href, 'edit.php') or contains(@title, 'Edit')]",
        )
    except NoSuchElementException:
        pass

    if edit_link is None:
        # Self-enrolment instance doesn't exist yet — add via the Add method
        # dropdown.
        try:
            Select(driver.find_element(By.ID, "id_jump")).select_by_visible_text(
                "Self enrolment"
            )
            time.sleep(1.5)
        except (NoSuchElementException, Exception):
            try:
                safe_click(driver, driver.find_element(By.CSS_SELECTOR, "a[title*='Enable']"))
                time.sleep(1)
                return
            except NoSuchElementException:
                return
    else:
        safe_click(driver, edit_link)
        time.sleep(1.0)

    if enrol_key:
        try:
            # 1. Look for the password unmask toggle link using its specific data attribute
            try:
                unmask_link = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-passwordunmask='edit']"))
                )
                safe_click(driver, unmask_link)
                time.sleep(0.5)  # Allow a brief moment for the input field to become active
            except (TimeoutException, NoSuchElementException):
                # Fallback to the legacy fallback selectors if the data attribute isn't found
                try:
                    show = driver.find_element(By.CSS_SELECTOR, "a.unmask, .form-passwordunmask a")
                    safe_click(driver, show)
                    time.sleep(0.3)
                except NoSuchElementException:
                    pass

            # 2. Locate the input field, clear it, and enter the enrollment key
            key_field = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "id_password"))
            )
            key_field.clear()
            
            if bypass == "enrol_key":
                _set_via_js(driver, key_field, enrol_key)
            else:
                key_field.send_keys(enrol_key)
                
        except (TimeoutException, NoSuchElementException) as e:
            print(f"   Note: Could not interact with enrollment key field: {e}")

    try:
        safe_click(driver, driver.find_element(By.ID, "id_submitbutton"))
        time.sleep(1.5)
    except NoSuchElementException:
        pass


ACTIONS = {
    "enroll": action_enroll,
    "search_only": action_search_only,
    "empty_search_check": action_empty_search_check,
    "enable_self_enrol": action_enable_self_enrol,
}


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def check_expected(driver, expected_text: str):
    if not expected_text:
        return True, "(no expected_result specified)"

    # Special assertion: expected "attr:false" means the modal Enrol button
    # should be disabled (e.g., when the search box is empty).
    if expected_text.startswith("attr:"):
        want_enabled = expected_text.split(":", 1)[1].strip().lower() == "true"
        try:
            btn = _enrol_modal_submit_button(driver)
            disabled = btn.get_attribute("disabled") is not None or (
                (btn.get_attribute("aria-disabled") or "").lower() == "true"
            )
            is_enabled = not disabled
            if is_enabled == want_enabled:
                return True, f"button enabled={is_enabled} (matches {expected_text})"
            return False, f"button enabled={is_enabled} (expected {expected_text})"
        except NoSuchElementException:
            return False, "modal submit button not found"

    page_text = driver.find_element(By.TAG_NAME, "body").text
    if expected_text in page_text:
        idx = page_text.find(expected_text)
        snippet = page_text[max(0, idx - 30): idx + len(expected_text) + 30]
        return True, snippet.replace("\n", " ").strip()[:200]
    return False, page_text[:120].replace("\n", " ").strip()


# ---------------------------------------------------------------------------
# Per-test-case execution
# ---------------------------------------------------------------------------
def run_one(driver, row, course_id: int) -> dict:
    tc_id = row.get("tc_id", "UNKNOWN")
    action = infer_action(row)
    expected_result = row.get("expected_result", "")
    started = time.time()
    screenshot_path = ""
    actual_status = ""
    notes = ""

    try:
        handler = ACTIONS.get(action)
        if handler is None:
            actual_status = "ERROR"
            notes = f"Unknown action: {action!r}"
        else:
            handler(driver, row, course_id)
            matched, evidence = check_expected(driver, expected_result)
            actual_status = "PASS" if matched else "FAIL"
            notes = evidence

    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        actual_status = "ERROR"
        notes = f"{type(e).__name__}: {str(e).splitlines()[0][:120]}"
    except Exception as e:
        actual_status = "ERROR"
        notes = f"Unexpected: {type(e).__name__}: {e}"
        traceback.print_exc()

    if actual_status != "PASS":
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"{tc_id}.png")
        try:
            driver.save_screenshot(screenshot_path)
        except Exception:
            screenshot_path = "(screenshot failed)"

    duration = f"{time.time() - started:.2f}s"
    actual_text = f"{notes} (action={action}; duration={duration})"

    return {
        "run_id": RUN_ID,
        "run_date": RUN_DATE,
        "feature_id": FEATURE_ID,
        "tc_id": tc_id,
        "level": LEVEL,
        "expected_result": expected_result,
        "actual_result": actual_text,
        "status": actual_status,
        "screenshot_path": screenshot_path,
        "error_message": actual_text if actual_status != "PASS" else "",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="F005 Enroll Users - Level 1 Test Runner",
        epilog=(
            "Examples:\n"
            "  python f005_enroll_users_level1.py                # run all TCs\n"
            "  python f005_enroll_users_level1.py --tc-id TC-005-001"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tc-id", type=str, help="Run only the specified TC ID")
    args = parser.parse_args()

    if not os.path.exists(DATA_CSV):
        print(f"ERROR: data file not found: {DATA_CSV}")
        sys.exit(1)

    rows = read_csv(DATA_CSV)
    if not rows:
        print(f"ERROR: {DATA_CSV} is empty")
        sys.exit(1)

    if args.tc_id:
        rows = [r for r in rows if r.get("tc_id") == args.tc_id]
        if not rows:
            print(f"ERROR: TC ID '{args.tc_id}' not found in {DATA_CSV}")
            sys.exit(1)

    Path(RESULT_CSV).unlink(missing_ok=True)
    Path(RESULT_CSV).parent.mkdir(parents=True, exist_ok=True)

    tc_info = f" ({args.tc_id})" if args.tc_id else ""
    print(f"Running {len(rows)} test cases for F005 (Enroll Users){tc_info}...")
    print(f"Browser: chrome | Base URL: {BASE_URL}\n")

    driver = create_driver()
    pass_count = fail_count = 0

    try:
        try:
            login_to_moodle(driver)
        except Exception as e:
            print(f"ERROR: manager login failed: {type(e).__name__}: {e}. Aborting.")
            sys.exit(2)

        course_id = ensure_test_course(driver)

        for i, row in enumerate(rows, 1):
            tc_id = row.get("tc_id", f"row{i}")
            action = infer_action(row)
            print(f"[{i}/{len(rows)}] {tc_id} ({action}) ...")

            # Pre-test cleanup: if this is an enroll, make sure the user
            # isn't already on the participants list from a prior TC.
            if action == "enroll":
                user_search = (row.get("user_search") or "").strip()
                if user_search:
                    print(f"   [Orchestrator] clearing '{user_search}' if already enrolled...")
                    try:
                        action_unenroll(driver, row, course_id)
                    except Exception as ce:
                        print(f"   [Orchestrator] cleanup warning: {type(ce).__name__}")

            print(f"   Executing ... ", end="", flush=True)
            result = run_one(driver, row, course_id)
            write_results(RESULT_CSV, [result])

            status = result["status"]
            evidence_short = result["actual_result"][:60]
            print(f"{status}  ({evidence_short})")
            if status == "PASS":
                pass_count += 1
            else:
                fail_count += 1

    finally:
        driver.quit()

    print("\n" + "=" * 60)
    print(f"F005 SUMMARY: {pass_count} PASS / {fail_count} FAIL  (total {len(rows)})")
    print(f"Results: {RESULT_CSV}")
    print(f"Screenshots: {SCREENSHOT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
