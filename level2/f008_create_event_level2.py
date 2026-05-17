import os
import time
import uuid
from datetime import datetime

from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from level2.generic_runner import run_data_driven_steps

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "level2", "f008_level2_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level2", "f008_level2_results.csv")

FEATURE_ID = "F008"
LEVEL = "level2"
LEVEL2_RESULT_COLUMNS = [
    "run_id",
    "run_date",
    "feature_id",
    "tc_id",
    "step_id",
    "level",
    "expected_result",
    "actual_result",
    "status",
    "screenshot_path",
    "error_message",
]
MAX_TC_ATTEMPTS = 2


def _is_driver_timeout(results: list[dict]) -> bool:
    for result in results:
        message = result.get("error_message", "")
        if "HTTPConnectionPool" in message and "Read timed out" in message:
            return True
    return False


def _run_single_tc(tc_rows: list[dict]) -> list[dict]:
    last_results = []

    for attempt in range(1, MAX_TC_ATTEMPTS + 1):
        driver = create_driver()
        try:
            last_results = run_data_driven_steps(driver, tc_rows)
        finally:
            close_driver(driver)

        if not _is_driver_timeout(last_results):
            return last_results

        if attempt < MAX_TC_ATTEMPTS:
            time.sleep(2)

    return last_results


def run():
    rows = read_csv(DATA_PATH)
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")
    step_results = []

    for tc_id in dict.fromkeys(row.get("tc_id", "").strip() for row in rows):
        tc_rows = [row for row in rows if row.get("tc_id", "").strip() == tc_id]
        step_results.extend(_run_single_tc(tc_rows))

    for result in step_results:
        result["run_id"] = run_id
        result["run_date"] = run_date
        result["feature_id"] = FEATURE_ID
        result["level"] = LEVEL

    if os.path.exists(RESULT_PATH):
        os.remove(RESULT_PATH)
    write_results(RESULT_PATH, step_results, LEVEL2_RESULT_COLUMNS)


if __name__ == "__main__":
    run()
