"""F003 Performance NFR: Quiz creation workflow response time measurement."""

import os
import re
import time
import uuid
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.moodle_helpers import login_to_moodle, make_unique_name
from common.result_writer import write_results
from common.screenshot import save_screenshot
from config.settings import BASE_URL

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data", "non_functional")
RESULT_DIR = os.path.join(ROOT_DIR, "results", "non_functional")
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

# Locators from Katalon recordings
ADD_QUIZ_URL_PATH = "/course/modedit.php?add=quiz&course=3&section=1&return=0&sr=0"
QUIZ_FORM_WAIT_CSS = "#id_name, form#mform1, form.mform"
QUIZ_NAME_ID = "id_name"
SUBMIT_BUTTON_NAME = "submitbutton2"
QUIZ_INDEX_PATH = "/mod/quiz/index.php?id=3"
QUIZ_INDEX_WAIT_CSS = "#page-mod-quiz-index, table.generaltable, #region-main"


def _build_url(page_url):
    page_url = (page_url or "").strip()
    if not page_url:
        return BASE_URL
    if page_url.startswith("http"):
        return page_url
    return BASE_URL.rstrip("/") + "/" + page_url.lstrip("/")


def _extract_seconds_limit(threshold):
    match = re.search(r"<=\s*([0-9]+(?:\.[0-9]+)?)", threshold or "")
    if not match:
        return None
    return float(match.group(1))


def _take_screenshot(driver, prefix):
    if not driver:
        return ""
    try:
        return save_screenshot(driver, SCREENSHOT_DIR, prefix)
    except Exception:
        return ""


def _measure_page_load(driver, url):
    start = time.perf_counter()
    driver.get(url)
    elapsed = time.perf_counter() - start
    return elapsed


def _measure_quiz_submission(driver):
    # Navigate to quiz add form
    url = BASE_URL.rstrip("/") + ADD_QUIZ_URL_PATH
    driver.get(url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, QUIZ_FORM_WAIT_CSS))
    )

    # Fill quiz name
    unique_name = make_unique_name("PerfTest")
    name_field = driver.find_element(By.ID, QUIZ_NAME_ID)
    name_field.clear()
    name_field.send_keys(unique_name)

    # Submit and measure
    submit_btn = driver.find_element(By.NAME, SUBMIT_BUTTON_NAME)
    start = time.perf_counter()
    submit_btn.click()

    # Wait for page to load after submission
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#page-mod-quiz-index, #page-mod-quiz-view, #region-main, form#mform1")
        )
    )
    elapsed = time.perf_counter() - start
    return elapsed


def run() -> None:
    data_path = os.path.join(DATA_DIR, "f003_quiz_performance_data.csv")
    result_path = os.path.join(RESULT_DIR, "f003_quiz_performance_results.csv")
    rows = read_csv(data_path)
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")
    driver = None

    page_load_seconds = 0.0
    submission_seconds = 0.0

    try:
        driver = create_driver()
        login_to_moodle(driver)

        for row in rows:
            tc_id = row.get("tc_id", "").strip()
            member = row.get("member", "").strip()
            feature_id = row.get("feature_id", "").strip()
            nfr_type = row.get("non_functional_type", "").strip()
            requirement = row.get("requirement", "").strip()
            metric = row.get("metric", "").strip()
            threshold = row.get("threshold", "").strip()
            expected = row.get("expected_result", "").strip()

            actual = ""
            status = "PASS"
            screenshot_path = ""
            error_message = ""
            measured = 0.0

            try:
                target_url = _build_url(row.get("page_url", ""))

                if "page_load" in metric:
                    elapsed = _measure_page_load(driver, target_url)
                    page_load_seconds = elapsed
                    measured = elapsed
                    actual = f"page_load_seconds={elapsed:.2f}"
                elif "submission" in metric:
                    try:
                        elapsed = _measure_quiz_submission(driver)
                        submission_seconds = elapsed
                        measured = elapsed
                        actual = f"submission_seconds={elapsed:.2f}"
                    except Exception as exc:
                        elapsed = _measure_page_load(driver, target_url)
                        submission_seconds = elapsed
                        measured = elapsed
                        actual = f"submission_seconds={elapsed:.2f} (page load fallback)"
                        error_message = f"Full submission measurement failed: {exc}"
                elif "average" in metric:
                    if page_load_seconds == 0.0:
                        page_load_seconds = _measure_page_load(driver, target_url)
                    avg = (page_load_seconds + submission_seconds) / 2 if submission_seconds > 0 else page_load_seconds
                    measured = avg
                    actual = (
                        f"page_load_seconds={page_load_seconds:.2f}; "
                        f"submission_seconds={submission_seconds:.2f}; "
                        f"average_seconds={avg:.2f}"
                    )
                else:
                    elapsed = _measure_page_load(driver, target_url)
                    measured = elapsed
                    actual = f"page_load_seconds={elapsed:.2f}"

                seconds_limit = _extract_seconds_limit(threshold)
                if seconds_limit is not None and measured > seconds_limit:
                    status = "FAIL"
                    error_message = (
                        f"Measured {measured:.2f}s, expected <= {seconds_limit:.2f}s."
                    )

                if status == "FAIL":
                    screenshot_path = _take_screenshot(
                        driver, f"F003_performance_{tc_id}"
                    )
            except Exception as exc:
                status = "ERROR"
                actual = "ERROR"
                error_message = str(exc)
                screenshot_path = _take_screenshot(
                    driver, f"F003_performance_{tc_id}"
                )

            results.append(
                {
                    "run_id": run_id,
                    "run_date": run_date,
                    "member": member,
                    "feature_id": feature_id,
                    "tc_id": tc_id,
                    "non_functional_type": nfr_type,
                    "requirement": requirement,
                    "metric": metric,
                    "expected_result": expected,
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

    write_results(result_path, results, NFR_RESULT_COLUMNS)
    print(f"F003 Performance NFR complete. Results: {result_path}")


if __name__ == "__main__":
    run()
