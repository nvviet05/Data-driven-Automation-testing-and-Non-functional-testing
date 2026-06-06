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
DATA_PATH = os.path.join(ROOT_DIR, "data", "level2", "f006_level2_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level2", "f006_level2_results.csv")

FEATURE_ID = "F006"
LEVEL = "level2"
COURSE_ID = "9"

def run():
    rows = read_csv(DATA_PATH)
    driver = create_driver()
    all_results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")

    try:
        # LOGIN
        driver.get("https://gr13vou5.moodlecloud.com/login/index.php")
        driver.find_element(By.ID, "username").send_keys("vocaonhatminh@gmail.com")
        driver.find_element(By.ID, "password").send_keys("ncYENCO1305.")
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "loginbtn"))
        
        time.sleep(4)
        sesskey = driver.execute_script("return M.cfg.sesskey;")
        driver.execute_script("var b=document.getElementById('onetrust-banner-sdk'); if(b) b.remove();")

        test_cases = {}
        for row in rows:
            tc = row['tc_id']
            if tc not in test_cases: test_cases[tc] = []
            test_cases[tc].append(row)

        for tc_id, steps in test_cases.items():
            creation_steps = [s for s in steps if s['step_id'] != 'S7']
            creation_results = run_moodle_robust_steps(driver, creation_steps)
            all_results.extend(creation_results)

            time.sleep(2)
            assign_url = driver.current_url

            switch_url = f"https://gr13vou5.moodlecloud.com/course/switchrole.php?id={COURSE_ID}&sesskey={sesskey}&switchrole=5&returnurl={assign_url}"
            driver.get(switch_url)
            time.sleep(2)

            verification_steps = [s for s in steps if s['step_id'] == 'S7']
            verification_results = run_moodle_robust_steps(driver, verification_steps)
            all_results.extend(verification_results)

            driver.get(f"https://gr13vou5.moodlecloud.com/course/switchrole.php?id={COURSE_ID}&sesskey={sesskey}&switchrole=0")

    finally:
        close_driver(driver)

    for res in all_results:
        res.update({"run_id": run_id, "run_date": run_date, "feature_id": FEATURE_ID, "level": LEVEL})

    write_results(RESULT_PATH, all_results)

if __name__ == "__main__":
    run()