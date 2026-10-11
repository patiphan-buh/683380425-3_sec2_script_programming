# agentic-web-scraper/test_setup.py
"""
Quick check that your environment is ready for the Advanced lab.
Run:  python test_setup.py
"""
import sys


def check(label, func):
    try:
        detail = func()
        print(f"[OK]   {label}" + (f" -> {detail}" if detail else ""))
        return True
    except Exception as e:
        print(f"[FAIL] {label} -> {e}")
        return False


def check_python():
    if sys.version_info < (3, 8):
        raise RuntimeError("Python 3.8+ is required")
    return sys.version.split()[0]


def check_selenium():
    import selenium
    return selenium.__version__


def check_webdriver_manager():
    import webdriver_manager  # noqa: F401
    return "installed"


def check_bs4():
    import bs4
    return bs4.__version__


def check_browser():
    from src.driver_manager import DriverManager

    manager = DriverManager(browser_name="chrome", headless=True)
    driver = manager.get_driver()
    if not driver:
        raise RuntimeError("could not start Chrome (see messages above)")
    try:
        driver.get("https://books.toscrape.com/")
        return f"page title = {driver.title!r}"
    finally:
        manager.quit_driver()


if __name__ == "__main__":
    results = [
        check("Python version", check_python),
        check("selenium", check_selenium),
        check("webdriver-manager", check_webdriver_manager),
        check("beautifulsoup4", check_bs4),
        check("Chrome + WebDriver (opens books.toscrape.com)", check_browser),
    ]
    print()
    if all(results):
        print("Setup OK - you can run: python main.py")
    else:
        print("Some checks failed. Run: pip install -r requirements.txt  (and make sure Chrome is installed)")
        sys.exit(1)
