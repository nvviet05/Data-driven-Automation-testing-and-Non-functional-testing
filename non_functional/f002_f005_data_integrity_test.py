"""F002/F005 Data Integrity NFR: workflow state and record consistency.

Verifies two data-integrity aspects for F002 (Create Course) and F005 (Enrol
Users):
    - state_consistency  : the final UI state matches the data that was
                           submitted (course details page reflects the
                           entered values; participants list reflects the
                           enrolled user).
    - record_consistency : the recorded role / metadata matches what the
                           tester selected (no silent role drift, no name
                           mutation).

Reads:   data/non_functional/f002_f005_data_integrity_data.csv
Writes:  results/non_functional/f002_f005_data_integrity_results.csv
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
DATA_PATH = os.path.join(ROOT_DIR, "data", "non_functional", "f002_f005_data_integrity_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "non_functional", "f002_f005_data_integrity_results.csv")
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

DEFAULT_COURSE_ID = "3"


def _parse_input(row: dict, key: str, default: str = "") -> str:
    for column in ("input_1", "input_2", "input_3"):
        value = (row.get(column) or "").strip()
        if value.startswith(f"{key}="):
            return value.split("=", 1)[1].strip()
    return default


def _unique_suffix() -> str:
    return datetime.now().strftime("%H%M%S") + uuid.uuid4().hex[:4]


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


def _safe_click(driver, element):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", element
        )
        time.sleep(0.2)
        element.click()
    except WebDriverException:
        driver.execute_script("arguments[0].click();", element)


def _check_course_data_integrity(driver, row: dict) -> dict:
    base_full = _parse_input(row, "full_name", "Integrity Course")
    base_short = _parse_input(row, "short_name", "INTEG")
    try:
        category_index = int(_parse_input(row, "category_index", "1") or "1")
    except ValueError:
        category_index = 1

    suffix = _unique_suffix()
    full_name = f"{base_full} {suffix}"
    short_name = f"{base_short}{suffix}"

    driver.get(BASE_URL.rstrip("/") + "/course/edit.php?category=1")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "id_fullname"))
    )

    fn = driver.find_element(By.ID, "id_fullname")
    fn.clear()
    fn.send_keys(full_name)

    sn = driver.find_element(By.ID, "id_shortname")
    sn.clear()
    sn.send_keys(short_name)

    try:
        Select(driver.find_element(By.ID, "id_category")).select_by_index(category_index)
    except (NoSuchElementException, Exception):
        pass

    save_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "id_saveanddisplay"))
    )
    _safe_click(driver, save_btn)

    WebDriverWait(driver, 20).until(EC.url_contains("/course/view.php"))

    # state_consistent: the user-facing course view page renders the full name
    # we just submitted.
    page_text = driver.find_element(By.TAG_NAME, "body").text or ""
    full_name_match = full_name in page_text

    # record_consistent: re-open the course edit form and read the persisted
    # short name from id_shortname. Moodle does not render the short name on
    # /course/view.php, so checking body.text alone would always FAIL.
    course_id = driver.current_url.split("id=")[-1].split("&")[0]
    persisted_short_name = ""
    short_name_match = False
    try:
        driver.get(f"{BASE_URL.rstrip('/')}/course/edit.php?id={course_id}")
        sn_after = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "id_shortname"))
        )
        persisted_short_name = (sn_after.get_attribute("value") or "").strip()
        short_name_match = persisted_short_name == short_name
    except (TimeoutException, NoSuchElementException):
        pass

    return {
        "submitted_full_name": full_name,
        "submitted_short_name": short_name,
        "full_name_match": full_name_match,
        "short_name_match": short_name_match,
        "persisted_short_name": persisted_short_name,
        "state_consistent": full_name_match,
        "record_consistent": short_name_match,
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
            _safe_click(driver, btn)
            break
        except (TimeoutException, NoSuchElementException):
            continue
    else:
        raise NoSuchElementException("Enrol users button not found")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-content"))
    )
    time.sleep(0.5)


def _enrol_user(driver, course_id: str, user_search: str, role: str) -> None:
    driver.get(f"{BASE_URL.rstrip('/')}/user/index.php?id={course_id}")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    _open_enrol_dialog(driver)

    search = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            ".modal-body input[placeholder='Search'], "
            ".form-autocomplete-input input[type='text']",
        ))
    )
    search.click()
    search.clear()
    search.send_keys(user_search)
    time.sleep(2.0)

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
        pass

    try:
        Select(driver.find_element(By.ID, "id_roletoassign")).select_by_visible_text(role)
    except Exception:
        pass

    confirm_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            ".modal-footer button[data-action='save'], .modal-footer .btn-primary",
        ))
    )
    _safe_click(driver, confirm_btn)
    time.sleep(2.0)


def _find_user_row(driver, user_search: str):
    needle = user_search.lower()
    rows = driver.find_elements(
        By.XPATH,
        "//*[@id='participants']/tbody/tr[starts-with(@id, 'user-index-participants-')]",
    )
    for row in rows:
        try:
            text = (row.text or "").lower()
            if needle in text:
                return row
        except Exception:
            continue
    return None


def _check_enrol_data_integrity(driver, row: dict) -> dict:
    course_id = _parse_input(row, "course_id", DEFAULT_COURSE_ID)
    user_search = _parse_input(row, "user_search", "sam")
    role = _parse_input(row, "role", "Student")

    _enrol_user(driver, course_id, user_search, role)

    driver.get(f"{BASE_URL.rstrip('/')}/user/index.php?id={course_id}")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    user_row = _find_user_row(driver, user_search)
    user_present = user_row is not None
    role_match = False
    observed_role = ""

    if user_row is not None:
        try:
            observed_role = (user_row.text or "").strip()
            role_match = role.lower() in observed_role.lower()
        except Exception:
            role_match = False

    return {
        "submitted_user": user_search,
        "submitted_role": role,
        "user_present": user_present,
        "role_match": role_match,
        "observed_text": observed_role[:160],
        "state_consistent": user_present,
        "record_consistent": role_match,
    }


def _execute_row(driver, row: dict) -> dict:
    feature_id = (row.get("feature_id") or "").strip().upper()
    if feature_id.startswith("F002"):
        return _check_course_data_integrity(driver, row)
    if feature_id.startswith("F005"):
        return _check_enrol_data_integrity(driver, row)
    raise ValueError(f"Unsupported feature_id for data integrity test: {feature_id!r}")


def _format_actual(outcome: dict, feature_id: str) -> str:
    if feature_id.upper().startswith("F002"):
        return (
            f"submitted_full_name={outcome['submitted_full_name']}; "
            f"submitted_short_name={outcome['submitted_short_name']}; "
            f"persisted_short_name={outcome.get('persisted_short_name', '')}; "
            f"full_name_match={str(outcome['full_name_match']).lower()}; "
            f"short_name_match={str(outcome['short_name_match']).lower()}"
        )
    return (
        f"submitted_user={outcome['submitted_user']}; "
        f"submitted_role={outcome['submitted_role']}; "
        f"user_present={str(outcome['user_present']).lower()}; "
        f"role_match={str(outcome['role_match']).lower()}; "
        f"observed={outcome['observed_text']}"
    )


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
            raise RuntimeError("manager login failed for data integrity test run.") from exc

        for row in rows:
            tc_id = (row.get("tc_id") or "").strip()
            feature_id = (row.get("feature_id") or "").strip()
            status = "PASS"
            error_message = ""
            screenshot_path = ""

            try:
                outcome = _execute_row(driver, row)
                actual = _format_actual(outcome, feature_id)

                if not outcome["state_consistent"] or not outcome["record_consistent"]:
                    status = "FAIL"
                    parts = []
                    if not outcome["state_consistent"]:
                        parts.append("state inconsistent with submitted data")
                    if not outcome["record_consistent"]:
                        parts.append("recorded role/short name differs from selected")
                    error_message = "; ".join(parts)
                    screenshot_path = _take_screenshot(driver, f"F002_F005_data_integrity_{tc_id}")
            except Exception as exc:
                status = "ERROR"
                actual = "ERROR"
                error_message = f"{type(exc).__name__}: {exc}"
                screenshot_path = _take_screenshot(driver, f"F002_F005_data_integrity_{tc_id}")

            results.append(
                {
                    "run_id": run_id,
                    "run_date": run_date,
                    "member": row.get("member", ""),
                    "feature_id": feature_id,
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
                    "screenshot_path": _take_screenshot(driver, "F002_F005_data_integrity_fatal"),
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
    print(f"F002/F005 Data Integrity NFR complete. Results: {RESULT_PATH}")


if __name__ == "__main__":
    run()
