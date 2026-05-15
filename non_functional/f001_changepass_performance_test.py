# -*- coding: utf-8 -*-
# run command "pip install webdriver-manager" before run the code
# "python non_functional/f001_changepass_performance_test.py" to run the code

import os
import unittest
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

BASE_URL   = "https://sandbox51.moodledemo.net/"
LOGIN_USER = "admin"
LOGIN_PASS = "sandbox24"
THRESHOLD  = 5.0  # seconds
RUNS       = 10

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
    driver.find_element(By.ID, "username").send_keys(LOGIN_USER)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(LOGIN_PASS)
    driver.find_element(By.ID, "loginbtn").click()

def measure_change_password_load(driver):
    driver.get(BASE_URL)
    driver.find_element(By.XPATH, "//a[@id='user-menu-toggle']/span/span/span/span").click()
    driver.find_element(By.LINK_TEXT, "Preferences").click()

    start = time.time()
    driver.find_element(By.LINK_TEXT, "Change password").click()
    # Chờ đến khi form hiện ra
    driver.find_element(By.ID, "id_password")
    elapsed = time.time() - start

    return elapsed

class PerformanceTest(unittest.TestCase):

    def test_change_password_page_load(self):
        times = []

        for i in range(RUNS):
            driver = make_driver()
            try:
                login(driver)
                elapsed = measure_change_password_load(driver)
                times.append(elapsed)
                print(f"  Run {i+1:2d}: {elapsed:.3f}s")
            finally:
                driver.quit()

        avg  = sum(times) / len(times)
        mn   = min(times)
        mx   = max(times)

        print(f"\n--- Results ({RUNS} runs) ---")
        print(f"  Min:     {mn:.3f}s")
        print(f"  Max:     {mx:.3f}s")
        print(f"  Average: {avg:.3f}s")
        print(f"  Threshold: {THRESHOLD}s")

        assert avg < THRESHOLD, \
            f"Average load time {avg:.3f}s exceeds threshold {THRESHOLD}s"

        print(f"[PASS] Average load time {avg:.3f}s is within threshold {THRESHOLD}s")

if __name__ == "__main__":
    unittest.main(verbosity=2, argv=[__import__("sys").argv[0]])
