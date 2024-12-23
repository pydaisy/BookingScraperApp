import scrapy
import logging
import pandas as pd
import re


class HotelDetailsSpider(scrapy.Spider):
    name = "hotelDetails"

    def __init__(self, csv_file=None, *args, **kwargs):
        """
        Inicjalizuje Spidera i wczytuje plik CSV z linkami do hoteli.

        :param csv_file: Ścieżka do pliku CSV zawierającego linki do hoteli
        """
        super(HotelDetailsSpider, self).__init__(*args, **kwargs)
        if csv_file:
            self.hotels_df = pd.read_csv(csv_file)  # Wczytujemy dane z pliku
            self.start_urls = self.hotels_df['link'].tolist()  # Pobieramy linki
        else:
            raise ValueError("Brak pliku CSV z linkami!")

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/96.0.4664.45 Safari/537.36',
        'LOG_LEVEL': logging.WARNING,
    }

    def parse(self, response):
        """
        Parsuje stronę hotelu i zapisuje dane takie jak typ hotelu, współrzędne geograficzne,
        oraz aktualizuje dane w pliku CSV.

        :param response: Odpowiedź z serwera zawierająca stronę hotelu
        """

        if not response.xpath('//*[@id="wrap-hotelpage-top"]'):
            self.logger.warning(f"No hotel data found for: {response.url}")

        hotelCards = response.xpath('//*[@id="wrap-hotelpage-top"]')

        # Pobierz aktualny URL
        current_link = response.url

        # Loguj przetwarzany link
        self.logger.info(f"Processing link: {current_link}")

        if not hotelCards:
            self.logger.warning(f"No hotel data found for link: {current_link}")
            return

        for card in hotelCards:
            # Pobierz rodzaj hotelu/hostelu/apartamentu etc.
            hotel_type = response.xpath('//a[@class="bui_breadcrumb__link_masked" and @itemprop="item"]/text()').get()
            hotel_type = re.search(r'\(([^,]+)\)', hotel_type).group(1) if hotel_type and re.search(r'\(([^,]+)\)',
                                                                                                    hotel_type) else None
            # Pobierz współrzędne geograficzne
            lat_lon = card.xpath('.//a[@id="map_trigger_header_pin"]/@data-atlas-latlng').get()
            latitude, longitude = None, None
            if lat_lon:
                lat_lon_split = lat_lon.split(",")
                if len(lat_lon_split) == 2:
                    latitude, longitude = lat_lon_split

            # Aktualizacja dataframe na podstawie linku
            if current_link in self.hotels_df['link'].values:
                self.hotels_df.loc[self.hotels_df['link'] == current_link, 'latitude'] = latitude
                self.hotels_df.loc[self.hotels_df['link'] == current_link, 'longitude'] = longitude
                self.hotels_df.loc[self.hotels_df['link'] == current_link, 'hotel_type'] = hotel_type
            else:
                self.logger.warning(f"Link {current_link} not found in original CSV.")

        # Zapisuj zaktualizowany plik po każdej iteracji
        self.hotels_df.to_csv('bookingResults_updated.csv', index=False)

    def close(self, reason):
        """
        Wywoływane po zakończeniu scrapowania. Zajmuje się usuwaniem duplikatów z pliku CSV.

        :param reason: Powód zakończenia scrapowania
        """
        print("Scrapowanie zakończone. Usuwanie duplikatów...")
        remove_duplicates_from_csv('bookingResults_updated.csv')
        print("Duplikaty usunięte.")


def remove_duplicates_from_csv(file_path):
    """
    Usuwa duplikaty z pliku CSV na podstawie kolumn 'latitude' i 'longitude'.

    :param file_path: Ścieżka do pliku CSV, z którego mają zostać usunięte duplikaty
    """
    try:
        df = pd.read_csv(file_path)
        if 'latitude' in df.columns and 'longitude' in df.columns:
            df = df.drop_duplicates(subset=['latitude', 'longitude'])
        else:
            print("Kolumny 'latitude' i 'longitude' nie istnieją w pliku CSV.")
        df.to_csv(file_path, index=False)
        print(f"Duplikaty zostały usunięte z pliku: {file_path}")
    except Exception as e:
        print(f"Błąd podczas usuwania duplikatów: {e}")
