import os
import re
import time
import uuid
from datetime import datetime
from urllib.parse import urljoin, urlparse

from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
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


def build_target_url(page_url: str) -> str:
    page_url = (page_url or "").strip()
    if not page_url:
        return BASE_URL
    if urlparse(page_url).scheme:
        return page_url
    return urljoin(BASE_URL.rstrip("/") + "/", page_url.lstrip("/"))


def extract_seconds_limit(threshold: str) -> float | None:
    match = re.search(r"<=\s*([0-9]+(?:\.[0-9]+)?)", threshold or "")
    if not match:
        return None
    return float(match.group(1))


def has_placeholder_data(row: dict) -> bool:
    combined = " ".join(str(value) for value in row.values()).lower()
    return "todo_locator" in combined or "todo_test_data" in combined


def take_failure_screenshot(driver, prefix: str) -> str:
    if not driver:
        return ""
    try:
        return save_screenshot(driver, SCREENSHOT_DIR, prefix)
    except Exception as exc:
        return f"screenshot_failed: {exc}"


def build_actual_result(metric: str, elapsed_seconds: float, planned_check: str) -> str:
    metric = (metric or "page_load_seconds").strip()
    elapsed_text = f"page_load_seconds={elapsed_seconds:.2f}"
    if "average_seconds" in metric:
        elapsed_text += f"; average_seconds={elapsed_seconds:.2f}"
    return f"{elapsed_text}; planned_check={planned_check}"


def run_non_functional_cases(
    data_filename: str,
    result_filename: str,
    screenshot_prefix: str,
    planned_check: str,
) -> None:
    data_path = os.path.join(DATA_DIR, data_filename)
    result_path = os.path.join(RESULT_DIR, result_filename)
    rows = read_csv(data_path)
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")
    driver = None

    try:
        driver = create_driver()
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

            try:
                target_url = build_target_url(row.get("page_url", ""))
                started_at = time.perf_counter()
                driver.get(target_url)
                elapsed_seconds = time.perf_counter() - started_at

                actual = build_actual_result(metric, elapsed_seconds, planned_check)
                seconds_limit = extract_seconds_limit(threshold)
                if seconds_limit is not None and elapsed_seconds > seconds_limit:
                    status = "FAIL"
                    error_message = (
                        f"Measured {elapsed_seconds:.2f}s, expected <= {seconds_limit:.2f}s."
                    )

                if has_placeholder_data(row):
                    status = "FAIL"
                    error_message = (
                        "TODO: Replace TODO_LOCATOR/TODO_TEST_DATA with real Moodle "
                        "locators and safe test data before final execution."
                    )

                if status == "FAIL":
                    screenshot_path = take_failure_screenshot(
                        driver, f"{screenshot_prefix}_{tc_id}"
                    )
            except Exception as exc:
                status = "ERROR"
                actual = "ERROR"
                error_message = str(exc)
                screenshot_path = take_failure_screenshot(
                    driver, f"{screenshot_prefix}_{tc_id}"
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
    finally:
        close_driver(driver)

    write_results(result_path, results, NFR_RESULT_COLUMNS)
