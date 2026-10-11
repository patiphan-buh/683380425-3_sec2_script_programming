# agentic-web-scraper/src/driver_manager.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
FIREFOX_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"


class DriverManager:
    """
    Manages the setup and teardown of Selenium WebDriver instances.
    Tries `webdriver-manager` first; if it is unavailable (or fails), falls back to
    Selenium Manager (built into selenium >= 4.6), which also downloads drivers automatically.
    """

    def __init__(self, browser_name="chrome", headless=True):
        self.browser_name = browser_name.lower()
        self.headless = headless
        self.driver = None

    # ---- service helpers -------------------------------------------------
    def _chrome_service(self):
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            return ChromeService(ChromeDriverManager().install())
        except Exception as e:  # webdriver-manager missing / offline
            print(f"[info] webdriver-manager not used ({e}); falling back to Selenium Manager.")
            return None

    def _firefox_service(self):
        try:
            from webdriver_manager.firefox import GeckoDriverManager
            return FirefoxService(GeckoDriverManager().install())
        except Exception as e:
            print(f"[info] webdriver-manager not used ({e}); falling back to Selenium Manager.")
            return None

    # ---- public API ------------------------------------------------------
    def get_driver(self):
        """Initializes and returns a WebDriver instance (or None on failure)."""
        if self.driver:
            return self.driver

        if self.browser_name == "chrome":
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")             # needed in some environments (Docker)
            options.add_argument("--disable-dev-shm-usage")  # needed in some environments
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--log-level=3")            # suppress console logs
            options.add_argument(f"user-agent={CHROME_UA}")
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            try:
                service = self._chrome_service()
                if service:
                    self.driver = webdriver.Chrome(service=service, options=options)
                else:
                    self.driver = webdriver.Chrome(options=options)
            except Exception as e:
                print(f"Error setting up Chrome driver: {e}")
                print("Make sure Google Chrome is installed, then run: pip install -r requirements.txt")
                return None

        elif self.browser_name == "firefox":
            options = webdriver.FirefoxOptions()
            if self.headless:
                options.add_argument("--headless")
            options.set_preference("general.useragent.override", FIREFOX_UA)
            try:
                service = self._firefox_service()
                if service:
                    self.driver = webdriver.Firefox(service=service, options=options)
                else:
                    self.driver = webdriver.Firefox(options=options)
            except Exception as e:
                print(f"Error setting up Firefox driver: {e}")
                print("Make sure Firefox is installed, then run: pip install -r requirements.txt")
                return None
        else:
            raise ValueError(f"Unsupported browser: {self.browser_name}. Choose 'chrome' or 'firefox'.")

        # We rely on EXPLICIT waits (WebDriverWait) in utils.py. Mixing a long implicit wait with
        # explicit waits makes missing elements (e.g. the last page's "next" button) very slow.
        self.driver.implicitly_wait(0)
        self.driver.set_page_load_timeout(30)
        return self.driver

    def quit_driver(self):
        """Quits the WebDriver instance if it's running."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("WebDriver quit successfully.")
