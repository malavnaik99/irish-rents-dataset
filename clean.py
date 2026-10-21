# %% [markdown]
# # Irish rents (RTB), cleaned
# A portfolio project by [Malav Naik](https://malavnaik99.github.io).
#
# The Residential Tenancies Board (RTB) publishes the average monthly rent of **new tenancies** registered in each
# half-year, by area, number of bedrooms and property type. The Central Statistics Office (CSO) publishes it as table
# [RIH02](https://data.cso.ie/table/RIH02). This notebook turns that table into one tidy, documented file.
#
# Source: CSO / RTB, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

# %%
import io
import os
import urllib.request

import pandas as pd

URL = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/RIH02/CSV/1.0/en"
raw = pd.read_csv(io.BytesIO(urllib.request.urlopen(URL, timeout=120).read()), dtype=str)
print(f"{len(raw):,} rows, columns: {list(raw.columns)}")

# %% [markdown]
# ## 1. Keep the useful columns, with plain names
# The CSO file repeats each category as a code column and a label column, and has columns that never change
# (table name, statistic, unit = euro). We keep the labels, plus the location code, which encodes the area level.

# %%
def tidy(raw):
    df = pd.DataFrame({
        "period": raw["HalfYear"],
        "location": raw["Location"].str.strip(),
        "location_code": raw["C03004V03625"],
        "bedrooms": raw["Number of Bedrooms"],
        "property_type": raw["Property Type"],
        "rent_eur": pd.to_numeric(raw["VALUE"], errors="coerce"),
    })
    df["year"] = df["period"].str[:4].astype(int)
    df["half"] = df["period"].str[-1].astype(int)
    df["period_start"] = pd.to_datetime(df["year"].astype(str) + "-" + df["half"].map({1: "01", 2: "07"}) + "-01")
    return df

df = tidy(raw)
assert raw["STATISTIC"].nunique() == 1 and raw["UNIT"].eq("Euro").all()
df.head()

# %% [markdown]
# ## 2. Missing rents mean "not published", not zero
# The RTB leaves a cell empty when too few new tenancies were registered to give a reliable average.
# We drop those rows, but first measure how many there are and where.

# %%
missing = df["rent_eur"].isna()
print(f"{missing.mean():.1%} of cells have no published rent")
print(df.assign(missing=missing).groupby("bedrooms")["missing"].mean().sort_values().round(3).to_string())
df = df[~missing].copy()

# %% [markdown]
# ## 3. Label each location's level
# Locations mix counties ("Carlow"), towns ("Carlow Town") and smaller areas ("Tullow, Carlow", "Artane, Dublin 5").
# Counties are matched by name; other names without a comma are towns or Dublin postal districts.

# %%
COUNTIES = {"Carlow", "Cavan", "Clare", "Cork", "Donegal", "Dublin", "Galway", "Kerry", "Kildare", "Kilkenny",
            "Laois", "Leitrim", "Limerick", "Longford", "Louth", "Mayo", "Meath", "Monaghan", "Offaly", "Roscommon",
            "Sligo", "Tipperary", "Waterford", "Westmeath", "Wexford", "Wicklow"}


def level(code, name):
    if name in ("Ireland", "State"):
        return "national"
    if name in COUNTIES:
        return "county"
    return "area" if "," in name else "town or district"

df["location_level"] = [level(c, n) for c, n in zip(df["location_code"], df["location"])]
print(df.groupby("location_level")["location"].nunique().to_string())
for lv in ["national", "county", "town or district"]:
    print(lv, sorted(df.loc[df.location_level == lv, "location"].unique()))

# %% [markdown]
# ## 4. Mark the "all" and grouped categories
# "All bedrooms", "1 to 2 bed", "1 to 3 bed" and "All property types" are totals over other rows. Mark them so
# nobody adds them up twice.

# %%
df["is_total_bedrooms"] = df["bedrooms"].isin(["All bedrooms", "1 to 2 bed", "1 to 3 bed"])
df["is_total_property_type"] = df["property_type"].eq("All property types")

# %% [markdown]
# ## 5. Checks and save

# %%
key = ["period", "location_code", "bedrooms", "property_type"]
assert not df.duplicated(key).any(), "one row per period, location, bedrooms and property type"
assert df["rent_eur"].between(50, 20000).all(), df["rent_eur"].describe()
cols = ["period", "year", "half", "period_start", "location", "location_code", "location_level",
        "bedrooms", "property_type", "is_total_bedrooms", "is_total_property_type", "rent_eur"]
df = df[cols].sort_values(["location_code", "bedrooms", "property_type", "period_start"]).reset_index(drop=True)
os.makedirs("out", exist_ok=True)
df.to_parquet("out/irish_rents_rtb.parquet", index=False)
df.to_csv("out/irish_rents_rtb.csv", index=False)
print(f"{len(df):,} rows, {df.location.nunique()} locations, {df.period.min()}–{df.period.max()}")

# %% [markdown]
# ## 6. A first look: average rent, all homes

# %%
allrows = df[df.is_total_bedrooms & df.is_total_property_type & df.bedrooms.eq("All bedrooms")]
pivot = allrows[allrows.location_level.isin(["national", "county"])].pivot_table(
    index="period", columns="location", values="rent_eur")
show = [c for c in ["Ireland", "Dublin", "Cork", "Galway", "Leitrim"] if c in pivot]
print(pivot[show].iloc[[0, len(pivot) // 2, -1]].round(0).to_string())
