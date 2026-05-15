# -*- coding: utf-8 -*-
# run command "pip install webdriver-manager" before run the code
# "python level1/f001_add_user_level1.py" to run the code
import csv
import sys
import os
import unittest
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

DATA_FILE_LEVEL1 = "data/level1/f001_level1_data.csv"
DATA_FILE_UCT    = "data/level1/f001_level1_uct_data.csv"
BASE_URL   = "https://sandbox51.moodledemo.net/"
ADMIN_USER = "admin"
ADMIN_PASS = "sandbox24"

BRAVE_CANDIDATES = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
]

# ── Shared helpers ──────────────────────────────────────────────────────────

def make_driver():
    options = Options()
    for path in BRAVE_CANDIDATES:
        if os.path.exists(path):
            options.binary_location = path
            break
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(30)
    return driver

def enable_password_policy(driver):
    driver.get("https://sandbox51.moodledemo.net/admin/settings.php?section=sitepolicies")
    checkbox = driver.find_element(By.ID, "id_s__passwordpolicy")
    checked = driver.execute_script("return arguments[0].checked;", checkbox)
    if not checked:
        label = driver.find_element(By.CSS_SELECTOR, "label[for='id_s__passwordpolicy']")
        driver.execute_script("arguments[0].scrollIntoView(true);", label)
        time.sleep(0.5)
        label.click()
        save_btns = driver.find_elements(By.XPATH, "//button[@type='submit' and contains(@class,'btn-primary')]")
        save_btn = save_btns[-1]
        driver.execute_script("arguments[0].scrollIntoView(true);", save_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", save_btn)
        time.sleep(2)

def login(driver):
    driver.get(BASE_URL + "login/index.php")
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(ADMIN_USER)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASS)
    driver.find_element(By.ID, "loginbtn").click()

# ── Level 1 ─────────────────────────────────────────────────────────────────

def run_test_case_level1(driver, row):
    driver.get(BASE_URL)
    driver.find_element(By.LINK_TEXT, "Site administration").click()
    driver.find_element(By.LINK_TEXT, "Users").click()
    driver.find_element(By.LINK_TEXT, "Add a new user").click()

    driver.find_element(By.ID, "id_username").clear()
    if row["username"]:
        driver.find_element(By.ID, "id_username").send_keys(row["username"])

    driver.find_element(By.CSS_SELECTOR, "a[data-passwordunmask=\"edit\"]").click()
    driver.find_element(By.ID, "id_newpassword").clear()
    if row["password"]:
        driver.find_element(By.ID, "id_newpassword").send_keys(row["password"])

    driver.find_element(By.ID, "id_firstname").clear()
    if row["firstname"]:
        driver.find_element(By.ID, "id_firstname").send_keys(row["firstname"])

    driver.find_element(By.ID, "id_lastname").clear()
    if row["lastname"]:
        driver.find_element(By.ID, "id_lastname").send_keys(row["lastname"])

    driver.find_element(By.ID, "id_email").clear()
    if row["email"]:
        driver.find_element(By.ID, "id_email").send_keys(row["email"])

    btn = driver.find_element(By.ID, "id_submitbutton")
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)

    body_text = driver.find_element(By.CSS_SELECTOR, "BODY").text
    expected = row["expected_result"]
    assert expected in body_text, f"[{row['tc_id']}] Expected '{expected}' not found in page"
    print(f"[PASS] {row['tc_id']}")

# ── UCT ─────────────────────────────────────────────────────────────────────

FIELD_ID = {
    "username":  "id_username",
    "password":  "id_newpassword",
    "firstname": "id_firstname",
    "lastname":  "id_lastname",
    "email":     "id_email",
}

def fill_form(driver, username, password, firstname, lastname, email):
    driver.find_element(By.ID, "id_username").clear()
    if username:
        driver.find_element(By.ID, "id_username").send_keys(username)

    driver.find_element(By.CSS_SELECTOR, "a[data-passwordunmask=\"edit\"]").click()
    driver.find_element(By.ID, "id_newpassword").clear()
    if password:
        driver.find_element(By.ID, "id_newpassword").send_keys(password)

    driver.find_element(By.ID, "id_firstname").clear()
    if firstname:
        driver.find_element(By.ID, "id_firstname").send_keys(firstname)

    driver.find_element(By.ID, "id_lastname").clear()
    if lastname:
        driver.find_element(By.ID, "id_lastname").send_keys(lastname)

    driver.find_element(By.ID, "id_email").clear()
    if email:
        driver.find_element(By.ID, "id_email").send_keys(email)

def submit(driver):
    btn = driver.find_element(By.ID, "id_submitbutton")
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)

def run_test_case_uct(driver, row):
    driver.get(BASE_URL)
    driver.find_element(By.LINK_TEXT, "Site administration").click()
    driver.find_element(By.LINK_TEXT, "Users").click()
    driver.find_element(By.LINK_TEXT, "Add a new user").click()

    fill_form(driver, row["username"], row["password"], row["firstname"], row["lastname"], row["email"])
    submit(driver)

    # Verify lỗi lần 1
    body_text = driver.find_element(By.CSS_SELECTOR, "BODY").text
    assert row["error_expected"] in body_text, \
        f"[{row['tc_id']}] Submit 1: Expected error '{row['error_expected']}' not found"

    # Fix field bị lỗi
    if row["empty_field"] == "password":
        driver.find_element(By.CSS_SELECTOR, "a[data-passwordunmask='edit']").click()
        time.sleep(0.3)
    field_id = FIELD_ID[row["empty_field"]]
    fix_field = driver.find_element(By.ID, field_id)
    fix_field.clear()
    fix_field.send_keys(row["fix_value"])

    submit(driver)

    # Verify thành công lần 2
    body_text = driver.find_element(By.CSS_SELECTOR, "BODY").text
    assert row["success_expected"] in body_text, \
        f"[{row['tc_id']}] Submit 2: Expected '{row['success_expected']}' not found"
    print(f"[PASS] {row['tc_id']}")

# ── Test suite ───────────────────────────────────────────────────────────────

class TC001Combined(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Bật password policy 1 lần duy nhất cho cả 2 phần
        driver = make_driver()
        login(driver)
        enable_password_policy(driver)
        driver.quit()

    def test_1_level1(self):
        with open(DATA_FILE_LEVEL1, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            with self.subTest(tc_id=row["tc_id"]):
                driver = make_driver()
                try:
                    login(driver)
                    run_test_case_level1(driver, row)
                finally:
                    driver.quit()

    def test_2_uct(self):
        with open(DATA_FILE_UCT, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            with self.subTest(tc_id=row["tc_id"]):
                driver = make_driver()
                try:
                    login(driver)
                    run_test_case_uct(driver, row)
                finally:
                    driver.quit()

if __name__ == "__main__":
    unittest.main(verbosity=2, argv=[sys.argv[0]])
