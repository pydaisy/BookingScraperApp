from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import folium
from scraper_booking import run_spider
from theme_settings import apply_theme, generate_color_palette
import datetime
import numpy as np


def create_map(scraped_data, top_5_hotels=None, filter_top_5=False):
    """
    Tworzy mapę z oznaczeniem hoteli, na podstawie danych zebranych przez scraper.

    Parametry:
    - scraped_data: pd.DataFrame - DataFrame zawierający dane o hotelach, w tym współrzędne geograficzne.
    - top_5_hotels: pd.DataFrame - DataFrame zawierający dane o top 5 hotelach do wyróżnienia.
    - filter_top_5: bool - Czy wyświetlać tylko top 5 hoteli.

    Zwraca:
    - folium.Map - Obiekt mapy z oznaczeniami hoteli.
    """
    scraped_data['latitude'] = pd.to_numeric(scraped_data['latitude'], errors='coerce')
    scraped_data['longitude'] = pd.to_numeric(scraped_data['longitude'], errors='coerce')
    scraped_data = scraped_data.dropna(subset=['latitude', 'longitude'])

    # Jeśli filtrujemy tylko top 5, ogranicz dane do top_5_hotels
    if filter_top_5 and top_5_hotels is not None:
        scraped_data = top_5_hotels

    center_lat = scraped_data['latitude'].mean()
    center_lon = scraped_data['longitude'].mean()

    # Tworzenie mapy
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='cartodbpositron')
    marker_cluster = MarkerCluster(zoom_to_bounds_on_click=True).add_to(m)

    for _, row in scraped_data.iterrows():
        popup_html = folium.Popup(
            f""" <style> @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,100..700;1,
            100..700&display=swap');
            
            div {{
            font-family: 'Roboto Mono', sans-serif !important;
            font-weight: 700 !important;
            text-align: left !important;
        }}
            </style>
            
            <div>
                <strong>{row['name']}</strong><br>
                <b>price:</b> {row['price']} PLN<br>
                <b>rating:</b> {row.get('rating_stars', 'N/A')}<br>
                <b>number of reviews:</b> {row.get('num_review', 'N/A')}<br>
                <b>address:</b> {row['address']}<br>
            </div>
            """,
            max_width=400
        )

        price = row.get('price', None)
        icon_color = '#597700' if price and price < 200 else '#F2C824' if price and price < 500 else '#CC322F'
        is_top_5 = top_5_hotels is not None and row['name'] in top_5_hotels['name'].values
        icon_color = '#FFD700' if is_top_5 else icon_color  # Złoty kolor dla top 5

        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=popup_html,
            tooltip=f"{row['name']} ({row['price']} PLN)",
            icon=folium.Icon(color=icon_color, icon="star" if is_top_5 else "info-sign")
        ).add_to(marker_cluster)

    return m


def load_scraped_data(file_path: str) -> pd.DataFrame:
    """
    Ładuje dane z pliku CSV zawierającego informacje o hotelach pochodzące ze scrapingu.

    Parametry:
    - file_path: str-Ścieżka do pliku CSV z danymi.

    Zwraca:
    - pd. DataFrame-DataFrame zawierający dane o hotelach.
    """
    try:
        scraped_data = pd.read_csv(file_path)
        scraped_data = scraped_data.dropna(subset=['latitude', 'longitude', 'hotel_type', 'num_review'])
        st.success("...csv file loaded successfully!")
        return scraped_data
    except FileNotFoundError:
        st.error("oops! resulting file not found.")
    except pd.errors.EmptyDataError:
        st.error("oops! the CSV file is empty.")
    except Exception as e:
        st.error(f"oops! an error occurred while loading the file: {e}")
    return pd.DataFrame()


def home_content(dark_mode):
    """
    Funkcja wyświetlająca główną stronę aplikacji z formularzem wyszukiwania hoteli.

    Na podstawie danych wprowadzonych przez użytkownika, generuje link do wyszukiwania na Booking.com
    i uruchamia proces scrapowania danych o hotelach.
    """

    st.header("search hotels")
    with st.form("booking_form", clear_on_submit=False):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

        with col1:
            city = st.text_input("where are we headed?", placeholder="destination")
        with col2:
            checkin = st.date_input("check-in", value=date.today(), min_value=date.today())
        with col3:
            checkout = st.date_input("check-out", value=date.today() + datetime.timedelta(days=1),
                                     min_value=date.today() + datetime.timedelta(days=1))
        num_days = (checkout - checkin).days # Liczba nocy
        with col4:
            adults_count = st.number_input("adults", min_value=1, value=2, step=1, help="number of adults")

            submit_button = st.form_submit_button("find my stay")

        if submit_button:
            if not city.strip():
                st.error(" no vibes, no travel. type in a destination!")
            elif checkin >= checkout:
                st.error(" whoa there, Doc Brown. let’s fix those dates!")
            else:
                link = (
                    f"https://www.booking.com/searchresults.pl.html"
                    f"?ss={city}"
                    f"&checkin={checkin}&checkout={checkout}"
                    f"&group_adults={adults_count}"
                )
                st.success("...link generated!")
                st.markdown(
                    f"scraping may take a moment...[while scraping you can explore booking.com by yourself.]({link})",
                    unsafe_allow_html=True)

                # Spinner podczas scrapowania danych
                with st.spinner("scraping hotel data..."):
                    try:
                        run_spider(link)
                        st.success("...scraping completed!")
                        data_file = "bookingResults_updated.csv"

                        # Spinner podczas ładowania danych
                        with st.spinner("loading scraped data..."):
                            scraped_data = load_scraped_data(data_file)
                            scraped_data['price_range'] = pd.cut(scraped_data['price']/num_days, bins=[0, 150, 300, 500, np.inf],
                                                                 labels=['cheap', 'moderate', 'expensive', 'luxury'])
                            st.session_state["scraped_data"] = scraped_data
                    except Exception as e:
                        st.error(f"oops! an error occurred during scraping: {e}")

    # Tab layout
    tabs = st.tabs(["hotels info", "understand the trends"])

    with tabs[0]:
        # Map section
        if "scraped_data" in st.session_state and not st.session_state["scraped_data"].empty:
            scraped_data = st.session_state["scraped_data"]
            st.header(f"your __{city}__ experience awaits: __{checkin}-{checkout}__ for __{adults_count}__ guests")
            st.divider()
            st.subheader("quick hotel insights")
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("no. of found spots", len(scraped_data))
            col2.metric("avg. price", f"{scraped_data['price'].mean():.2f} pln")
            col2.write(
                f"_highest price:_ ___{scraped_data['price'].max():.2f} pln___")
            col2.write(
                f"_lowest price:_ ___{scraped_data['price'].min():.2f} pln___")
            col3.metric("avg rate review:",
                        f"{scraped_data['rate_review'].mean():.2f}")
            col3.write(
                f"_highest rate review:_ ___{scraped_data['rate_review'].max():.2f}___")
            col3.write(
                f"_lowest rate review:_ ___{scraped_data['rate_review'].min():.2f}___")
            col4.metric("avg distance to city center",
                        f"{scraped_data['distance'].mean():.2f} m")
            col4.write(
                f"_highest distance:_ ___{scraped_data['distance'].max():.2f} m___")
            col4.write(
                f"_lowest distance:_ ___{scraped_data['distance'].min():.2f} m___")
            st.divider()
            if 'latitude' in scraped_data.columns and 'longitude' in scraped_data.columns:
                col_map, col_data = st.columns([1, 1])

                with col_map:
                    # Wybór kategorii
                    st.subheader("show me top 5")

                    options = ['distance', 'rate_review', 'rating_stars', 'num_review', 'price']
                    top_5_referring = st.selectbox("referring to...", options, index=0, help="""   Choose a criterion to filter the top 5 hotels based on:

    - **distance**: hotels closest to the city center.
    - **rate_review**: hotels with the highest rating based on reviews.
    - **rating_stars**: hotels with the highest number of stars (highest star rating).
    - **num_review**: hotels with the most reviews.
    - **price**: the cheapest hotels (lowest price).""")

                    # Filtracja top 5 hoteli
                    if top_5_referring in scraped_data.columns:
                        if top_5_referring == 'price':
                            # dla ceny wybieramy najtańsze hotele
                            top_5_hotels = scraped_data.nsmallest(5, top_5_referring)
                        elif top_5_referring == 'rating_stars':
                            # dla ocen gwiazdkowych wybieramy najwyższe hotele
                            top_5_hotels = scraped_data.nlargest(5, top_5_referring)
                        else:
                            # dla innych kryteriów (np. liczba recenzji, ocena) wybieramy najmniejsze lub największe
                            # wartości w zależności od kontekstu
                            top_5_hotels = scraped_data.nsmallest(5, top_5_referring)

                    show_only_top_5 = st.checkbox("show only top 5 hotels on the map", value=False)
                    st.divider()

                    with st.spinner("creating map..."):
                        m = create_map(scraped_data, top_5_hotels, filter_top_5=show_only_top_5)
                        st_folium(m, width=1200, height=1200)

                    with col_data:
                        with st.container():
                            st.write(f"#### top 5 hotels sorted by {top_5_referring}:")
                            for index, row in top_5_hotels.iterrows():
                                st.markdown(f"**{row['name']}** " + f"[click here to visit the hotel]({row['link']})") # Link do strony hotelu na booking
                                col1, col2 = st.columns(2)  # Dwie kolumny dla metryk

                                with col1:
                                    st.metric(label="price", value=f"{row['price']} pln")
                                    st.metric(label="rating", value=f"{row['rating_stars']}/5 ☆")

                                with col2:
                                    st.metric(label="review rate", value=f"{row['rate_review']} / 10")
                                    st.metric(label="distance to city center", value=f"{row['distance']} m")


                    # st.subheader("3D Hotel Trends")
                    # if not scraped_data.empty:
                    #     fig = px.scatter_3d(
                    #         scraped_data,
                    #         x='price',
                    #         y='rating_stars',
                    #         z='distance',
                    #         color='price_range',
                    #         size='num_review',
                    #         hover_name='name',
                    #         title="Hotel Analysis in 3D"
                    #     )
                    #     st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("missing required geographic data in results.")
        else:
            st.info("fill in the form to see the results.")

    with tabs[1]:
        # Dashboard content
        if "scraped_data" in st.session_state and not st.session_state["scraped_data"].empty:
            scraped_data = st.session_state["scraped_data"]

            col1, col2 = st.columns([3, 2.5])

            with col1:

                st.subheader("customizable scatter plot")
                options = ['distance', 'rate_review', 'rating_stars', 'num_review', 'price']
                x_axis = st.selectbox("select X-axis", options, index=0)
                y_axis = st.selectbox("select Y-axis", options, index=4)

                with st.spinner("generating your scatter plot..."):
                    if x_axis in scraped_data.columns and y_axis in scraped_data.columns:
                        fig = px.scatter(
                            scraped_data,
                            x=x_axis,
                            y=y_axis,
                            color=y_axis,
                            size=x_axis,
                            color_continuous_scale=generate_color_palette(dark_mode)['palette'],
                            labels={x_axis: x_axis, y_axis: y_axis},
                            title=f"relation between {x_axis} and {y_axis}"
                        )
                        fig.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='black')))
                        fig.update_layout(
                            modebar=dict(bgcolor='rgba(0,0,0,0)'),
                            font=dict(family="Roboto Mono"),
                            title=dict(
                                font=dict(family="Roboto Mono", color=generate_color_palette(dark_mode)['title'])
                            ),
                            xaxis=dict(
                                title=dict(
                                    font=dict(family="Roboto Mono", size=14,
                                              color=generate_color_palette(dark_mode)['text'])
                                ),
                                tickfont=dict(color=generate_color_palette(dark_mode)['text'])
                            ),
                            yaxis=dict(
                                title=dict(
                                    font=dict(family="Roboto Mono", size=14,
                                              color=generate_color_palette(dark_mode)['text'])
                                ),
                                tickfont=dict(color=generate_color_palette(dark_mode)['text'])
                            ),
                            height=630
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error(f"the data does not contain the selected columns '{x_axis}' or '{y_axis}'.")

            with col2:
                if x_axis in scraped_data.columns:
                    hist_fig_x = px.histogram(
                        scraped_data,
                        x=x_axis,
                        title=f"{x_axis} distribution",
                        labels={x_axis: x_axis},
                        nbins=20,
                        color_discrete_sequence=[generate_color_palette(dark_mode)['middle']]
                    )
                    hist_fig_x.update_layout(
                        xaxis=dict(
                            title=dict(
                                text=f"{x_axis}",
                                font=dict(family="Roboto Mono", size=14,
                                          color=generate_color_palette(dark_mode)['text'])
                            ),
                            tickfont=dict(color=generate_color_palette(dark_mode)['text'])
                        ),
                        yaxis=dict(
                            title=dict(
                                text="count",
                                font=dict(family="Roboto Mono", size=14,
                                          color=generate_color_palette(dark_mode)['text'])
                            ),
                            tickfont=dict(color=generate_color_palette(dark_mode)['text'])
                        ),
                        modebar=dict(bgcolor='rgba(0,0,0,0)'),
                        font=dict(family="Roboto Mono"),
                        title=dict(
                            font=dict(family="Roboto Mono", color=generate_color_palette(dark_mode)['title'])
                        ),
                        height=410
                    )

                    st.plotly_chart(hist_fig_x, use_container_width=True, key="hist_x")
                else:
                    st.error(f"{x_axis} data is not available.")

                if y_axis in scraped_data.columns:
                    hist_fig_y = px.histogram(
                        scraped_data,
                        x=y_axis,
                        title=f"{y_axis} distribution",
                        labels={y_axis: y_axis},
                        nbins=20,
                        color_discrete_sequence=[generate_color_palette(dark_mode)['middle']]
                    )
                    hist_fig_y.update_layout(
                        xaxis=dict(
                            title=dict(
                                text=f"{y_axis}",
                                font=dict(family="Roboto Mono", size=14,
                                          color=generate_color_palette(dark_mode)['text'])
                            ),
                            tickfont=dict(color=generate_color_palette(dark_mode)['text'])
                        ),
                        yaxis=dict(
                            title=dict(
                                text="count",
                                font=dict(family="Roboto Mono", size=14,
                                          color=generate_color_palette(dark_mode)['text'])
                            ),
                            tickfont=dict(color=generate_color_palette(dark_mode)['text'])
                        ),
                        modebar=dict(bgcolor='rgba(0,0,0,0)'),
                        font=dict(family="Roboto Mono"),
                        title=dict(
                            font=dict(family="Roboto Mono", color=generate_color_palette(dark_mode)['title'])
                        ),
                        height=410
                    )

                    st.plotly_chart(hist_fig_y, use_container_width=True, key="hist_y")
                else:
                    st.error(f"{y_axis} data is not available.")

        st.divider()

        col1, col2 = st.columns([3, 1])

        with col1:
            if "scraped_data" in st.session_state and not st.session_state["scraped_data"].empty:
                scraped_data = st.session_state["scraped_data"]
                st.subheader("treemap: hotel distribution by price range and...")
                color_option = st.radio("choose color by", ['num_review', 'rate_review', 'rating_stars'], index=0,
                                        horizontal=True)
                if 'hotel_type' in scraped_data.columns and 'price_range' in scraped_data.columns:
                    treemap_fig = px.treemap(
                        scraped_data,
                        path=['hotel_type', 'price_range'],
                        values='price',
                        color=color_option,
                        color_continuous_scale=generate_color_palette(dark_mode)['palette']
                    )

                    # Aktualizacja etykiet w treemap
                    treemap_fig.update_traces(
                        root_color='rgba(0,0,0,0)',
                        marker=dict(cornerradius=5)
                    )

                    # Aktualizacja tytułów osi i ogólnej etykiety koloru
                    treemap_fig.update_layout(
                        coloraxis_colorbar=dict(
                            tickfont=dict(color=generate_color_palette(dark_mode)['title']),
                            # Zmiana koloru tekstu etykiet na skali kolorów
                            titlefont=dict(color=generate_color_palette(dark_mode)['text'])  # Zmiana koloru tytułu skali kolorów
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=30, l=25, r=25, b=25),
                        font=dict(family="Roboto Mono"),
                        modebar=dict(bgcolor='rgba(0,0,0,0)')
                    )

                    st.plotly_chart(treemap_fig, use_container_width=True)
                else:
                    st.write(scraped_data.columns)
                    st.error("oops! columns do not exist.")
            if "scraped_data" in st.session_state and not st.session_state["scraped_data"].empty:
                st.subheader("3D scatter plot: distance, rate_review, rating_stars")
                options = ['distance', 'rate_review', 'rating_stars', 'num_review', 'price']
                x_axis_3d = st.selectbox("select X-axis (3D)", options, index=0, key="x_3d")
                y_axis_3d = st.selectbox("select Y-axis (3D)", options, index=1, key="y_3d")
                z_axis_3d = st.selectbox("select Z-axis (3D)", options, index=2, key="z_3d")

                if all(col in scraped_data.columns for col in [x_axis_3d, y_axis_3d, z_axis_3d]):
                    fig_3d = px.scatter_3d(
                        scraped_data,
                        x=x_axis_3d,
                        y=y_axis_3d,
                        z=z_axis_3d,
                        color=z_axis_3d,
                        size=x_axis_3d,
                        color_continuous_scale=generate_color_palette(dark_mode)['palette']
                    )
                    fig_3d.update_traces(marker=dict(opacity=0.7))
                    fig_3d.update_layout(
                        coloraxis_colorbar=dict(
                            tickfont=dict(color=generate_color_palette(dark_mode)['title']),
                            # Zmiana koloru tekstu etykiet na skali kolorów
                            titlefont=dict(color=generate_color_palette(dark_mode)['text'])  # Zmiana koloru tytułu skali kolorów
                        ),
                        height=700,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=30, l=25, r=25, b=25),
                        font=dict(family="Roboto Mono"),
                        modebar=dict(bgcolor='rgba(0,0,0,0)'))

                    st.plotly_chart(fig_3d, use_container_width=True)
                else:
                    st.error(f"selected columns are not in the data: {x_axis_3d}, {y_axis_3d}, {z_axis_3d}.")
            with col2:
                st.write("""
                #### price categories description:

                - **cheap**: items priced from 0 to 150 per night. these are affordable options suitable for budget-conscious buyers.
                - **moderate**: prices between 150 and 300 per night. these items are moderately priced and offer a balance between quality and cost.
                - **expensive**: items priced from 300 to 500 per night. these are higher-priced items often associated with luxury features or premium brands.
                - **luxury**: items priced over 500 per night. these are high-end, exclusive products often linked to top-quality materials or prestigious brands.
                """)

            st.divider()


def write_about(dark_mode):
    """
    Funkcja wyświetlająca stronę informacyjną z opisem aplikacji.

    """
    st.divider()
    st.title("about this app")
    st.divider()

    st.header("welcome to the **booking scraper**!")
    st.write(
        """
        **🕸️booking scraper** is your ultimate companion for exploring hotel data and making informed booking decisions.  
        this app brings together **web scraping**, **interactive visualizations**, and **advanced analysis** to simplify your travel planning.  
        """
    )

    st.subheader("✨ **what can you do here?**")
    st.write(
        """
        - 🌍 **search Hotels**: input a destination, travel dates, and the number of guests to begin exploring.  
        - 🕵️‍♀️ **scrape Data**: automatically collect detailed information about hotels, including prices, reviews, and distances from the city center.  
        - 🗺️ **interactive Map**: visualize hotel locations, highlighting the top 5 based on your chosen criteria.  
        - 📊 **analyze Trends**: dive into interactive charts and graphs, such as scatter plots and 3D visualizations, to better understand the market.  
        - 💡 **customize Your Search**: refine results by selecting key metrics like price, ratings, or proximity.  
        """
    )

    st.subheader("🚀 **how to use the app?**")
    st.write(
        """
        1. **start with the home page**:
           - enter the city name, check-in and check-out dates, and the number of adults.  
           - click **find my stay** to start scraping data from Booking.com.  
        2. **explore hotel information**:
           - navigate through tabs to view detailed stats, interactive maps, and customizable visualizations.  
        3. **understand trends**:
           - use scatter plots and histograms to analyze relationships between metrics like price and reviews.  
           - switch to 3D views for a more dynamic exploration of data.  
        4. **top picks**:
           - identify the best hotels based on your preferred metrics (e.g., lowest price, highest rating).
           
        **pro-tip**: if you're unsure about any feature, hover over the question mark icons (❓) to get more details.  
        """
    )

    st.image("data/image_doc_1.png", caption="example of filtering hotels by criteria", width=800)

    st.subheader("🔧 **what’s under the hood?**")
    st.write(
        """
        this app leverages a combination of cutting-edge python libraries and frameworks to deliver an interactive and visually appealing experience:
        - **scrapy**: for scraping detailed hotel data from Booking.com across multiple criteria.  
        - **streamlit**: to create a sleek, user-friendly interface.  
        - **pandas**: for data preprocessing and analysis.  
        - **plotly**: for creating dynamic 2D and 3D visualizations.  
        - **folium**: for interactive maps that showcase hotel locations.  
        - **custom design**: integrated light/dark mode and a visually engaging color palette.  

        **modular code structure**:
        - the project consists of multiple Python files to ensure maintainability:
          - `scraper_booking.py`: handles scraping hotel lists and essential data.  
          - `scraper_hotel_details.py`: scrapes additional details like coordinates and types of accommodations.  
          - `app.py`: the main application logic for interacting with users and presenting data.  
        """
    )
    with st.expander("scrapy_booking.py"):
        st.write(
            """
            ### description of `scraper_booking.py`

            the `scraper_booking.py` file is a scrapy-based scraper that automates the collection of hotel data from booking.com. the script handles dynamic url generation, data extraction, and result processing.  

            #### main functions:
            1. **`__init__(self, url)`**  
               creates a list of urls to scrape based on the main provided link and various suffixes (e.g., sorting by price or ratings).  

            2. **`parse(self, response)`**  
               extracts hotel data such as:  
               - name, address, price per night  
               - distance from the center, star rating  
               - review score and number of reviews  
               links are stored and filtered to avoid duplicates.  

            3. **`close(self, reason)`**  
               after scraping, it removes duplicates from the csv file and launches an additional scraper for detailed information.  

            4. **`remove_duplicates_from_csv(file_path)`**  
               removes duplicates from the csv file based on unique links.  

            5. **`run_spider(url)`**  
               launches the scraper as a separate process using `subprocess`.

            #### key features:
            - supports sorting results in various ways (e.g., price, distance, ratings).  
            - automatic removal of duplicates.  
            - dynamically configurable with any provided url.  
            """
        )

    with st.expander("scraper_hotel_details.py"):
        st.write(
            """
            ### description of `scraping_details.py`

            the `scraping_details.py` script focuses on extracting additional information for each hotel, such as geographic coordinates and type of accommodation. it processes a list of hotel links provided in a csv file and updates the data dynamically.  

            #### main functions:
            1. **`__init__(self, csv_file)`**  
               initializes the spider by loading hotel links from the csv file and setting up start urls.  

            2. **`parse(self, response)`**  
               extracts:  
               - hotel type (e.g., apartment, hostel, hotel).  
               - geographic coordinates (latitude and longitude).  
               updates the original csv file with the newly scraped data.  

            3. **`close(self, reason)`**  
               cleans the updated csv by removing duplicate entries based on coordinates.  

            4. **`remove_duplicates_from_csv(file_path)`**  
               removes duplicate rows from the csv file to ensure clean and consistent data.  

            #### key features:
            - dynamically scrapes hotel pages using start urls.  
            - ensures data accuracy with automatic duplicate removal.  
            - seamlessly integrates with the `scraper_booking.py` script for enriched datasets.  
            """
        )

    with st.expander("app.py"):
        st.write(
            """
            ### description of `app.py`

            the `app.py` file is the main streamlit application that serves as an interactive user interface for searching and visualizing hotel data scraped from booking.com. the application provides users with a seamless experience by allowing them to input their travel details, fetch hotel information, and explore the results on an interactive map with a variety of filtering options.

            #### main functions:
            1. **`create_map(scraped_data, top_5_hotels=None, filter_top_5=False)`**  
               this function generates an interactive map that visualizes the scraped hotel data. each hotel is marked on the map, and additional details such as hotel name, price range, and rating can be viewed when users click on a marker.  
               - **`top_5_hotels`** (optional): highlights the top 5 hotels based on user-specified criteria such as price or review rating.  
               - **`filter_top_5`** (optional): when set to true, it filters the map to show only the top 5 hotels.  

            2. **`load_scraped_data(file_path)`**  
               this function loads the hotel data from a csv file generated by the scraping process. it processes the data to handle missing values, clean up any inconsistencies, and add useful derived columns like **`price_range`**, which categorizes hotels into affordable, mid-range, and expensive price brackets.  
               the function ensures that the data is ready for further analysis or visualization.

            3. **`home_content(dark_mode)`**  
               displays the main content of the application. it presents a user-friendly form where users can input their travel information, such as destination, check-in and check-out dates, and the number of guests.  
               upon submitting the form, the app generates a link to booking.com for the user to check out the available hotels directly. additionally, the app triggers the scraping process, displaying relevant statistics about the number of hotels found, average price, and review score.

            4. **`run_scraper(url)`**  
               initiates the scraping process by calling a pre-configured scraping function. this function makes use of dynamic url generation to scrape hotel data from booking.com based on the user’s input. it also handles potential errors or missing information gracefully, ensuring the app continues functioning even in case of incomplete data.

            #### key features:
            - **interactive map**: visualize hotel locations on an interactive map with markers that provide additional details, such as price range and rating.  
            - **hotel search**: users can search for hotels by entering travel details such as city, dates, and guest count. the app then scrapes relevant hotel information from booking.com.  
            - **data insights**: after the scraping process is complete, the app displays key statistics such as average price, review score, and number of hotels available.  
            - **customizable filters**: users can filter hotels by specific criteria, such as top-rated, most affordable, or closest to the city center.  
            - **dark mode**: the app supports dark mode for improved user experience in low-light environments.  
            - **error handling**: the app is built with robust error handling, ensuring smooth user interaction even in cases of incomplete or invalid input.  
            - **price range classification**: hotels are classified into different price ranges, allowing users to easily find options within their budget.  
            - **booking link**: after the search, the app generates a direct link to booking.com for users to make reservations.  

            this streamlit app is designed to be both informative and user-friendly, providing a streamlined process for discovering hotels and analyzing key data points in a visually appealing way. with the integration of interactive maps and dynamic filtering, it enhances the overall travel planning experience for users.
            """
        )

    st.subheader("🎨 **custom theme settings**")
    st.write(
        """
        the visual appeal of this app is enhanced by a custom theme setup that was crafted manually to ensure a unique user experience.  

        - the **theme_settings.py** file serves as the backbone for applying a personalized light/dark theme.  
        - the theme data is loaded from a JSON file, allowing flexibility for easy updates or future changes.  
        - he color palette leverages a combination of vibrant and subtle shades to create a balance between aesthetic and usability.  
        """
    )


    st.write(
        """
        key features of the `theme_settings.py` file include:  

        - **custom CSS and inline styles**: precisely tailored styles for headers, forms, buttons, and interactive elements.  
        - **dynamic adaptability**: adjusts the interface seamlessly based on the selected light or dark mode.  
        - **integration with Google Fonts**: the app uses the 'Roboto Mono' font to ensure a sleek and professional look.  
        - **modular structure**: simplifies the process of applying themes across different components of the app.  
        """
    )

    st.write(
        """
        the manual configuration of this file highlights the effort put into ensuring the app's design remains both engaging and functional.  
        """
    )

    with st.expander("theme_settings.py"):
        st.write(
            """
            ### description of `theme_settings.py`

            the `theme_settings.py` file is responsible for managing the theme and color scheme of the streamlit application. it allows users to apply custom themes, including light and dark modes, and generates a color palette based on the selected theme for a more visually appealing user interface.

            #### main functions:
            1. **`load_theme(file_path)`**  
               loads a theme from a json file, ensuring that the app can dynamically change its appearance based on the theme settings.

            2. **`apply_theme(dark_mode, theme_file)`**  
               applies the selected theme to the app. it adjusts colors for various components such as the header, buttons, and text based on the dark or light mode preference.

            3. **`generate_color_palette(dark_mode, theme_file)`**  
               generates a color palette using the primary and secondary colors from the theme, allowing for consistent styling across the app. it calculates gradient colors to create a smooth visual experience.

            #### key features:
            - **customizable themes**: easily switch between light and dark modes to match user preferences.
            - **color palette generation**: dynamically generate color gradients based on the theme, enhancing the app's visual design.
            - **seamless integration**: the theme settings are seamlessly integrated into the app, providing a consistent and customizable user experience.

            this module ensures that the streamlit application has a visually consistent theme, with customizable options for light and dark modes, contributing to an improved overall user experience.
            """
        )

    st.subheader("💻 **tips for best experience**")
    st.write(
        """
        - tor an optimal view, set your browser zoom to **75%**.  
        - use the **dark mode toggle** for a more comfortable experience in low-light environments.  
        - if scraping takes time, feel free to explore the preloaded dataset in the app.  
        - enjoy exploring interactive elements such as maps, charts, and tabs.  
        """
    )

    st.subheader("🔮 **future improvements**")
    st.write(
        """
        i am constantly looking to enhance the app. some planned updates include:
        - integration with other booking platforms (e. g. airbnb) for broader comparisons.  
        - more advanced machine learning models for hotel recommendations.  
        - real-time updates to scraped data for the latest offers.  
        - localization support for non-English languages.  
        """
    )

    st.write("💬 got feedback or suggestions? feel free to reach out!")
    st.markdown(
        """
        <div style="text-align: center; font-size: larger; font-weight: bold;">
        happy scraping! 🌟
        </div>
        """,
        unsafe_allow_html=True
    )


def main():
    # Page configuration
    st.set_page_config(
        page_title="booking scraper",
        page_icon="🏨",
        layout="wide"
    )

    # Uruchomienie funkcji popup na początku
    st.components.v1.html("""
    
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,100..700;1,100..700&display=swap');
            
            div {{
            font-family: 'Roboto Mono', sans-serif !important;
            font-weight: 700 !important;
            text-align: left !important;
        }}
            </style>
        <script>
            alert("hi there! before u start please set your browser zoom to 75% :) thanks!");
        </script>
    """, height=0)  # Ustawienie odpowiedniej etykiety

    # Inicjalizacja sesji
    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    col1, col2, col3, col4 = st.columns([5.5, 1, 1, 5.5])

    with col2:
        # Tworzenie przycisków st.button
        if st.button("home", key="home"):
            st.session_state["page"] = "home"
    with col3:
        if st.button("about", key="about"):
            st.session_state["page"] = "about"

    # Dark mode toggle button
    dark_mode = st.toggle("switch mode", value=False)
    apply_theme(dark_mode)

    st.title("🕸️booking scraper")  # Tytuł obok logo

    # Wywoływanie odpowiednich funkcji w zależności od wyboru zakładek
    if st.session_state["page"] == "home":
        home_content(dark_mode)
    elif st.session_state["page"] == "about":
        write_about(dark_mode)


if __name__ == "__main__":
    main()
