import pandas as pd
import streamlit as st
from pathlib import Path

def _data(file_path: Path = None):
    @st.cache_data
    def get_data(file_path: Path = None):
        BASE_DIR = Path(__file__).resolve().parents[2]
        if file_path is None:
            file_path = BASE_DIR / "data" / "transformed" / "digitalhaushalt_transformed.csv"
        else:
            file_path = BASE_DIR / file_path
        df = pd.read_csv(file_path)
        if "jahr" in df.columns:
            df["jahr"] = df["jahr"].astype(str)
        LABELS = {
            "digi_soll_eng":      "Digitalhaushalt Soll (eng)",
            "digi_ist_eng":       "Digitalhaushalt Ist (eng)",
            "digi_soll_weit":     "Digitalhaushalt Soll (weit)",
            "digi_ist_weit":      "Digitalhaushalt Ist (weit)",
            "ist":                "Gesamthaushalt Ist",
            "soll":               "Gesamthaushalt Soll",
            "einzelplan-text":    "Einzelplan (~Ministerium)",
            "funktion-text":      "Funktion",
            "digi_klasse-text":   "Digital Klasse",
            "digi_klasse":        "Digital Klasse ID",
            "gruppe-text":        "Gruppe",
            "kapitel-text":       "Kapitel",
            "jahr":               "Jahr",
            "hauptgruppe-text":   "Hauptgruppe",
            "obergruppe-text":    "Obergruppe",
            "hauptfunktion-text": "Hauptfunktion",
            "oberfunktion-text":  "Oberfunktion",
            "kategorie":          "Kategorie",
            "titel_text":         "Titel",
            "char_len":           "Länge des Titels",
            "cleaned_text":       "Bereinigter Titel",
        }
        df.rename(columns=LABELS, inplace=True, errors="ignore")
        return df

    df = get_data(file_path)

    T_TO_MRD = 1_000_000

    FILTER_COLS = [c for c in [
        "Jahr",
        "Kategorie",
        "Digital Klasse",
        "Einzelplan (~Ministerium)", "Kapitel",
        "Hauptfunktion", "Oberfunktion", "Funktion",
        "Hauptgruppe", "Obergruppe", "Gruppe",
    ] if c in df.columns]

    num_cols = df.select_dtypes("number").columns.tolist()
    cat_cols = [c for c in df.select_dtypes(exclude="number").columns if c not in ("Jahr", "Titel", "Bereinigter Titel")]

    SOLL = "Digitalhaushalt Soll (eng)"
    IST  = "Digitalhaushalt Ist (eng)"

    return df, T_TO_MRD, FILTER_COLS, num_cols, cat_cols, SOLL, IST

if __name__ == "__main__":
    _data()