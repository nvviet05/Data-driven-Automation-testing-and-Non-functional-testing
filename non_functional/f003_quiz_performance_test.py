"""F003 Performance NFR: quiz creation workflow response time."""

import os
import re
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
DATA_PATH = os.path.join(ROOT_DIR, "data", "non_functional", "f003_quiz_performance_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "non_functional", "f003_quiz_performance_results.csv")
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

ADD_QUIZ_URL_PATH = "/course/modedit.php?add=quiz&course=3&section=1&return=0&sr=0"
QUIZ_INDEX_PATH = "/mod/quiz/index.php?id=3"
QUIZ_FORM_WAIT_CSS = "#id_name, form#mform1, form.mform"
QUIZ_INDEX_WAIT_CSS = "#page-mod-quiz-index, table.generaltable, #region-main"
ERROR_SELECTORS = "#id_error_name, #id_error_timelimit, .invalid-feedback, .error"


def _threshold_seconds(row: dict, default: float = 8.0) -> float:
    match = re.search(r"<=\s*([0-9]+(?:\.[0-9]+)?)", row.get("threshold", ""))
    return float(match.group(1)) if match else default


def _parse_input(row: dict, key: str, default: str = "") -> str:
    for column in ("input_1", "input_2", "input_3"):
        value = row.get(column, "").strip()
        if value.startswith(f"{key}="):
            return value.split("=", 1)[1].strip()
    return default


def _xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"


def _take_screenshot(driver, prefix):
    try:
        return save_screenshot(driver, SCREENSHOT_DIR, prefix) if driver else ""
    except Exception:
        return ""


def _set_time_limit(driver, minutes: str):
    if not minutes:
        return
    try:
        checkbox = driver.find_element(By.ID, "id_timelimit_enabled")
        if not checkbox.is_selected():
            checkbox.click()
    except Exception:
        pass
    driver.execute_script(
        """
        var cb = document.getElementById('id_timelimit_enabled');
        if (cb && !cb.checked) {
            cb.checked = true;
            cb.dispatchEvent(new Event('change', {bubbles: true}));
        }
        var e = document.getElementById('id_timelimit_number');
        if (e) {
            e.removeAttribute('disabled');
            e.value = arguments[0];
            e.dispatchEvent(new Event('input', {bubbles: true}));
            e.dispatchEvent(new Event('change', {bubbles: true}));
        }
        """,
        minutes,
    )
    try:
        Select(driver.find_element(By.ID, "id_timelimit_timeunit")).select_by_visible_text("minutes")
    except Exception:
        pass


def _set_attempts(driver, attempts: str):
    if not attempts:
        return
    try:
        selector = Select(driver.find_element(By.ID, "id_attempts"))
        if attempts == "0":
            selector.select_by_visible_text("Unlimited")
        else:
            try:
                selector.select_by_visible_text(attempts)
            except Exception:
                selector.select_by_value(attempts)
    except Exception:
        pass


def _visible_errors(driver) -> str:
    messages = []
    for element in driver.find_elements(By.CSS_SELECTOR, ERROR_SELECTORS):
        try:
            if element.is_displayed():
                messages.append(element.text.strip() or "validation selector visible")
        except Exception:
            continue
    return "; ".join(messages)


def _verify_quiz_created(driver, quiz_name: str) -> bool:
    driver.get(BASE_URL.rstrip("/") + QUIZ_INDEX_PATH)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, QUIZ_INDEX_WAIT_CSS))
    )
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(normalize-space(.), {_xpath_literal(quiz_name)})]")
        )
    )
    return True


def _measure_workflow(driver, row: dict) -> dict:
    add_url = BASE_URL.rstrip("/") + ADD_QUIZ_URL_PATH
    quiz_name = make_unique_name(_parse_input(row, "quiz_name", "PerfTest"))

    page_start = time.perf_counter()
    driver.get(add_url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, QUIZ_FORM_WAIT_CSS))
    )
    page_load_seconds = time.perf_counter() - page_start

    name_field = driver.find_element(By.ID, "id_name")
    name_field.clear()
    name_field.send_keys(quiz_name)
    _set_time_limit(driver, _parse_input(row, "time_limit", "10"))
    _set_attempts(driver, _parse_input(row, "attempts", "1"))

    submit_start = time.perf_counter()
    driver.find_element(By.NAME, "submitbutton2").click()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#page-mod-quiz-view, #page-mod-quiz-index, #region-main, form#mform1")
        )
    )
    submission_seconds = time.perf_counter() - submit_start

    error_text = _visible_errors(driver)
    if error_text:
        return {
            "created": False,
            "quiz_name": quiz_name,
            "page_load_seconds": page_load_seconds,
            "submission_seconds": submission_seconds,
            "average_seconds": (page_load_seconds + submission_seconds) / 2,
            "error": f"Validation error: {error_text}",
        }

    created = _verify_quiz_created(driver, quiz_name)
    return {
        "created": created,
        "quiz_name": quiz_name,
        "page_load_seconds": page_load_seconds,
        "submission_seconds": submission_seconds,
        "average_seconds": (page_load_seconds + submission_seconds) / 2,
        "error": "",
    }


def run() -> None:
    rows = read_csv(DATA_PATH)
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")
    driver = None

    try:
        driver = create_driver()
        login_to_moodle(driver)

        for row in rows:
            tc_id = row.get("tc_id", "").strip()
            screenshot_path = ""
            error_message = ""
            actual = ""
            status = "PASS"

            try:
                metrics = _measure_workflow(driver, row)
                limit = _threshold_seconds(row)
                actual = (
                    f"quiz_name={metrics['quiz_name']}; "
                    f"page_load_seconds={metrics['page_load_seconds']:.2f}; "
                    f"submission_seconds={metrics['submission_seconds']:.2f}; "
                    f"average_seconds={metrics['average_seconds']:.2f}"
                )
                if not metrics["created"]:
                    status = "FAIL"
                    error_message = metrics["error"] or "Quiz was not created"
                elif metrics["average_seconds"] > limit:
                    status = "FAIL"
                    error_message = (
                        f"Average {metrics['average_seconds']:.2f}s exceeded {limit:.2f}s"
                    )
                if status == "FAIL":
                    screenshot_path = _take_screenshot(driver, f"F003_performance_{tc_id}")
            except Exception as exc:
                status = "ERROR"
                actual = "ERROR"
                error_message = str(exc)
                screenshot_path = _take_screenshot(driver, f"F003_performance_{tc_id}")

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
                    "screenshot_path": _take_screenshot(driver, "F003_performance_fatal"),
                    "error_message": str(exc),
                }
            )
    finally:
        close_driver(driver)

    if os.path.exists(RESULT_PATH):
        os.remove(RESULT_PATH)
    write_results(RESULT_PATH, results, NFR_RESULT_COLUMNS)
    print(f"F003 Performance NFR complete. Results: {RESULT_PATH}")


if __name__ == "__main__":
    run()
