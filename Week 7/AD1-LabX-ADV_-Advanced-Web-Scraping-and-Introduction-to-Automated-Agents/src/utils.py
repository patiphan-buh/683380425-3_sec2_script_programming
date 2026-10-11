# agentic-web-scraper/src/utils.py
import json
import os
import time

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def save_data_to_json(data, filename, directory="data"):
    """Saves a list of dictionaries to a JSON file."""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data saved to {filepath}")
        return True
    except IOError as e:
        print(f"Error saving data to JSON file: {e}")
        return False


def guess_by(selector):
    """XPath if the selector looks like one ('/...' or '(/...'), otherwise CSS."""
    s = selector.strip()
    return By.XPATH if s.startswith(("/", "(")) else By.CSS_SELECTOR


def wait_for_element(driver, by, value, timeout=10):
    """
    Waits for an element to be present on the DOM and visible.
    Returns the element, or None on timeout.
    """
    try:
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
    except TimeoutException:
        print(f"Timeout waiting for element: {value}")
        return None
    except NoSuchElementException:
        print(f"Element not found after wait: {value}")
        return None


def robust_click(driver, by, value, max_attempts=3, delay_between_attempts=2):
    """
    Clicks an element, retrying on transient errors (overlays, stale elements, ...).
    Falls back to a JavaScript click if a normal click is intercepted.
    """
    for attempt in range(max_attempts):
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((by, value)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            try:
                element.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", element)
            return True
        except TimeoutException:
            print(f"Element not clickable: {value}")
            return False
        except WebDriverException as e:
            print(f"Click attempt {attempt + 1} failed: {e.__class__.__name__}")
            if attempt < max_attempts - 1:
                time.sleep(delay_between_attempts)
    print(f"Failed to click element {value} after {max_attempts} attempts.")
    return False


def scroll_to_bottom(driver):
    """Scrolls to the bottom of the page (useful for infinite-scroll pages)."""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # give some time for content to load
