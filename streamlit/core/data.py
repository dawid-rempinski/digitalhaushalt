import pandas as pd
import streamlit as st

def _data():
    @st.cache_data
    def get_data():
        df = pd.read_csv("../data/transformed/digitalhaushalt_transformed.csv")
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
            "kategorie": "Kategorie"
        }
        df.rename(columns=LABELS, inplace=True, errors="ignore")
        return df

    df = get_data()

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
    cat_cols = [c for c in df.select_dtypes(exclude="number").columns if c != "Jahr"]

    SOLL = "Digitalhaushalt Soll (eng)"
    IST  = "Digitalhaushalt Ist (eng)"

    return df, T_TO_MRD, FILTER_COLS, num_cols, cat_cols, SOLL, IST

if __name__ == "__main__":
    _data()