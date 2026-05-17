import os
import uuid
import time
from datetime import datetime
from selenium.webdriver.common.by import By

from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from level2.generic_runner import run_moodle_robust_steps 

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "level2", "f004_level2_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level2", "f004_level2_results.csv")

FEATURE_ID = "F004"
LEVEL = "level2"

def run():
    rows = read_csv(DATA_PATH)
    driver = create_driver()
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")

    try:
        # LOGIN
        driver.get("https://gr13vou5.moodlecloud.com/login/index.php")
        driver.find_element(By.ID, "username").send_keys("vocaonhatminh@gmail.com")
        driver.find_element(By.ID, "password").send_keys("ncYENCO1305.")
        
        login_btn = driver.find_element(By.ID, "loginbtn")
        driver.execute_script("arguments[0].click();", login_btn)
        
        time.sleep(5)
        driver.execute_script("""
            var banner = document.getElementById('onetrust-banner-sdk');
            if(banner) banner.remove();
            var filter = document.querySelector('.onetrust-pc-dark-filter');
            if(filter) filter.remove();
            var modal = document.querySelector('.modal-backdrop');
            if(modal) modal.remove();
        """)

        # RUN THE STEPS
        step_results = run_moodle_robust_steps(driver, rows)

    finally:
        close_driver(driver)

    for result in step_results:
        result.update({"run_id": run_id, "run_date": run_date, "feature_id": FEATURE_ID, "level": LEVEL})

    write_results(RESULT_PATH, step_results)

if __name__ == "__main__":
    run()