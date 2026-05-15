# -*- coding: utf-8 -*-
# run command "pip install webdriver-manager" before run the code
# "python level1/f007_change_password_level1.py" to run the code

import csv
import os
import unittest
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

DATA_FILE = "data/level1/f007_level1_data.csv"
BASE_URL   = "https://sandbox51.moodledemo.net/"

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

def login(driver, username, password):
    driver.get(BASE_URL + "login/index.php")
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "loginbtn").click()

# ── Run test case ────────────────────────────────────────────────────────────

def run_test_case(driver, row):
    driver.get(BASE_URL)
    driver.find_element(By.XPATH, "//a[@id='user-menu-toggle']/span/span/span/span").click()
    driver.find_element(By.LINK_TEXT, "Preferences").click()
    driver.find_element(By.LINK_TEXT, "Change password").click()

    driver.find_element(By.ID, "id_password").click()
    driver.find_element(By.ID, "id_password").clear()
    if row["current_password"]:
        driver.find_element(By.ID, "id_password").send_keys(row["current_password"])

    driver.find_element(By.ID, "id_newpassword1").click()
    driver.find_element(By.ID, "id_newpassword1").clear()
    if row["new_password"]:
        driver.find_element(By.ID, "id_newpassword1").send_keys(row["new_password"])

    driver.find_element(By.ID, "id_newpassword2").click()
    driver.find_element(By.ID, "id_newpassword2").clear()
    if row["new_password_again"]:
        driver.find_element(By.ID, "id_newpassword2").send_keys(row["new_password_again"])

    driver.find_element(By.ID, "id_submitbutton").click()
    time.sleep(1)

    body_text = driver.find_element(By.CSS_SELECTOR, "BODY").text
    expected = row["expected_result"]
    assert expected in body_text, \
        f"[{row['tc_id']}] Expected '{expected}' not found in page"
    
    print(f"[PASS] {row['tc_id']}")

# ── Test suite ───────────────────────────────────────────────────────────────

class TC007Combined(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Bật password policy 1 lần duy nhất — dùng admin account
        driver = make_driver()
        login(driver, "admin", "sandbox24")
        enable_password_policy(driver)
        driver.quit()

    def test_all(self):
        with open(DATA_FILE, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            with self.subTest(tc_id=row["tc_id"]):
                driver = make_driver()
                try:
                    login(driver, row["login_username"], row["login_password"])
                    run_test_case(driver, row)
                finally:
                    driver.quit()

if __name__ == "__main__":
    unittest.main(verbosity=2, argv=[__import__("sys").argv[0]])
