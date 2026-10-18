# World Cup Player Analytics

A small interactive dashboard for exploring player-level event statistics from the 2022 FIFA World Cup. I built it to practise cleaning and aggregating football event data with Pandas, visualising results with Plotly, and presenting comparisons in Streamlit.

## Features

- Browse the 2022 World Cup fixture list and select an individual match.
- Filter players by national team.
- Explore goals, assists, shots, attempted passes, completed passes, and pass accuracy.
- Rank players with an interactive bar chart.
- Compare two players from the same match.

## Data and methodology

I use [StatsBomb Open Data](https://github.com/statsbomb/open-data), loaded through [statsbombpy](https://github.com/hudl/statsbombpy). The app fetches public match and event data and caches responses for 24 hours. An internet connection is required to retrieve data that has not been cached.

- Statistics are **per selected match**, not tournament-wide totals.
- Penalty shootout events (period 5) are excluded. Regular-time and extra-time events are included.
- Goals count shot events with the outcome `Goal`; own goals are not included in this metric.
- Assists count pass events marked as goal assists in the source data.
- A pass is completed when the pass event has no unsuccessful outcome recorded.
- Pass accuracy is `completed passes / attempted passes * 100`. It is undefined for players with zero passes.
- I do not estimate player minutes or per-90 statistics, because the current version does not verify minutes played.

These event definitions can differ from official FIFA statistics. The comparison is descriptive, not a player-quality ranking.

## Run locally

Use Python 3.11 or 3.12. In a terminal opened in the project directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If Python 3.11 is not installed, replace `py -3.11` with an installed compatible version (for example, `py -3.12`). Streamlit will display a local URL, usually `http://localhost:8501`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests use synthetic events to check goal and assist counts, pass accuracy, missing fields, penalty shootout exclusion, and match selection. They do not require a StatsBomb network connection.

## Deploy to Streamlit Community Cloud

- Push the project to GitHub.
- Open [Streamlit Community Cloud](https://share.streamlit.io/) and create a new app.
- Select this repository, branch `main`, and entry point `app.py`.
- Deploy and verify that a match loads, player filters work, and player comparison responds correctly.

No API keys are required for StatsBomb Open Data. Initial data retrieval may take longer than a cached load.

## Project structure

```text
app.py                 # Streamlit dashboard
src/data.py            # Match retrieval and event aggregation
tests/test_data.py     # Regression tests
requirements.txt       # Python packages
.streamlit/config.toml # Streamlit theme
.gitignore
```

## Possible extensions

- Validate lineup/substitution timings and add per-90 statistics.
- Cache a tournament-wide player summary for cross-match comparisons.
- Investigate differences between shot-based goals and official scorelines.

## Credits

Data provided by [StatsBomb Open Data](https://github.com/statsbomb/open-data). I retain source attribution as requested by the data provider.
