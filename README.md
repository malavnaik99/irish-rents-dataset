# Irish rents (RTB), cleaned

The official average monthly rent of new tenancies in Ireland, every half-year from 2008 to 2025, by county, town and
area, number of bedrooms and property type: cleaned into one tidy, documented table (201,912 rows, 437 locations).

- **Dataset:** [Hugging Face](https://huggingface.co/datasets/Malavnaik/irish-rents-rtb) · [Kaggle](https://www.kaggle.com/datasets/malavnaik/irish-rents-rtb)
- **Cleaning notebook:** [Kaggle](https://www.kaggle.com/code/malavnaik/cleaning-irish-rents-rtb) (same code as `clean.py`)

## How it works
`clean.py` downloads CSO table [RIH02](https://data.cso.ie/table/RIH02), keeps readable columns, drops unpublished
rents (70% of cells: the RTB doesn't publish an average when too few tenancies were registered), labels each location
as county / town or district / area, flags totals, and checks there is one row per period, area, bedrooms and property
type. `publish.py` uploads the result and a data card. The *Build dataset* workflow runs both and the Kaggle notebook.

## Source and licence
CSO / Residential Tenancies Board, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Cleaned by
[Malav Naik](https://malavnaik99.github.io). Rents are for new tenancies only and are not adjusted for inflation.
