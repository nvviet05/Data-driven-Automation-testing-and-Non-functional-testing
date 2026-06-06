import os
import uuid
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from common.screenshot import save_screenshot

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "non_functional", "f006_assignment_performance_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "non_functional", "f006_assignment_performance_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "non_functional")

FEATURE_ID = "F006"
TEST_TYPE = "Performance"
COURSE_ID = "9"

def run():
    rows = read_csv(DATA_PATH)
    driver = create_driver()
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")

    try:
        # LOGIN
        driver.get("https://gr13vou5.moodlecloud.com/login/index.php")
        driver.find_element(By.ID, "username").send_keys("vocaonhatminh@gmail.com")
        driver.find_element(By.ID, "password").send_keys("ncYENCO1305.")
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "loginbtn"))
        
        time.sleep(3)
        sesskey = driver.execute_script("return M.cfg.sesskey;")

        driver.execute_script("var b=document.getElementById('onetrust-banner-sdk'); if(b) b.remove();")

        for row in rows:
            tc_id = row.get("tc_id")
            assign_name = f"{row.get('assignment_name')}_{uuid.uuid4().hex[:4]}"
            threshold = float(row.get("threshold_seconds", 5.0))
            status, actual_result, error_message, screenshot_path, duration = "PASS", "", "", "", 0.0

            try:
                # CREATE ASSIGNMENT 
                driver.get(f"https://gr13vou5.moodlecloud.com/course/modedit.php?add=assign&type&course={COURSE_ID}&sectionid=34")
                driver.find_element(By.ID, "id_name").send_keys(assign_name)
                
                for box in ["id_duedate_enabled", "id_gradingduedate_enabled"]:
                    chk = driver.find_element(By.ID, box)
                    if chk.is_selected(): driver.execute_script("arguments[0].click();", chk)
                
                onlinetxt = driver.find_element(By.ID, "id_assignsubmission_onlinetext_enabled")
                if not onlinetxt.is_selected(): driver.execute_script("arguments[0].click();", onlinetxt)
                file_sub = driver.find_element(By.ID, "id_assignsubmission_file_enabled")
                if file_sub.is_selected(): driver.execute_script("arguments[0].click();", file_sub)

                driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "id_submitbutton"))
                WebDriverWait(driver, 10).until(EC.url_contains("mod/assign/view.php"))
                assign_url = driver.current_url

                # SWITCH TO STUDENT ROLE
                driver.get(f"https://gr13vou5.moodlecloud.com/course/switchrole.php?id={COURSE_ID}&sesskey={sesskey}&switchrole=5&returnurl={assign_url}")
                
                # PREPARE SUBMISSION
                driver.get(assign_url)
                add_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add submission')]")))
                driver.execute_script("arguments[0].click();", add_btn)

                WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "id_onlinetext_editor_ifr")))

                editor_body = driver.find_element(By.ID, "tinymce")
                editor_body.send_keys("Performance Test Submission")

                driver.switch_to.default_content()

                save_btn = driver.find_element(By.ID, "id_submitbutton")

                start_time = time.time()
                driver.execute_script("arguments[0].click();", save_btn)
                
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "submissionstatustable")))
                end_time = time.time()

                duration = round(end_time - start_time, 2)
                actual_result = f"Latency: {duration}s"
                if duration > threshold: status = "FAIL"

                # SWITCH BACK TO TEACHER 
                driver.get(f"https://gr13vou5.moodlecloud.com/course/switchrole.php?id={COURSE_ID}&sesskey={sesskey}&switchrole=0")

            except Exception as exc:
                status, actual_result, error_message = "ERROR", "ERROR", str(exc)
                screenshot_path = save_screenshot(driver, SCREENSHOT_DIR, f"PERF_ERR_{tc_id}")
                driver.get(f"https://gr13vou5.moodlecloud.com/course/switchrole.php?id={COURSE_ID}&sesskey={sesskey}&switchrole=0")

            results.append({
                "run_id": run_id, "run_date": run_date, "feature_id": FEATURE_ID,
                "test_type": TEST_TYPE, "tc_id": tc_id,
                "expected_result": f"Latency <= {threshold}s",
                "actual_result": actual_result, "status": status,
                "metrics": f"{duration}s", "screenshot_path": screenshot_path,
                "error_message": error_message
            })

    finally:
        close_driver(driver)

    write_results(RESULT_PATH, results)
    print(f"Performance Test Complete. Latency: {duration}s")

if __name__ == "__main__":
    run()