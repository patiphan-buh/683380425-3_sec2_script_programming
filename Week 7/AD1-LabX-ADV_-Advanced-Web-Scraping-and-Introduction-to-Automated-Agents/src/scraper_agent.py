# agentic-web-scraper/src/scraper_agent.py
import logging
import os
import time

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .data_models import Product
from .driver_manager import DriverManager
from .utils import guess_by, robust_click, save_data_to_json, wait_for_element

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


class ScraperAgent:
    """
    An agentic web scraper that operates based on a provided configuration.
    It reads the plan (config), navigates, extracts data, and follows pagination.
    """

    def __init__(self, config, browser="chrome", headless=True, output_file="scraped_products.json"):
        self.config = config
        self.driver_manager = DriverManager(browser_name=browser, headless=headless)
        self.driver = None
        self.scraped_products = []
        self.output_file = output_file
        self.max_pages = config.get("max_pages", 5)  # default: at most 5 pages
        logging.info(f"Scraper Agent initialized with config for {config['start_url']}")

    # ---- element helpers -------------------------------------------------
    def _get_element_text(self, parent_element, selector, prefer_title=False):
        """Safely get text from a child element. Returns None if no selector / not found."""
        if not selector:
            return None
        try:
            element = parent_element.find_element(guess_by(selector), selector)
            text = element.text.strip()
            # Some sites truncate visible text with "..." but keep the full text in `title`
            if prefer_title and (not text or text.endswith("...")):
                text = (element.get_attribute("title") or text).strip()
            return text or None
        except (NoSuchElementException, StaleElementReferenceException):
            return None

    def _get_element_attribute(self, parent_element, selector, attribute):
        """Safely get an attribute from a child element. Returns None if not available."""
        if not selector:
            return None
        try:
            element = parent_element.find_element(guess_by(selector), selector)
            value = element.get_attribute(attribute)
            return value.strip() if value else None
        except (NoSuchElementException, StaleElementReferenceException):
            return None

    def _parse_product_data(self, item_element):
        """Extracts product data from one product block, using the config selectors."""
        selectors = self.config["item_data_selectors"]

        name = self._get_element_text(item_element, selectors.get("name"), prefer_title=True)
        price = self._get_element_text(item_element, selectors.get("price"))
        description = self._get_element_text(item_element, selectors.get("description"))
        url = self._get_element_attribute(item_element, selectors.get("url"), "href")
        image_url = self._get_element_attribute(item_element, selectors.get("image_url"), "src")

        if name and price:  # basic validation for a valid product
            return Product(name=name, price=price, description=description, url=url, image_url=image_url)
        return None

    # ---- scraping --------------------------------------------------------
    def scrape_page(self):
        """Scrapes product items from the current page."""
        logging.info(f"Scraping page: {self.driver.current_url}")
        selector = self.config["item_container_selector"]
        try:
            item_elements = self.driver.find_elements(guess_by(selector), selector)
            logging.info(f"Found {len(item_elements)} potential product items on this page.")

            for item_element in item_elements:
                product = self._parse_product_data(item_element)
                if product:
                    self.scraped_products.append(product.to_dict())
                else:
                    logging.warning("Could not parse product data from an item element.")
        except Exception as e:
            logging.error(f"An error occurred while scraping items: {e}")

    def _go_to_next_page(self):
        """
        Clicks the 'next page' control. Returns True if the browser moved to a new page.
        Returns False when there is no (clickable) next link => last page reached.
        """
        selector = self.config["pagination_selector"]
        by = guess_by(selector)

        next_button = wait_for_element(self.driver, by, selector, timeout=5)
        if not (next_button and next_button.is_displayed() and next_button.is_enabled()):
            logging.info("No more next page button found or not clickable. Ending pagination.")
            return False

        logging.info(f"Clicking next page: {next_button.text or 'No text'}")

        # Remember an element of the old page so we can detect when the new page has loaded
        old_marker = None
        try:
            container = self.config["item_container_selector"]
            found = self.driver.find_elements(guess_by(container), container)
            old_marker = found[0] if found else None
        except Exception:
            pass

        if not robust_click(self.driver, by, selector):
            return False

        if old_marker is not None:
            try:
                WebDriverWait(self.driver, 10).until(EC.staleness_of(old_marker))
            except TimeoutException:
                logging.warning("Page did not change after clicking next. Ending pagination.")
                return False
        return True

    def run(self):
        """Executes the scraping process."""
        self.driver = self.driver_manager.get_driver()
        if not self.driver:
            logging.error("Failed to get WebDriver. Exiting.")
            return

        try:
            self.driver.get(self.config["start_url"])
            current_page = 1

            while True:
                logging.info(f"Processing page {current_page} at {self.driver.current_url}")
                container = self.config["item_container_selector"]
                wait_for_element(self.driver, guess_by(container), container, timeout=10)
                self.scrape_page()

                if not self.config["pagination_selector"]:
                    logging.info("No pagination selector configured. Scraped a single page.")
                    break
                if current_page >= self.max_pages:
                    logging.info(f"Reached max_pages ({self.max_pages}). Stopping.")
                    break

                time.sleep(self.config.get("delay_between_pages", 2))  # respectful delay

                try:
                    if not self._go_to_next_page():
                        break
                except Exception as e:
                    logging.error(f"Error during pagination: {e}. Ending pagination.")
                    break
                current_page += 1

        except Exception as e:
            logging.critical(f"An unhandled error occurred during scraping: {e}")
        finally:
            self.driver_manager.quit_driver()
            logging.info(f"Scraping finished. Total products scraped: {len(self.scraped_products)}")
            save_data_to_json(self.scraped_products, self.output_file, directory=DATA_DIR)
