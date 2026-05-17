import os
import uuid
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from common.screenshot import save_screenshot

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "level1", "f006_level1_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level1", "f006_level1_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "level1")

FEATURE_ID = "F006"
LEVEL = "level1"
COURSE_ID = "9" 

def select_moodle_date(driver, prefix, day, month, year):
    """Helper to select Day, Month, and Year for Moodle fields"""
    if day:
        el = driver.find_element(By.ID, f"id_{prefix}_day")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        Select(el).select_by_visible_text(str(day))
    if month:
        Select(driver.find_element(By.ID, f"id_{prefix}_month")).select_by_visible_text(month)
    if year:
        Select(driver.find_element(By.ID, f"id_{prefix}_year")).select_by_visible_text(str(year))

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

        for row in rows:
            tc_id = (row.get("tc_id") or "").strip()
            if not tc_id: continue

            expected = (row.get("expected_result") or "").strip()
            name = row.get("name")
            status, actual, error_message, screenshot_path = "PASS", "", "", ""

            try:
                # CREATE ASSIGNMENT
                driver.get(f"https://gr13vou5.moodlecloud.com/course/modedit.php?add=assign&type&course={COURSE_ID}&sectionid=34")

                driver.execute_script("""
                    var b = document.getElementById('onetrust-banner-sdk'); if(b) b.remove();
                    var f = document.querySelector('.onetrust-pc-dark-filter'); if(f) f.remove();
                """)

                driver.find_element(By.ID, "id_name").clear()
                driver.find_element(By.ID, "id_name").send_keys(name)

                due_chk = driver.find_element(By.ID, "id_duedate_enabled")
                if due_chk.is_selected(): driver.execute_script("arguments[0].click();", due_chk)
                
                grading_chk = driver.find_element(By.ID, "id_gradingduedate_enabled")
                if grading_chk.is_selected(): driver.execute_script("arguments[0].click();", grading_chk)

                select_moodle_date(driver, "allowsubmissionsfromdate", row.get("allow_day"), row.get("allow_month"), row.get("allow_year"))

                save_display_btn = driver.find_element(By.ID, "id_submitbutton")
                driver.execute_script("arguments[0].click();", save_display_btn)
                
                WebDriverWait(driver, 10).until(EC.url_contains("mod/assign/view.php"))
                assign_url = driver.current_url # Now captures the correct mod/assign URL

                # SWITCH TO STUDENT ROLE
                switch_url = f"https://gr13vou5.moodlecloud.com/course/switchrole.php?id={COURSE_ID}&sesskey={sesskey}&switchrole=5&returnurl={assign_url}"
                driver.get(switch_url)
                time.sleep(2)

                # NAVIGATE TO ASSIGNMENT AS STUDENT
                driver.get(assign_url)
                
                # VERIFY BUTTON VISIBILITY
                btn_xpath = "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add submission')]"
                
                try:
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, btn_xpath)))
                    has_button = True
                except:
                    has_button = False

                if expected == "BUTTON_HIDDEN":
                    if has_button:
                        actual, status = "FAIL: Button was visible", "FAIL"
                    else:
                        actual = "BUTTON_HIDDEN"
                else: # BUTTON_VISIBLE
                    if has_button:
                        actual = "BUTTON_VISIBLE"
                    else:
                        actual, status = "FAIL: Button was NOT found", "FAIL"

                if status == "FAIL":
                    screenshot_path = save_screenshot(driver, SCREENSHOT_DIR, f"{FEATURE_ID}_{tc_id}")

                # SWITCH BACK TO TEACHER
                driver.get(f"https://gr13vou5.moodlecloud.com/course/switchrole.php?id={COURSE_ID}&sesskey={sesskey}&switchrole=0")

            except Exception as exc:
                status, actual, error_message = "ERROR", "ERROR", str(exc)
                screenshot_path = save_screenshot(driver, SCREENSHOT_DIR, f"ERR_{tc_id}")
                driver.get(f"https://gr13vou5.moodlecloud.com/course/switchrole.php?id={COURSE_ID}&sesskey={sesskey}&switchrole=0")

            results.append({
                "run_id": run_id, "run_date": run_date, "feature_id": FEATURE_ID,
                "tc_id": tc_id, "level": LEVEL, "expected_result": expected,
                "actual_result": actual, "status": status, "screenshot_path": screenshot_path,
                "error_message": error_message
            })

    finally:
        close_driver(driver)

    write_results(RESULT_PATH, results)

if __name__ == "__main__":
    run()