import json
import streamlit as st
import matplotlib.colors as mcolors
import numpy as np


def load_theme(file_path):
    """Funkcja ładująca motyw z pliku JSON.

    Args:
        file_path (str): Ścieżka do pliku JSON zawierającego dane motywu.

    Returns:
        dict: Słownik zawierający dane motywu, lub pusty słownik w przypadku błędu.
    """
    try:
        with open(file_path, 'r') as f:
            theme = json.load(f)  # Wczytywanie motywu z pliku JSON
        return theme
    except Exception as e:
        print(f"Error loading theme: {e}")  # Wypisanie błędu, jeśli plik nie zostanie wczytany
        return {}


def apply_theme(dark_mode, theme_file="material-theme_pink_blue.json"):
    """Funkcja zmieniająca styl aplikacji na podstawie koloru wczytanego z pliku JSON.
        Args:
        dark_mode (bool): Określa, czy aktywować tryb ciemny.
        theme_file (str): Ścieżka do pliku JSON z motywem.
    """
    theme = load_theme(theme_file)

    alpha = "0D"

    if dark_mode:
        selected_theme = theme['schemes']['light']
    else:
        selected_theme = theme['schemes']['dark']

    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,100..700;1,100..700&display=swap');
            
            /* Styl dla górnego paska (nadpisanie .stAppHeader) */
            .stAppHeader {{
                background-color: transparent !important;
                color: {selected_theme['onPrimary']} !important;
                height: 60px !important;
            }}
            
            .css-1u4fkce {{
    visibility: hidden;
}}
            

            
        h1 {{
            font-family: 'Roboto Mono', sans-serif !important;
            font-weight: 700 !important;
            font-style: bold !important;
            text-align: left !important;
        }}
            
        h2 {{
            font-family: 'Roboto Mono', sans-serif !important;
            font-weight: 400 !important;
            text-align: left !important;
        }}
        
        h3, h4, h5, h6 {{
            font-family: 'Roboto Mono', sans-serif !important;
            font-weight: 300 !important;
            text-align: left !important;
        }}
    
        html, body, p, div, span, input {{
            font-family: 'Roboto Mono', sans-serif !important;
            font-weight: 400;
        }}


        /* Styl dla całej aplikacji */
        .stApp {{
                 
                     background-size: cover !important;
            background-repeat: no-repeat !important;
            background-color: {selected_theme['surfaceContainer']} !important;
            color: {selected_theme['onSurface']} !important;
            
        }}
        
        /* Metryki */
        
        .stMetric > div{{
            color: {selected_theme['onSurface']} !important;
            
        }}
        
        .stMetric {{
            color: {selected_theme['onSurface']} !important;
            border: 1px solid  {selected_theme['primary']} !important;
            border-shadow: 2px !important;
            box-shadow: 4px 4px 10px  {selected_theme['onSurface']}{alpha};
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            
        }}

        /* Styl pól tekstowych i etykiet formularza */
        input, textarea, select {{
            background-color: {selected_theme['inversePrimary']} !important;
            color: {selected_theme['onSecondaryContainer']} !important;
        }}

        /* Styl dla etykiet formularza */
        label {{
            color: {selected_theme['onSecondaryContainer']} !important;
        }}
        
        /* Styl dla formularza */
        .stForm {{
            background-color: {selected_theme['secondaryContainer']} !important;
            border: 0.5px solid {selected_theme['secondary']} !important;
        }}

        /* Styl przycisków */
        button {{
            background-color: {selected_theme['surfaceTint']} !important;
            color: {selected_theme['onPrimary']} !important;
        }}
        


    /* Styl przycisku Home */
    div.st-key-home > div > button {{
        position: absolute;
        top: -30px;
        margin: 0 10px;
        text-decoration: none;
        color: {selected_theme['primary']} !important;
        font-family: 'Roboto Mono', sans-serif;
        border: 0px;
        font-weight: 700;
        padding: 8px 12px;
        transition: all 0.3s ease;
        background-color: transparent !important;
        width: 125px !important;
        height: 40px !important;
    }}

    /* Efekt hover na przycisku */
    div.st-key-home > div > button:hover {{
        border: 0px;
        background-color: {selected_theme['onTertiaryFixed']} !important;
        color: {selected_theme['inversePrimary']} !important;
        border-radius: 0px;
    }}

    /* Aktywny przycisk - zmiana koloru i obramowanie */
    div.st-key-home > div > button:focus {{
        border-radius: 0px;
        border-bottom: 2px solid {selected_theme['onPrimary']} !important;
        background-image: linear-gradient(180deg,transparent, {selected_theme['onPrimary']}) !important;
        
    }}
    


    /* Styl przycisku about */
    div.st-key-about > div > button {{
        position: absolute;
        top: -30px;
        margin: 0 10px;
        text-decoration: none;
        color: {selected_theme['primary']} !important;
        font-family: 'Roboto Mono', sans-serif;
        border: 0px;
        font-weight: 600;
        padding: 8px 12px;
        transition: all 0.3s ease;
        background-color: transparent !important;
        width: 125px !important;
        height: 40px !important;
    }}

    /* Efekt hover na przycisku */
    div.st-key-about > div > button:hover {{
        border: 0px;
        background-color: {selected_theme['onTertiaryFixed']} !important;
        color: {selected_theme['inversePrimary']} !important;
        border-radius: 0px;
    }}

    /* Aktywny przycisk - zmiana koloru i obramowanie */
    div.st-key-about > div > button:focus {{
        border-radius: 0px;
        border-bottom: 2px solid {selected_theme['onPrimary']} !important;
        background-image: linear-gradient(180deg,transparent, {selected_theme['onPrimary']}) !important;
        
    }}
    
        div.st-key-about > div > button:active {{
        border-radius: 0px;
        border-bottom: 2px solid {selected_theme['onPrimary']} !important;
        background-image: linear-gradient(180deg,transparent, {selected_theme['onPrimary']}) !important;
        
    }}
        
        /* Styl przycisków */
        .stTabs [data-baseweb="tab-list"] {{
            display: flex;
            justify-content: space-between;
            box-shadow: none !important;
            
        }}
        
        .stTabs [data-baseweb="tab"] {{
            flex: 1; /* Każda zakładka zajmuje równą szerokość */
            text-align: center;
            font-weight: bold !important;
            background-color: transparent !important; 
            color:  {selected_theme['onPrimaryContainer']} !important;
            box-shadow: none !important;
            transition: all 0.5s ease;
            
        }}
        
        /* Efekt podświetlenia i cienia przy najechaniu */
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {selected_theme['secondary']} !important; /* Kolor tła przy najechaniu */
            box-shadow: 0px 6px 12px {selected_theme['onSurface']}; /* Cień */
            color: {selected_theme['onSecondary']} !important; /* Kolor tekstu po najechaniu */
        }}
        
        /* Styl aktywnej zakładki */
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
                background-color: {selected_theme['outlineVariant']} !important;
                color: {selected_theme['onSurface']} !important;
                box-shadow: 0px 6px 12px {selected_theme['primary']} !important; /* Cień aktywnej zakładki */
        }}
        
        div[data-baseweb="tab-highlight"] {{
                background-color: {selected_theme['primary']}; /* Przykład: zmienia tło na pomarańczowe */
                border-radius: 20px; /* Opcjonalnie: zaokrąglenie rogów */
                height: 3px; /* Opcjonalnie: zmiana wysokości */
        }}
        

        .stTextInput > div > div {{
                background-color: {selected_theme['primaryContainer']} !important;
                color: {selected_theme['onPrimaryContainer']} !important;
        }}
        
        /* Checkbox - kolor */
        label[data-baseweb="checkbox"] > span:first-child {{
                background-color: {selected_theme['tertiary']} !important;
                color: {selected_theme['onTertiary']} !important;
        }}
        
        div[data-testid="stWidgetLabel"] {{
                color: {selected_theme['onSurface']} !important;
        }}
        
        
        /* Ustawienie toggle button na prawo */
        
        label[data-baseweb="checkbox"] {{
                position: absolute;
                top: 50px;
                right: 10px;
                color: {selected_theme['onSurface']} !important;
        }}
        
        /* Toggle button - kolor */
        label[data-baseweb="checkbox"] > div:first-child {{
                background-color: {selected_theme['onSurface']} !important;
        }}
        
        /* Radio button - kolor */
        
        label[data-baseweb="radio"] {{
                color: {selected_theme['onSurface']} !important;
        }}
        
        /* Radio button - kolor */
        label[data-baseweb="radio"] > div:first-child {{
                background-color: {selected_theme['onSurface']} !important;
        }}
        
        /* Radio button - tytuly - kolor */
        label[data-baseweb="radio"] > div:nth-child(3) > div {{
                color: {selected_theme['onSurface']} !important;
        }}
        
        
        .st-bj > div > div {{
            background-color: {selected_theme['surfaceContainer']} !important;
            color: {selected_theme['onSurface']} !important;
        }}
        

        
        .st-a1 {{
                background-color: {selected_theme['inverseOnSurface']} !important;
        }}
        
        /*Selectboxy*/
        .stSelectbox > div > div > div {{
                background-color: {selected_theme['onTertiary']} !important;
                color: {selected_theme['primary']} !important;
        }}
        
        svg[data-baseweb="icon"] {{
                background-color: {selected_theme['onTertiary']} !important;
                color: {selected_theme['primary']} !important;
        }}
        
        /* Kalendarz */
        
        div[data-baseweb="calendar"] > div > div > div {{
                background-color: {selected_theme['onTertiary']} !important;
                font-family: 'Roboto Mono', sans-serif;
        }}
        
        div[role="grid"] {{
                color: {selected_theme['tertiary']} !important;
                background-color: {selected_theme['onTertiary']} !important;
                font-family: 'Roboto Mono', sans-serif;
        }}
        
        div[role="gridcell"] {{
        color: {selected_theme['tertiary']} !important;
                background-color: {selected_theme['onTertiary']} !important;
                transform: none;
                font-family: 'Roboto Mono', sans-serif;
        }}
        
        /* Errory i powiadomienia */ 
        div[role="alert"] {{
                background-color: {selected_theme['onErrorContainer']} !important;
                color: {selected_theme['errorContainer']} !important;
        }}
        
        
        
        /* Styl wykresów Plotly - transparentne tło */
        .main-svg {{
        background: transparent !important; /* Tło wykresu */
        }}
        
        path[d*="M25,35a5,5"] {{
            fill: transparent !important; 
        }}
        
         .stHorizontalBlock:hover {{

            background-color: {selected_theme['onSurface']}{alpha} !important; /* Jasne tło */
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1) !important; /* Cień */
            transition: all 0.3s ease-in-out; /* Płynne przejście */
            border-radius: 10px; /* Zaokrąglenie rogów */
            cursor: pointer; /* Zmiana kursora */
        }}
        
        
        #tabs-bui3-tabpanel-0 .stVerticalBlock:hover {{
            background-color: {selected_theme['onSurface']}{alpha} !important; /* Jasne tło */
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1) !important; /* Cień */
            transition: all 0.3s ease-in-out; /* Płynne przejście */
            border-radius: 10px; /* Zaokrąglenie rogów */
            cursor: pointer; /* Zmiana kursora */
        }}
        
         
        </style>
        """,
        unsafe_allow_html=True
    )


def generate_color_palette(dark_mode, theme_file="material-theme_pink_blue.json"):
    """
    Generuje paletę kolorów przechodzącą od koloru początkowego do końcowego.

    Args:
        dark_mode (bool): Określa, czy włączyć tryb ciemny.
        theme_file (str): Ścieżka do pliku z motywem.

    Returns:
        dict: Słownik zawierający paletę kolorów oraz kolory dla tytułu i tekstu.
    """

    theme = load_theme(theme_file)

    if dark_mode:
        selected_theme = theme['schemes']['light']
    else:
        selected_theme = theme['schemes']['dark']

    title_color = selected_theme['primary']
    text_color = selected_theme['onSurface']

    # Konwersja kolorów do przestrzeni RGB
    start_rgb = mcolors.to_rgb(selected_theme['onTertiary'])
    end_rgb = mcolors.to_rgb(selected_theme['tertiaryFixedDim'])

    # Interpolacja liniowa między kolorami
    palette = [
        mcolors.to_hex(
            np.array(start_rgb) * (1 - t) + np.array(end_rgb) * t
        )
        for t in np.linspace(0, 1, 40)
    ]

    # Znalezienie środkowej wartości
    middle_index = len(palette) // 2
    middle_color_plot = palette[middle_index]

    return {'palette': palette, 'middle': middle_color_plot, 'title': title_color, 'text': text_color}
