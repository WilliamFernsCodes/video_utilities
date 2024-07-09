from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import random
import time
import os

# Short function to find element, using webdriver wait
def find_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def find_elements(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((by, value))
    )

# Simple function to scroll to bottom of screen.
def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

def set_element_innertext(driver, element, text):
    driver.execute_script("arguments[0].innerText = arguments[1];", element, text)

def new_driver(chrome_profile_path: str):
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")  # Disable notifications
    options.add_argument("--disable-popup-blocking")  # Disable popup blocking
    prefs = {"download.default_directory": "/tmp"}
    options.add_experimental_option("prefs", prefs)

    profile_path = chrome_profile_path.replace("/", "\\")
    options.add_argument(f"user-data-dir={profile_path}")

    driver = uc.Chrome(options=options)
    return driver

def gen_random_string(length=8):
    random_string = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for i in range(length))
    return random_string

def simulate_typing(text, element):
    for character in text:
        element.send_keys(character)
        time.sleep(random.uniform(0.05, 0.1))

def get_path_size_mb(path : str) -> float:
    """Get size in megabytes for a specific path"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    total_size_mb = total_size / (1024 * 1024)
    return round(total_size_mb, 2)
