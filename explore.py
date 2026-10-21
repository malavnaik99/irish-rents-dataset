"""One-off look at the CSO rent tables: columns, values and time span."""
import io
import urllib.request
import pandas as pd

URL = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/{}/CSV/1.0/en"
for table in ["RIQ02", "RIH02", "RIA02"]:
    try:
        df = pd.read_csv(io.BytesIO(urllib.request.urlopen(URL.format(table), timeout=120).read()))
    except Exception as e:
        print(table, "failed:", e); continue
    print(f"\n===== {table}: {len(df):,} rows")
    print(df.head(3).to_string())
    for c in df.columns:
        u = df[c].nunique()
        print(f"- {c}: {u} distinct", list(df[c].drop_duplicates()[:8]) if u < 5000 else "")
    print("missing VALUE:", df["VALUE"].isna().sum() if "VALUE" in df else "n/a")
