# -*- coding: utf-8 -*-
# run command "pip install webdriver-manager" before run the code
# "python non_functional/f001_f007_security_test.py" to run the code

import csv
import os
import unittest
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

DATA_FILE = "data/non_functional/f001_f007_security_data.csv"
BASE_URL   = "https://sandbox51.moodledemo.net/"
ADMIN_USER = "admin"
ADMIN_PASS = "sandbox24"

BRAVE_CANDIDATES = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
]

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

def login(driver):
    driver.get(BASE_URL + "login/index.php")
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(ADMIN_USER)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASS)
    driver.find_element(By.ID, "loginbtn").click()

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

def run_security_test(driver, row):
    driver.get(BASE_URL)
    driver.find_element(By.LINK_TEXT, "Site administration").click()
    driver.find_element(By.LINK_TEXT, "Users").click()
    driver.find_element(By.LINK_TEXT, "Add a new user").click()

    driver.find_element(By.ID, "id_username").clear()
    driver.find_element(By.ID, "id_username").send_keys(row["username"])

    driver.find_element(By.CSS_SELECTOR, "a[data-passwordunmask='edit']").click()
    driver.find_element(By.ID, "id_newpassword").clear()
    driver.find_element(By.ID, "id_newpassword").send_keys(row["password"])

    driver.find_element(By.ID, "id_firstname").clear()
    driver.find_element(By.ID, "id_firstname").send_keys(row["firstname"])

    driver.find_element(By.ID, "id_lastname").clear()
    driver.find_element(By.ID, "id_lastname").send_keys(row["lastname"])

    driver.find_element(By.ID, "id_email").clear()
    driver.find_element(By.ID, "id_email").send_keys(row["email"])

    btn = driver.find_element(By.ID, "id_submitbutton")
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)

    body_text = driver.find_element(By.CSS_SELECTOR, "BODY").text
    assert row["expected_result"] in body_text, \
        f"[{row['tc_id']}] Password policy NOT enforced for password='{row['password']}'"

    print(f"[PASS] {row['tc_id']} — policy enforced for password='{row['password']}'")

class SecurityTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        driver = make_driver()
        login(driver)
        enable_password_policy(driver)
        driver.quit()

    def test_password_policy_enforcement(self):
        with open(DATA_FILE, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            with self.subTest(tc_id=row["tc_id"]):
                driver = make_driver()
                try:
                    login(driver)
                    run_security_test(driver, row)
                finally:
                    driver.quit()

if __name__ == "__main__":
    unittest.main(verbosity=2, argv=[__import__("sys").argv[0]])