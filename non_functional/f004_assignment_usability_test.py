import os
import uuid
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from common.browser import close_driver, create_driver
from common.csv_reader import read_csv
from common.result_writer import write_results
from common.screenshot import save_screenshot

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT_DIR, "data", "non_functional", "f004_assignment_usability_data.csv")
RESULT_PATH = os.path.join(ROOT_DIR, "results", "non_functional", "f004_assignment_usability_data.csv")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots", "non_functional")

FEATURE_ID = "F004"
TEST_TYPE = "Usability"

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

        for row in rows:
            tc_id = row.get("tc_id")
            url = row.get("page_url")
            threshold = float(row.get("min_expected_score", 75))
            
            status = "PASS"
            screenshot_path = ""
            error_message = ""
            
            try:
                driver.get(url)
                time.sleep(3)

                scan_results = driver.execute_script("""
                    var inputs = document.querySelectorAll("input:not([type='hidden']), select, textarea");
                    var missing = [];
                    inputs.forEach(el => {
                        if (el.id) {
                            if (!document.querySelector("label[for='" + el.id + "']")) {
                                missing.push(el.id);
                            }
                        }
                    });
                    return { total: inputs.length, missing: missing };
                """)

                total, missing_ids = scan_results['total'], scan_results['missing']
                fail_count = len(missing_ids)
                score = round(((total - fail_count) / total) * 100, 2) if total > 0 else 100
                
                if score < threshold:
                    status = "FAIL"
                
                actual_result = f"Compliance: {score}% ({fail_count} missing labels)"
                
                if status == "FAIL":
                    error_message = f"First 3 missing: {', '.join(missing_ids[:3])}"
                    screenshot_path = save_screenshot(driver, SCREENSHOT_DIR, f"USABILITY_FAIL_{tc_id}")

            except Exception as exc:
                status = "ERROR"
                error_message = str(exc)
                screenshot_path = save_screenshot(driver, SCREENSHOT_DIR, f"USABILITY_ERROR_{tc_id}")

            results.append({
                "run_id": run_id, "run_date": run_date, "feature_id": FEATURE_ID,
                "test_type": TEST_TYPE, "tc_id": tc_id,
                "expected_result": f"Compliance >= {threshold}%",
                "actual_result": actual_result,
                "status": status, "metrics": f"{score}%",
                "screenshot_path": screenshot_path, "error_message": error_message
            })
            print(f"Scan complete. Score: {score}%. Status: {status}")

    finally:
        close_driver(driver)

    write_results(RESULT_PATH, results)

if __name__ == "__main__":
    run()