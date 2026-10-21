"""Publishes the cleaned table (out/) to Hugging Face and Kaggle (public, approved by Malav).
The data card's numbers are computed from the file itself, so they always match it."""
import json
import os
import shutil
import subprocess

import pandas as pd
from huggingface_hub import HfApi

HF_REPO, KAGGLE_ID = "Malavnaik/irish-rents-rtb", "malavnaik/irish-rents-rtb"
df = pd.read_parquet("out/irish_rents_rtb.parquet")
levels = df.groupby("location_level")["location"].nunique()

CARD = f"""---
license: cc-by-4.0
language: [en]
pretty_name: Irish rents (RTB), cleaned
tags: [ireland, rent, housing, cso, rtb, open-data]
---
# Irish rents (RTB), cleaned

The average monthly rent of **new tenancies** registered with Ireland's Residential Tenancies Board (RTB), per half-year,
from **{df.period.min()} to {df.period.max()}**, by location, number of bedrooms and property type: **{len(df):,} rows**.

Source: CSO table [RIH02](https://data.cso.ie/table/RIH02), "RTB Average Monthly Rent Report", © Central Statistics Office
and Residential Tenancies Board, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Cleaned by
[Malav Naik](https://malavnaik99.github.io); code and cleaning notebook: [irish-rents-dataset](https://github.com/malavnaik99/irish-rents-dataset).

## What was cleaned
- One tidy table with plain column names; the CSO's repeated code columns and constant columns are removed.
- **Unpublished rents are dropped, not zero:** the RTB leaves a cell empty when too few new tenancies were registered.
  That was 70% of the original cells, mostly for small areas and specific bedroom counts.
- Each location is labelled: {levels.get('county', 0)} counties, {levels.get('town or district', 0)} towns, cities and Dublin
  postal districts, and {levels.get('area', 0)} smaller areas.
- Totals ("All bedrooms", "1 to 2 bed", "1 to 3 bed", "All property types") are flagged, so they aren't added up twice.
- Checked: one row per period, location, bedrooms and property type; all rents between €50 and €20,000.

## Columns
| Column | Meaning |
|---|---|
| `period`, `year`, `half`, `period_start` | Half-year, e.g. `2025H2` (July–December) |
| `location`, `location_code`, `location_level` | Area name, CSO code, and county / town or district / area |
| `bedrooms`, `property_type` | As published by the RTB |
| `is_total_bedrooms`, `is_total_property_type` | True for total or grouped categories |
| `rent_eur` | Average monthly rent in euro (not adjusted for inflation) |

## Limits
These are averages for **new** tenancies registered in each half-year, not what all tenants pay. Small areas have few
tenancies, so their averages move a lot. Files: `irish_rents_rtb.parquet` and `irish_rents_rtb.csv` (same data).
"""

FIELDS = [{"name": n, "description": d} for n, d in [
    ("period", "Half-year, e.g. 2025H2 (July-December)"), ("year", "Year"), ("half", "1 = January-June, 2 = July-December"),
    ("period_start", "First day of the half-year"), ("location", "Area name as published"),
    ("location_code", "CSO location code"), ("location_level", "county, town or district, or area"),
    ("bedrooms", "Number of bedrooms, or a total/grouped category"), ("property_type", "Property type, or All property types"),
    ("is_total_bedrooms", "True for All bedrooms, 1 to 2 bed and 1 to 3 bed"),
    ("is_total_property_type", "True for All property types"),
    ("rent_eur", "Average monthly rent of new tenancies, euro, not inflation-adjusted")]]


if __name__ == "__main__":
    os.makedirs("pub", exist_ok=True)
    for f in ["irish_rents_rtb.parquet", "irish_rents_rtb.csv"]:
        shutil.copy(f"out/{f}", f"pub/{f}")
    open("pub/README.md", "w").write(CARD)

    api = HfApi()
    api.create_repo(HF_REPO, repo_type="dataset", exist_ok=True)
    api.update_repo_settings(HF_REPO, repo_type="dataset", private=False)  # Malav approved publishing on 21 Oct 2026
    api.upload_folder(repo_id=HF_REPO, repo_type="dataset", folder_path="pub")
    print(f"https://huggingface.co/datasets/{HF_REPO}")

    os.remove("pub/README.md")  # Kaggle takes the card as the description instead
    json.dump({"title": "Irish Rents (RTB) 2008-2025, cleaned", "id": KAGGLE_ID,
               "subtitle": "Average rent of new tenancies by area, bedrooms and property type",
               "licenses": [{"name": "CC-BY-4.0"}], "description": CARD.split("---", 2)[2].strip(),
               "keywords": ["housing", "real estate", "europe", "economics", "data cleaning"],
               "resources": [{"path": f, "description": f"Cleaned RTB average rents, one row per half-year, location, "
                              f"bedrooms and property type ({fmt}).", "schema": {"fields": FIELDS}}
                             for f, fmt in [("irish_rents_rtb.csv", "CSV"), ("irish_rents_rtb.parquet", "Parquet")]]},
              open("pub/dataset-metadata.json", "w"), indent=1)
    exists = subprocess.run(["kaggle", "datasets", "status", KAGGLE_ID], capture_output=True, text=True).returncode == 0
    cmd = ["kaggle", "datasets", "version", "-p", "pub", "-m", "Rebuilt from CSO RIH02"] if exists else \
          ["kaggle", "datasets", "create", "-p", "pub"]  # create is private by default
    subprocess.run(cmd, check=True)
    if exists:  # versioning updates files only; this updates the title, tags and column descriptions
        subprocess.run(["kaggle", "datasets", "metadata", "--update", "-p", "pub", KAGGLE_ID], check=True)
    print(f"https://www.kaggle.com/datasets/{KAGGLE_ID}")
