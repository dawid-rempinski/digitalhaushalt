# digitalhaushalt

Data preparation and dashboard for analysing Germany's federal digital budget
("Digitalhaushalt"), based on the Agora open data export.

## Pipeline

Run the notebooks in order. Each step reads the previous step's output from `data/`:

1. **`01_aufbereitung.ipynb`** — reads the raw Agora export and the mapping tables
   from `data/raw/`, builds the year-specific Einzelplan/Kapitel mappings, and writes
   `digitalhaushalt_transformed.csv` and `..._with_titel_text.csv` to `data/transformed/`.
2. **`02_keywords.ipynb`** — extracts and cleans keywords from the budget titles and
   writes `..._extracted_keywords_cleaned.csv`.
3. **`03_semantik.ipynb`** — adds semantic/NLP features (spaCy) and writes
   `digitalhaushalt_semantic_features.csv`.

## Dashboard

```
streamlit run streamlit/Exploration.py
```

The dashboard reads `digitalhaushalt_transformed.csv`, the cleaned keywords file and
`digitalhaushalt_semantic_features.csv` from `data/transformed/`.

## Setup

```
pip install -r requirements.txt
python -m spacy download de_core_news_sm
```

## Layout

- `data/raw/` — inputs (Agora export, yearly HH files, mapping tables)
- `data/transformed/` — pipeline outputs
- `streamlit/` — dashboard
- `docs/` — reference PDFs (studies, plans)
