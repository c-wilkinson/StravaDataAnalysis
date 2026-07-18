# Interactive dashboard

The Streamlit dashboard is an additional presentation layer for the existing
Strava analysis project. The existing Matplotlib and Seaborn functions continue
to generate the PNG files under `assets/`.

## Data flow

```text
Strava API -> encrypted SQLite -> Pandas DataFrames
                                  |-> existing PNG graphs
                                  `-> date-only Parquet export -> Streamlit dashboard
```

The dashboard never opens the SQLite database and does not import the DAO. A
normal project run writes the following dashboard datasets:

- `data/dashboard/activities.parquet`
- `data/dashboard/splits.parquet`
- `data/dashboard/metadata.json`

Activity names, calendar dates and available heart-rate values are retained.
Precise start times, time zones and UTC offsets are not exported.

## Generate the data and images

```bash
poetry run python src/main.py --skip-fetch
```

Omit `--skip-fetch` when the normal Strava refresh should run first.

## Run the dashboard

```bash
poetry run streamlit run src/dashboard/app.py
```

The dashboard includes interactive distance, pace, effort, distribution and
machine-learning views, an activity and split explorer, and a gallery of the
existing PNG graphs.

## Development checks

```bash
poetry run black --check src
poetry run pylint src
poetry run pytest
```
