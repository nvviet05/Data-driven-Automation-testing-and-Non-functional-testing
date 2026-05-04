import os
import uuid
from datetime import datetime

from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from level2.generic_runner import run_data_driven_steps

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "level2", "f002_level2_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level2", "f002_level2_results.csv")

FEATURE_ID = "F002"
LEVEL = "level2"


def run():
    # TODO: Update data/level2/f002_level2_data.csv with real Moodle locators.
    rows = read_csv(DATA_PATH)
    driver = create_driver()
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")

    try:
        step_results = run_data_driven_steps(driver, rows)
    finally:
        close_driver(driver)

    for result in step_results:
        result["run_id"] = run_id
        result["run_date"] = run_date
        result["feature_id"] = FEATURE_ID
        result["level"] = LEVEL

    write_results(RESULT_PATH, step_results)


if __name__ == "__main__":
    run()
