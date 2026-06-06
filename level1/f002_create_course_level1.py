"""
f002_create_course_level1.py
----------------------------
Level 1 data-driven script for F002 - Create New Course.

Reads:   data/level1/f002_create_course.csv
Writes:  results/level1/f002_results.csv
         resources/screenshots/<tc_id>.png  (on FAIL only)

CSV schema
----------
tc_id, scenario, technique, full_name, short_name, course_id,
category_index, bypass_maxlength_field, expected_result

bypass_maxlength_field
    fullname | shortname | idnumber | (empty)
    When set, the script removes the HTML maxlength attribute on that field
    and assigns the value via JavaScript so we can submit values longer than
    the frontend would normally allow.

Scenario containing the word "cancel" clicks id_cancel instead of
id_saveanddisplay (used by TC-002-039).

A test PASSes if expected_result text is found on the resulting page.
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


DATA_CSV = os.path.join("data", "level1", "f002_level1_data.csv")
RESULT_CSV = os.path.join("results", "level1", "f002_results.csv")
SCREENSHOT_DIR = os.path.join("resources", "screenshots")

FEATURE_ID = "F002"
LEVEL = "level1"
RUN_ID = uuid.uuid4().hex[:8]
RUN_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _set_via_js(driver, element, value: str):
    driver.execute_script(
        "arguments[0].removeAttribute('maxlength');"
        "arguments[0].value = arguments[1];",
        element, value,
    )


def fill_course_form(driver, row, timeout: int = 10):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, "id_fullname"))
    )

    full_name = row.get("full_name", "")
    short_name = row.get("short_name", "")
    course_id = row.get("course_id", "")
    category_index = row.get("category_index", "").strip()
    bypass_field = (row.get("bypass_maxlength_field") or "").strip().lower()

    fn = driver.find_element(By.ID, "id_fullname")
    fn.clear()
    if full_name:
        if bypass_field == "fullname":
            _set_via_js(driver, fn, full_name)
        else:
            fn.send_keys(full_name)

    sn = driver.find_element(By.ID, "id_shortname")
    sn.clear()
    if short_name:
        if bypass_field == "shortname":
            _set_via_js(driver, sn, short_name)
        else:
            sn.send_keys(short_name)

    try:
        idn = driver.find_element(By.ID, "id_idnumber")
        idn.clear()
        if course_id:
            if bypass_field == "idnumber":
                _set_via_js(driver, idn, course_id)
            else:
                idn.send_keys(course_id)
    except NoSuchElementException:
        pass

    if category_index:
        try:
            sel = Select(driver.find_element(By.ID, "id_category"))
            sel.select_by_index(int(category_index))
        except (NoSuchElementException, ValueError):
            pass


def submit_form(driver, row, timeout: int = 10):
    scenario = (row.get("scenario") or "").lower()
    button_id = "id_cancel" if "cancel" in scenario else "id_saveanddisplay"

    btn = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.ID, button_id))
    )
    btn.click()
    time.sleep(1.5)


def check_expected(driver, expected_text: str):
    if not expected_text:
        return True, "(no expected_result specified)"

    page_text = driver.find_element(By.TAG_NAME, "body").text
    if expected_text in page_text:
        idx = page_text.find(expected_text)
        snippet = page_text[max(0, idx - 30): idx + len(expected_text) + 30]
        return True, snippet.replace("\n", " ").strip()[:200]

    for marker in [".error", ".alert-danger", ".form-control-feedback"]:
        try:
            err = driver.find_element(By.CSS_SELECTOR, marker)
            if err.text.strip():
                return False, err.text.strip()[:120]
        except NoSuchElementException:
            continue

    return False, page_text[:120].replace("\n", " ").strip()


def run_one(driver, row) -> dict:
    tc_id = row.get("tc_id", "UNKNOWN")
    expected_result = row.get("expected_result", "")
    started = time.time()
    screenshot_path = ""
    actual_status = ""
    notes = ""

    try:
        driver.get(f"{BASE_URL.rstrip('/')}/course/edit.php?category=1")
        fill_course_form(driver, row)
        submit_form(driver, row)
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
    actual_text = f"{notes} (duration={duration})"

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


def main():
    parser = argparse.ArgumentParser(
        description="F002 Create Course - Level 1 Test Runner",
        epilog=(
            "Examples:\n"
            "  python f002_create_course_level1.py                # run all TCs\n"
            "  python f002_create_course_level1.py --tc-id TC-002-001"
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
    print(f"Running {len(rows)} test cases for F002 (Create Course){tc_info}...")
    print(f"Browser: chrome | Base URL: {BASE_URL}\n")

    driver = create_driver()
    pass_count = fail_count = 0

    try:
        try:
            login_to_moodle(driver)
        except Exception as e:
            print(f"ERROR: manager login failed: {type(e).__name__}: {e}. Aborting.")
            sys.exit(2)

        for i, row in enumerate(rows, 1):
            tc_id = row.get("tc_id", f"row{i}")
            print(f"[{i}/{len(rows)}] {tc_id} ... ", end="", flush=True)

            result = run_one(driver, row)
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
    print(f"F002 SUMMARY: {pass_count} PASS / {fail_count} FAIL  (total {len(rows)})")
    print(f"Results: {RESULT_CSV}")
    print(f"Screenshots: {SCREENSHOT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
