import sys

if "twisted.internet.reactor" in sys.modules:
    del sys.modules["twisted.internet.reactor"]
import re
import logging
import scrapy
import subprocess
import pandas as pd


class HotelsSpider(scrapy.Spider):
    name = "hotels"

    def __init__(self, url=None, *args, **kwargs):
        """
        Inicjalizuje spidera, który generuje listę URL do scrapowania na podstawie podanego URL-a i różnych końcówek linków.

        Parametry:
        - url: str. (opcjonalnie) - Główny URL, do którego będą dodawane różne końcówki.
        """

        super(HotelsSpider, self).__init__(*args, **kwargs)
        if url:
            # Lista końcówek-aby zescrapować jak najwięcej hoteli to sortuję po różnych atrybutach
            suffixes = [
                "",  # Bez końcówki
                "&order=upsort_bh",
                "&order=price",
                "&order=price_from_high_to_low",
                "&order=review_score_and_price",
                "&order=class",
                "&order=class_asc",
                "&order=distance_from_search",
                "&order=bayesian_review_score",
                "&order=class_and_price",
            ]
            # Generowanie URL-i z końcówkami
            self.start_urls = [f"{url}{suffix}" for suffix in suffixes]
        else:
            raise ValueError("Brak URL! Podaj URL podczas uruchamiania scrapera.")
        self.seen_links = set()  # Zbiór przechowujący już widziane linki

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/96.0.4664.45 Safari/537.36',
        'FEEDS': {
            'bookingResults.csv': {
                'format': 'csv',
                'overwrite': True,
            },
        },
        'LOG_LEVEL': logging.WARNING,
    }

    def parse(self, response):
        """
        Funkcja, która przetwarza odpowiedź HTTP, ekstraktuje dane o hotelach i zapisuje je w formacie JSON.

        Parametry:
        - response: scrapy.http.Response - Odpowiedź HTTP otrzymana podczas scrapowania.
        """
        hotel_cards = response.xpath('//*[@data-testid="property-card"]')

        for card in hotel_cards:
            link = response.urljoin(card.xpath('.//h3[@class="aab71f8e4e"]//@href').get())
            if link in self.seen_links:
                continue  # Pomijanie duplikatów
            self.seen_links.add(link)

            raw_price = card.xpath('.//*[@data-testid="price-and-discounted-price"]//text()').get()
            clean_price = (
                int(raw_price.replace(' ', '').replace('zł', '').strip().encode('ascii', 'ignore').decode('ascii'))
                if raw_price else None
            )

            raw_distance = card.xpath('.//span[@data-testid="distance"]//text()').get()
            if raw_distance:
                distance_value, distance_unit = raw_distance.replace(',', '.').split(' ')[:2]
                distance_value = float(distance_value.strip())
                clean_distance = distance_value * 1000 if distance_unit.lower() == 'km' else distance_value
            else:
                clean_distance = None

            raw_rate_review = card.xpath('.//*[@data-testid="review-score"]//text()').get()
            clean_rate_review = (
                float(raw_rate_review.replace(',', '.').split(' ')[2].strip()) if raw_rate_review else None
            )

            raw_reviews = card.xpath(
                './/*[@data-testid="review-score"]//div[contains(@class,"abf093bdfe")]//text()').get()
            clean_reviews = int(re.sub(r'\D', '', raw_reviews)) if raw_reviews else None

            rating_stars = len(
                card.xpath('.//div[@data-testid="rating-stars"]//span[contains(@class, "fcd9eec8fb")]').extract()
            )
            if rating_stars == 0:
                rating_stars = len(
                    card.xpath('.//div[@data-testid="rating-circles"]//span[contains(@class, "fcd9eec8fb")]').extract()
                )
            if rating_stars == 0:
                rating_stars = len(
                    card.xpath('.//div[@data-testid="rating-squares"]//span[contains(@class, "fcd9eec8fb")]').extract()
                )

            yield {
                'name': card.xpath('.//*[@data-testid="title"]//text()').get(),
                'address': card.xpath('.//*[@data-testid="address"]//text()').get(),
                'price': clean_price,
                'distance': clean_distance,
                'rate_review': clean_rate_review,
                'num_review': clean_reviews,
                'rating_stars': rating_stars,
                'link': link,
                'source_url': response.url,  # Dodanie oryginalnego URL-a z końcówką
            }

    def close(self, reason):
        """
        Funkcja uruchamiana po zakończeniu działania Scrapera.
        Usuwa duplikaty z pliku CSV i uruchamia drugi Scraper.

        Parametry:
        - reason: str - Powód zakończenia działania Scrapera.
        """
        print("Scrapowanie głównych danych zakończone. Usuwanie duplikatów...")
        remove_duplicates_from_csv('bookingResults.csv')
        print("Duplikaty usunięte. Rozpoczynam scrapowanie detali...")
        try:
            subprocess.run(
                [
                    "scrapy",
                    "runspider",
                    "scraper_hotel_details.py",
                    "-a",
                    "csv_file=bookingResults.csv",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error during second Scrapy execution: {e}")


def remove_duplicates_from_csv(file_path):
    """
    Usuwa duplikaty z pliku CSV na podstawie kolumny 'link'.

    Parametry:
    - file_path: str - Ścieżka do pliku CSV, z którego mają zostać usunięte duplikaty.
    """
    try:
        df = pd.read_csv(file_path)
        df = df.drop_duplicates(subset=['link'])
        df.to_csv(file_path, index=False)
        print(f"Duplikaty zostały usunięte z pliku: {file_path}")
    except Exception as e:
        print(f"Błąd podczas usuwania duplikatów: {e}")


def run_spider(url):
    """
    Uruchamia Scrapy jako osobny proces za pomocą subprocess.

    Parametry:
    - url: str-URL, który ma zostać użyty do uruchomienia Scrapy.
    """
    command = [
        "scrapy",
        "runspider",
        "scraper_booking.py",
        "-a",
        f"url={url}"
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during Scrapy execution: {e}")
