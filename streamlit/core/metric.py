import streamlit as st

def _metric(df):
    metric = st.sidebar.selectbox(
        "Kennzahl",
        options=[c for c in [
            "Digitalhaushalt Soll (eng)", "Digitalhaushalt Ist (eng)",
            "Digitalhaushalt Soll (weit)", "Digitalhaushalt Ist (weit)",
            "Gesamthaushalt Soll", "Gesamthaushalt Ist",
        ] if c in df.columns],
    )

    return metric

if __name__ == "__main__":
    _metric()