# -*- coding: utf-8 -*-
# run command "pip install webdriver-manager" before run the code
# "python level2/f001_add_user_level2.py" to run the code

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
CONFIG_FILE      = "data/level2/f001_level2_data.csv"
ADMIN_USER = "admin"
ADMIN_PASS = "sandbox24"

BRAVE_CANDIDATES = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
]

# ── Load config ──────────────────────────────────────────────────────────────

def load_config(config_file):
    config = {}
    with open(config_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            config[row["field_name"]] = {
                "locator_type":  row["locator_type"],
                "locator_value": row["locator_value"],
            }
    return config

def find_element(driver, config, field_name):
    loc_type  = config[field_name]["locator_type"].lower()
    loc_value = config[field_name]["locator_value"]
    by_map = {
        "id":         By.ID,
        "css":        By.CSS_SELECTOR,
        "link_text":  By.LINK_TEXT,
        "xpath":      By.XPATH,
        "name":       By.NAME,
    }
    return driver.find_element(by_map[loc_type], loc_value)

# ── Shared helpers ───────────────────────────────────────────────────────────

def make_driver():
    options = Options()
    for path in BRAVE_CANDIDATES:
        if os.path.exists(path):
            options.binary_location = path
            break
    options.add_argument("--start-maximized")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-extensions")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(30)
    return driver

def enable_password_policy(driver, config):
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

def login(driver, config):
    driver.get(config["site_url"]["locator_value"] + "login/index.php")
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(ADMIN_USER)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASS)
    driver.find_element(By.ID, "loginbtn").click()

# ── Level 1 ──────────────────────────────────────────────────────────────────

def run_test_case_level1(driver, config, row):
    driver.get(config["site_url"]["locator_value"])
    find_element(driver, config, "nav_admin").click()
    find_element(driver, config, "nav_users").click()
    find_element(driver, config, "nav_add_user").click()

    find_element(driver, config, "username").clear()
    if row["username"]:
        find_element(driver, config, "username").send_keys(row["username"])

    find_element(driver, config, "password_unmask").click()
    find_element(driver, config, "password").clear()
    if row["password"]:
        find_element(driver, config, "password").send_keys(row["password"])

    find_element(driver, config, "firstname").clear()
    if row["firstname"]:
        find_element(driver, config, "firstname").send_keys(row["firstname"])

    find_element(driver, config, "lastname").clear()
    if row["lastname"]:
        find_element(driver, config, "lastname").send_keys(row["lastname"])

    find_element(driver, config, "email").clear()
    if row["email"]:
        find_element(driver, config, "email").send_keys(row["email"])

    btn = find_element(driver, config, "submit")
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)

    body_text = driver.find_element(By.CSS_SELECTOR, "BODY").text
    expected = row["expected_result"]
    assert expected in body_text, f"[{row['tc_id']}] Expected '{expected}' not found in page"
    print(f"[PASS] {row['tc_id']}")

# ── UCT ──────────────────────────────────────────────────────────────────────

FIELD_CONFIG_KEY = {
    "username":  "username",
    "password":  "password",
    "firstname": "firstname",
    "lastname":  "lastname",
    "email":     "email",
}

def fill_form(driver, config, username, password, firstname, lastname, email):
    find_element(driver, config, "username").clear()
    if username:
        find_element(driver, config, "username").send_keys(username)

    find_element(driver, config, "password_unmask").click()
    find_element(driver, config, "password").clear()
    if password:
        find_element(driver, config, "password").send_keys(password)

    find_element(driver, config, "firstname").clear()
    if firstname:
        find_element(driver, config, "firstname").send_keys(firstname)

    find_element(driver, config, "lastname").clear()
    if lastname:
        find_element(driver, config, "lastname").send_keys(lastname)

    find_element(driver, config, "email").clear()
    if email:
        find_element(driver, config, "email").send_keys(email)

def submit(driver, config):
    btn = find_element(driver, config, "submit")
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)

def run_test_case_uct(driver, config, row):
    driver.get(config["site_url"]["locator_value"])
    find_element(driver, config, "nav_admin").click()
    find_element(driver, config, "nav_users").click()
    find_element(driver, config, "nav_add_user").click()

    fill_form(driver, config, row["username"], row["password"], row["firstname"], row["lastname"], row["email"])
    submit(driver, config)

    body_text = driver.find_element(By.CSS_SELECTOR, "BODY").text
    assert row["error_expected"] in body_text, \
        f"[{row['tc_id']}] Submit 1: Expected error '{row['error_expected']}' not found"

    if row["empty_field"] == "password":
        find_element(driver, config, "password_unmask").click()
        time.sleep(0.3)
    config_key = FIELD_CONFIG_KEY[row["empty_field"]]
    fix_field = find_element(driver, config, config_key)
    fix_field.clear()
    fix_field.send_keys(row["fix_value"])

    submit(driver, config)

    body_text = driver.find_element(By.CSS_SELECTOR, "BODY").text
    assert row["success_expected"] in body_text, \
        f"[{row['tc_id']}] Submit 2: Expected '{row['success_expected']}' not found"
    print(f"[PASS] {row['tc_id']}")

# ── Test suite ────────────────────────────────────────────────────────────────

class TC001Level2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = load_config(CONFIG_FILE)
        driver = make_driver()
        login(driver, cls.config)
        enable_password_policy(driver, cls.config)
        driver.quit()

    def test_1_level1(self):
        with open(DATA_FILE_LEVEL1, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            with self.subTest(tc_id=row["tc_id"]):
                driver = make_driver()
                try:
                    login(driver, self.config)
                    run_test_case_level1(driver, self.config, row)
                finally:
                    driver.quit()

    def test_2_uct(self):
        with open(DATA_FILE_UCT, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            with self.subTest(tc_id=row["tc_id"]):
                driver = make_driver()
                try:
                    login(driver, self.config)
                    run_test_case_uct(driver, self.config, row)
                finally:
                    driver.quit()

if __name__ == "__main__":
    unittest.main(verbosity=2, argv=[sys.argv[0]])
