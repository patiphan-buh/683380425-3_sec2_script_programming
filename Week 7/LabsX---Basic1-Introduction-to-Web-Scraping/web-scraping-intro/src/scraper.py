# web-scraping-intro/src/scraper.py
import re

import requests
from bs4 import BeautifulSoup


class SimpleWebScraper:
    """
    A class to encapsulate basic web scraping functionality.
    Target: "Automate the Boring Stuff with Python" (3rd Edition) main page.
    """

    # Pattern of the items we want from the Table of Contents
    TOC_PATTERN = re.compile(r"^(Introduction|Chapter\s+\d+|Appendix\s+[A-Z])\b")

    def __init__(self, target_url):
        self.target_url = target_url

    def _get_html_content(self):
        """
        Downloads the HTML content from the target URL.
        Handles basic error checking.
        """
        print(f"กำลังดาวน์โหลดเนื้อหาจาก: {self.target_url}")
        try:
            # Some sites block the default requests User-Agent
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(self.target_url, headers=headers, timeout=10)
            response.raise_for_status()  # raise HTTPError for 4xx / 5xx
            response.encoding = "utf-8"
            print("ดาวน์โหลดเนื้อหาสำเร็จ")
            return response.text
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e} - Status Code: {e.response.status_code}")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error occurred: {e} - Could not connect to {self.target_url}")
        except requests.exceptions.Timeout:
            print("The request timed out.")
        except requests.exceptions.RequestException as e:
            print(f"An unexpected request error occurred: {e}")
        return None

    def _find_book_title(self, soup):
        """Book title = the <h1> in <article><header> (falls back to the first <h1>)."""
        h1_tag = None
        article_tag = soup.find("article")
        if article_tag:
            header_tag = article_tag.find("header")
            if header_tag:
                h1_tag = header_tag.find("h1")
        if h1_tag is None:
            h1_tag = soup.find("h1")
        return h1_tag.get_text(strip=True) if h1_tag else "Book Title Not Found"

    def _find_chapter_titles(self, soup):
        """
        Chapter titles come from the 'Table of Contents' list.
        1) Prefer the <ul>/<ol> right after the 'Table of Contents' heading.
        2) Fallback: any <a> whose text looks like Introduction / Chapter N / Appendix X.
        """
        titles = []

        toc_heading = soup.find(
            lambda tag: tag.name in ("h1", "h2", "h3")
            and "table of contents" in tag.get_text(strip=True).lower()
        )
        if toc_heading:
            toc_list = toc_heading.find_next(["ul", "ol"])
            if toc_list:
                for link in toc_list.select("li a"):
                    text = link.get_text(strip=True)
                    if text:
                        titles.append(text)

        if not titles:
            for link in soup.find_all("a"):
                text = link.get_text(strip=True)
                if self.TOC_PATTERN.match(text) and text not in titles:
                    titles.append(text)

        return titles

    def scrape_main_titles(self):
        """Scrapes the book title and the chapter titles from the main page."""
        html_content = self._get_html_content()
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")

        return {
            "book_title": self._find_book_title(soup),
            "chapter_titles": self._find_chapter_titles(soup),
        }
