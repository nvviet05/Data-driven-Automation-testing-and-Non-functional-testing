import os
import uuid
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from common.screenshot import save_screenshot

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "level1", "f004_level1_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "level1", "f004_level1_results.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "level1")

FEATURE_ID = "F004"
LEVEL = "level1"

def select_moodle_date(driver, prefix, day, month, year):
    """Helper to select Day, Month, and Year for Moodle fields"""
    if day:
        Select(driver.find_element(By.ID, f"id_{prefix}_day")).select_by_visible_text(str(day))
    if month:
        Select(driver.find_element(By.ID, f"id_{prefix}_month")).select_by_visible_text(month)
    if year:
        Select(driver.find_element(By.ID, f"id_{prefix}_year")).select_by_visible_text(str(year))

def set_checkbox(driver, element_id, wanted_state):
    """Helper to ensure a checkbox is checked or unchecked using JS to avoid intercept errors"""
    checkbox = driver.find_element(By.ID, element_id)
    is_selected = checkbox.is_selected()
    if (wanted_state == "yes" and not is_selected) or \
       (wanted_state == "no" and is_selected):
        driver.execute_script("arguments[0].click();", checkbox)

def run():
    rows = read_csv(DATA_PATH)
    driver = create_driver()
    results = []
    run_id = str(uuid.uuid4())
    run_date = datetime.now().isoformat(timespec="seconds")

    # LOGIN 
    driver.get("https://gr13vou5.moodlecloud.com/login/index.php")
    driver.find_element(By.ID, "username").send_keys("vocaonhatminh@gmail.com")
    driver.find_element(By.ID, "password").send_keys("ncYENCO1305.")
    
    login_btn = driver.find_element(By.ID, "loginbtn")
    driver.execute_script("arguments[0].click();", login_btn)
    time.sleep(2)

    for row in rows:
        tc_id = (row.get("tc_id") or "").strip()
        if not tc_id:
            continue

        expected = (row.get("expected_result") or "").strip()
        actual = ""
        status = "PASS"
        screenshot_path = ""
        error_message = ""

        try:
            # Navigate to Add Assignment page
            driver.get("https://gr13vou5.moodlecloud.com/course/modedit.php?add=assign&type&course=9&sectionid=34")

            # Assignment Name
            name_val = (row.get("name") or "").strip()
            driver.find_element(By.ID, "id_name").clear()
            driver.find_element(By.ID, "id_name").send_keys(name_val)

            # Handle Dates
            allow_enabled = (row.get("allow_enabled") or "").strip()
            set_checkbox(driver, "id_allowsubmissionsfromdate_enabled", allow_enabled)
            if allow_enabled == "yes":
                select_moodle_date(driver, "allowsubmissionsfromdate", row.get("allow_day"), row.get("allow_month"), row.get("allow_year"))

            due_enabled = (row.get("due_enabled") or "").strip()
            set_checkbox(driver, "id_duedate_enabled", due_enabled)
            if due_enabled == "yes":
                select_moodle_date(driver, "duedate", row.get("due_day"), row.get("due_month"), row.get("due_year"))

            cutoff_enabled = (row.get("cutoff_enabled") or "").strip()
            set_checkbox(driver, "id_cutoffdate_enabled", cutoff_enabled)
            if cutoff_enabled == "yes":
                select_moodle_date(driver, "cutoffdate", row.get("cutoff_day"), row.get("cutoff_month"), row.get("cutoff_year"))

            # Handle Word Limit
            if (row.get("word_limit_enabled") or "").strip() == "yes":
                set_checkbox(driver, "id_assignsubmission_onlinetext_enabled", "yes")
                set_checkbox(driver, "id_assignsubmission_onlinetext_wordlimit_enabled", "yes")
                limit_field = driver.find_element(By.ID, "id_assignsubmission_onlinetext_wordlimit")
                limit_field.clear()
                limit_field.send_keys(row.get("word_limit_val"))

            # Submit
            submit_btn = driver.find_element(By.ID, "id_submitbutton2")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(1) # Small wait for validation to appear or page to redirect

            # Verification Logic
            if expected == "SUCCESS":
                if "modedit.php" in driver.current_url:
                    try:
                        actual = driver.find_element(By.CLASS_NAME, "invalid-feedback").text
                    except:
                        actual = "Stayed on edit page (Validation failed)"
                    status = "FAIL"
                else:
                    actual = "SUCCESS"
            else:
                if expected in driver.page_source:
                    actual = expected
                else:
                    try:
                        actual = driver.find_element(By.CLASS_NAME, "invalid-feedback").text
                    except:
                        actual = "Error message not found"
                    status = "FAIL"

            if status == "FAIL":
                screenshot_path = save_screenshot(driver, SCREENSHOT_DIR, f"{FEATURE_ID}_{tc_id}")

        except Exception as exc:
            status = "ERROR"
            error_message = str(exc)
            actual = "ERROR"
            screenshot_path = save_screenshot(driver, SCREENSHOT_DIR, f"{FEATURE_ID}_{tc_id}")

        results.append({
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
        })

    close_driver(driver)
    write_results(RESULT_PATH, results)

if __name__ == "__main__":
    run()