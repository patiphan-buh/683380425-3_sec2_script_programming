# web-scraping-intro/main.py
from src.scraper import SimpleWebScraper


def main():
    """
    Main entry point for the simple web scraping application.
    """
    target_url = "https://automatetheboringstuff.com/3e/"
    scraper = SimpleWebScraper(target_url)

    scraped_data = scraper.scrape_main_titles()

    if scraped_data:
        print("\n--- ข้อมูลที่ Scrape ได้ ---")
        print(f"ชื่อหนังสือ: {scraped_data['book_title']}")
        print("\nชื่อบทต่างๆ:")
        if scraped_data["chapter_titles"]:
            for i, title in enumerate(scraped_data["chapter_titles"], start=1):
                print(f"{i}. {title}")
        else:
            print("ไม่พบชื่อบท")
        print("--------------------")
    else:
        print("Scrape ข้อมูลไม่สำเร็จ")


if __name__ == "__main__":
    main()
