"""
f005_enroll_users_level2.py
---------------------------
Level 2 data-driven script for F005 - User Enrollment.

Differs from f005_enroll_users_level1.py in one way only: every URL and
element locator is read from data/level2/f005_level2_data.csv. The flow,
action inference, advanced-options logic, and verification are identical.

Reads:
  data/level1/f005_enroll_users.csv   - test cases (same as Level 1)
  data/level2/f005_level2_data.csv    - URLs + element locators

Writes:
  results/level2/f005_results.csv
  resources/screenshots/<tc_id>_L2.png  (on FAIL only)

Locator CSV schema
------------------
field_name, locator_type, locator_value

locator_type:
  url        -> a URL the script will driver.get() to. May contain
                {COURSE_ID} which is substituted at runtime.
  id, css, xpath, link_text, name -> their respective Selenium By types.
"""

import os
import sys
import csv
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


DATA_CSV   = os.path.join("data", "level1", "f005_level1_data.csv")
CONFIG_CSV = os.path.join("data", "level2", "f005_level2_data.csv")
RESULT_CSV = os.path.join("results", "level2", "f005_results.csv")
SCREENSHOT_DIR = os.path.join("resources", "screenshots")

FEATURE_ID = "F005"
LEVEL = "level2"
RUN_ID = uuid.uuid4().hex[:8]
RUN_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Locator dictionary
# ---------------------------------------------------------------------------
BY_MAP = {
    "id":        By.ID,
    "css":       By.CSS_SELECTOR,
    "xpath":     By.XPATH,
    "link_text": By.LINK_TEXT,
    "name":      By.NAME,
}


def load_config(path: str) -> dict:
    config = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            field = (row.get("field_name") or "").strip()
            if not field:
                continue
            config[field] = {
                "locator_type":  (row.get("locator_type") or "").strip().lower(),
                "locator_value": (row.get("locator_value") or "").strip(),
            }
    return config


def url_of(config: dict, field: str, course_id: int = 0) -> str:
    """Return a URL. Substitutes {COURSE_ID} with the runtime course id."""
    entry = config[field]
    if entry["locator_type"] != "url":
        raise ValueError(f"Config field '{field}' is not a URL")
    return entry["locator_value"].replace("{COURSE_ID}", str(course_id))


def _by_for(config: dict, field: str):
    entry = config[field]
    return BY_MAP[entry["locator_type"]], entry["locator_value"]


def find_field(driver, config, field):
    by, val = _by_for(config, field)
    return driver.find_element(by, val)


def find_all(driver, config, field):
    by, val = _by_for(config, field)
    return driver.find_elements(by, val)


def wait_for_field(driver, config, field, timeout: int = 10):
    by, val = _by_for(config, field)
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, val))
    )


def wait_clickable(driver, config, field, timeout: int = 10):
    by, val = _by_for(config, field)
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, val))
    )


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
    driver.execute_script(
        "arguments[0].removeAttribute('maxlength');"
        "arguments[0].value = arguments[1];"
        "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
        "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
        element, value,
    )


# ---------------------------------------------------------------------------
# Action inference (identical to Level 1)
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
# Course setup
# ---------------------------------------------------------------------------
def ensure_test_course(driver, config) -> int:
    env_id = os.environ.get("MOODLE_TEST_COURSE_ID", "").strip()
    if env_id.isdigit():
        return int(env_id)

    stamp = datetime.now().strftime("%H%M%S")
    full = f"F005 L2 Course {stamp}"
    short = f"F005L2{stamp}"

    driver.get(url_of(config, "new_course_url"))
    wait_for_field(driver, config, "new_course_fullname", timeout=15)
    find_field(driver, config, "new_course_fullname").send_keys(full)
    find_field(driver, config, "new_course_shortname").send_keys(short)
    safe_click(driver, find_field(driver, config, "new_course_save"))

    WebDriverWait(driver, 15).until(EC.url_contains("/course/view.php"))
    url = driver.current_url
    cid = url.split("id=")[-1].split("&")[0]
    print(f"[setup] Created test course {short} (id={cid})")
    return int(cid)


# ---------------------------------------------------------------------------
# Page navigation
# ---------------------------------------------------------------------------
def goto_participants(driver, config, course_id: int):
    driver.get(url_of(config, "participants_url", course_id))
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )


def goto_enrolment_methods(driver, config, course_id: int):
    driver.get(url_of(config, "enrolment_methods_url", course_id))
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )


# ---------------------------------------------------------------------------
# Enrol-dialog helpers (use config locators)
# ---------------------------------------------------------------------------
def _open_enrol_dialog(driver, config):
    time.sleep(1)
    btn = wait_clickable(driver, config, "open_enrol_modal", timeout=8)
    safe_click(driver, btn)
    wait_for_field(driver, config, "modal_content", timeout=10)
    time.sleep(0.5)


def _type_user_search(driver, config, query: str):
    search = wait_clickable(driver, config, "user_search", timeout=10)
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
def action_enroll(driver, config, row, course_id):
    goto_participants(driver, config, course_id)
    _open_enrol_dialog(driver, config)

    user_search = (row.get("user_search") or "").strip()
    role = (row.get("role") or "Student").strip()

    _type_user_search(driver, config, user_search)

    try:
        suggestion = wait_clickable(driver, config, "user_search_first_option", timeout=5)
        suggestion.click()
        time.sleep(0.5)
    except TimeoutException:
        print(f"   Warning: no suggestion dropdown for '{user_search}'")

    if role:
        try:
            Select(find_field(driver, config, "role_select")).select_by_visible_text(role)
        except Exception as e:
            print(f"   Note: could not set role '{role}': {e}")

    _apply_advanced_options(driver, config, row)

    try:
        confirm_btn = wait_clickable(driver, config, "modal_submit", timeout=5)
        safe_click(driver, confirm_btn)
        time.sleep(2.0)
    except TimeoutException:
        raise NoSuchElementException("Modal-footer submit button not clickable")


def _apply_advanced_options(driver, config, row):
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
        toggler = find_field(driver, config, "more_toggler")
        if "moreless-less" not in (toggler.get_attribute("class") or ""):
            safe_click(driver, toggler)
            time.sleep(0.5)
    except NoSuchElementException:
        pass

    if start_date_value:
        try:
            Select(find_field(driver, config, "startdate")).select_by_value(start_date_value)
        except Exception as e:
            print(f"   Note: could not set start date: {e}")

    if n_days is not None and 1 <= n_days <= 365:
        try:
            Select(find_field(driver, config, "duration")).select_by_visible_text(f"{n_days} days")
        except Exception as e:
            print(f"   Note: could not set duration '{duration_days}': {e}")

    if toggle_end_date:
        try:
            cb = find_field(driver, config, "timeend_enabled")
            if not cb.is_selected():
                safe_click(driver, cb)
                time.sleep(0.3)
            if end_year:
                Select(find_field(driver, config, "timeend_year")).select_by_value(end_year)
        except Exception as e:
            print(f"   Note: could not configure end date: {e}")


def action_search_only(driver, config, row, course_id):
    goto_participants(driver, config, course_id)
    _open_enrol_dialog(driver, config)
    _type_user_search(driver, config, (row.get("user_search") or "").strip())


def action_empty_search_check(driver, config, row, course_id):
    goto_participants(driver, config, course_id)
    _open_enrol_dialog(driver, config)
    _type_user_search(driver, config, "")


def action_unenroll(driver, config, row, course_id):
    goto_participants(driver, config, course_id)
    user_search = (row.get("user_search") or "").strip()
    if not user_search:
        return

    try:
        filter_input = wait_clickable(driver, config, "participants_filter", timeout=8)
        filter_input.clear()
        filter_input.send_keys(user_search + Keys.RETURN)
        time.sleep(2.0)
    except Exception:
        pass

    # The implicit wait (10s) compounds badly inside the per-row loop below:
    # any row missing span.userinitials would stall for 10s. Disable it here.
    driver.implicitly_wait(0)
    try:
        rows = find_all(driver, config, "participants_row")
        if not rows:
            return

        needle = user_search.lower()
        target = None
        for r in rows:
            try:
                badge = r.find_element(By.CSS_SELECTOR, "span.userinitials")
                title = (badge.get_attribute("title") or "").lower()
                aria  = (badge.get_attribute("aria-label") or "").lower()
                if needle in title or needle in aria:
                    target = r
                    break
            except NoSuchElementException:
                continue
        if target is None:
            return

        unenrol_entry = config["unenrol_link"]
        unenrol_by = BY_MAP[unenrol_entry["locator_type"]]
        try:
            trash = target.find_element(unenrol_by, unenrol_entry["locator_value"])
        except NoSuchElementException:
            return
        safe_click(driver, trash)
    finally:
        driver.implicitly_wait(10)

    try:
        confirm_btn = wait_clickable(driver, config, "unenrol_confirm", timeout=5)
        safe_click(driver, confirm_btn)
        time.sleep(2.0)
    except (TimeoutException, NoSuchElementException):
        pass


def action_enable_self_enrol(driver, config, row, course_id):
    goto_enrolment_methods(driver, config, course_id)
    enrol_key = (row.get("enrol_key") or "").strip()
    bypass = (row.get("bypass_maxlength") or "").strip().lower()

    # Try to open the existing Self-enrolment edit form.
    edit_link = None
    try:
        edit_link = find_field(driver, config, "self_enrol_edit_link")
    except NoSuchElementException:
        pass

    if edit_link is None:
        # Self-enrolment instance doesn't exist yet — add via the Add method dropdown.
        try:
            Select(find_field(driver, config, "add_method_select")).select_by_visible_text(
                "Self enrolment"
            )
            time.sleep(1.5)
        except (NoSuchElementException, Exception):
            return
    else:
        safe_click(driver, edit_link)
        time.sleep(1.0)

    if enrol_key:
        try:
            key_field = find_field(driver, config, "self_enrol_password")
            try:
                show = find_field(driver, config, "self_enrol_unmask")
                safe_click(driver, show)
            except NoSuchElementException:
                pass
            key_field.clear()
            if bypass == "enrol_key":
                _set_via_js(driver, key_field, enrol_key)
            else:
                key_field.send_keys(enrol_key)
        except NoSuchElementException:
            pass

    try:
        safe_click(driver, find_field(driver, config, "self_enrol_submit"))
        time.sleep(1.5)
    except NoSuchElementException:
        pass


ACTIONS = {
    "enroll":             action_enroll,
    "search_only":        action_search_only,
    "empty_search_check": action_empty_search_check,
    "enable_self_enrol":  action_enable_self_enrol,
}


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def check_expected(driver, config, expected_text: str):
    if not expected_text:
        return True, "(no expected_result specified)"

    # Special assertion: expected "attr:false" means the modal Enrol button
    # should be disabled (e.g., when the search box is empty).
    if expected_text.startswith("attr:"):
        want_enabled = expected_text.split(":", 1)[1].strip().lower() == "true"
        try:
            btn = find_field(driver, config, "modal_submit")
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
def run_one(driver, config, row, course_id) -> dict:
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
            handler(driver, config, row, course_id)
            matched, evidence = check_expected(driver, config, expected_result)
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
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"{tc_id}_L2.png")
        try:
            driver.save_screenshot(screenshot_path)
        except Exception:
            screenshot_path = "(screenshot failed)"

    duration = f"{time.time() - started:.2f}s"
    actual_text = f"{notes} (L2; action={action}; duration={duration})"

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
        description="F005 Enroll Users - Level 2 Test Runner",
        epilog=(
            "Examples:\n"
            "  python f005_enroll_users_level2.py                # run all TCs\n"
            "  python f005_enroll_users_level2.py --tc-id TC-005-001"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tc-id", type=str, help="Run only the specified TC ID")
    args = parser.parse_args()

    if not os.path.exists(DATA_CSV):
        print(f"ERROR: data file not found: {DATA_CSV}")
        sys.exit(1)
    if not os.path.exists(CONFIG_CSV):
        print(f"ERROR: config file not found: {CONFIG_CSV}")
        sys.exit(1)

    config = load_config(CONFIG_CSV)
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
    print(f"Running {len(rows)} test cases for F005 (Enroll Users, Level 2){tc_info}...")
    print(f"Config file: {CONFIG_CSV}")
    print(f"Loaded {len(config)} field locators.\n")

    driver = create_driver()
    pass_count = fail_count = 0

    try:
        try:
            login_to_moodle(driver)
        except Exception as e:
            print(f"ERROR: manager login failed: {type(e).__name__}: {e}. Aborting.")
            sys.exit(2)

        course_id = ensure_test_course(driver, config)

        for i, row in enumerate(rows, 1):
            tc_id = row.get("tc_id", f"row{i}")
            action = infer_action(row)
            print(f"[{i}/{len(rows)}] {tc_id} ({action}) ...")

            if action == "enroll":
                user_search = (row.get("user_search") or "").strip()
                if user_search:
                    print(f"   [Orchestrator] clearing '{user_search}' if already enrolled...")
                    try:
                        action_unenroll(driver, config, row, course_id)
                    except Exception as ce:
                        print(f"   [Orchestrator] cleanup warning: {type(ce).__name__}")

            print(f"   Executing ... ", end="", flush=True)
            result = run_one(driver, config, row, course_id)
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
    print(f"F005 LEVEL 2 SUMMARY: {pass_count} PASS / {fail_count} FAIL  (total {len(rows)})")
    print(f"Results: {RESULT_CSV}")
    print(f"Screenshots: {SCREENSHOT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()