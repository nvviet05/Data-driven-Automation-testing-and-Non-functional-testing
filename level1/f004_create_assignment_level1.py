import os
import uuid
from datetime import datetime

from common.assertions import text_equals
from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from common.screenshot import save_screenshot
from config.settings import BASE_URL

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "level1", "f004_level1_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level1", "f004_level1_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "level1")

FEATURE_ID = "F004"
LEVEL = "level1"


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
                # TODO: Add Selenium steps for F004 Create Assignment
                driver.get(BASE_URL)

                actual = "TODO"
                if not text_equals(expected, actual):
                    status = "FAIL"
                    screenshot_path = save_screenshot(
                        driver, SCREENSHOT_DIR, f"{FEATURE_ID}_{tc_id}"
                    )
            except Exception as exc:
                status = "ERROR"
                error_message = str(exc)
                actual = "ERROR"
                screenshot_path = save_screenshot(
                    driver, SCREENSHOT_DIR, f"{FEATURE_ID}_{tc_id}"
                )

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


if __name__ == "__main__":
    run()
