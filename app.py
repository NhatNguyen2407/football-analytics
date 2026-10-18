"""Interactive dashboard for 2022 World Cup player event statistics."""

import plotly.express as px
import streamlit as st

from src.data import match_players, matches

st.set_page_config(page_title="World Cup Player Analytics", page_icon="⚽", layout="wide")
st.title("World Cup Player Analytics")
st.caption("2022 FIFA World Cup | StatsBomb Open Data | Individual match analysis")

try:
    games = matches()
except Exception as error:
    st.error(f"Could not load the match list: {error}")
    st.stop()

options = {
    f"{game.match_date} | {game.home_team} vs {game.away_team} | #{game.match_id}": int(game.match_id)
    for game in games.itertuples()
}
with st.sidebar:
    st.header("Match selection")
    selected_match = st.selectbox("Match", options=list(options))

try:
    players = match_players(options[selected_match])
except Exception as error:
    st.error(f"Could not load match events: {error}")
    st.stop()

if players.empty:
    st.info("No player events are available for this match.")
    st.stop()

with st.sidebar:
    teams = sorted(players["team"].dropna().unique())
    selected_teams = st.multiselect("Teams", options=teams, default=teams)
filtered = players.loc[players["team"].isin(selected_teams)].reset_index(drop=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Players with events", len(filtered))
c2.metric("Goals (excluding shootouts)", int(filtered["goals"].sum()))
c3.metric("Shots", int(filtered["shots"].sum()))
c4.metric("Completed passes", int(filtered["completed_passes"].sum()))

st.subheader("Player statistics")
st.dataframe(filtered, hide_index=True, use_container_width=True)

if filtered.empty:
    st.info("Select at least one team to display statistics.")
    st.stop()

metrics = ["goals", "assists", "shots", "passes", "completed_passes", "pass_accuracy"]
selected_metric = st.selectbox("Rank players by", options=metrics, format_func=lambda x: x.replace("_", " ").title())
top_players = filtered.sort_values(selected_metric, ascending=False).head(15)
chart = px.bar(
    top_players,
    x=selected_metric,
    y="player",
    color="team",
    orientation="h",
    title=f"Top players - {selected_metric.replace('_', ' ')}",
    labels={selected_metric: selected_metric.replace("_", " ").title(), "player": "Player"},
)
chart.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(chart, use_container_width=True)

st.subheader("Head-to-head comparison")
player_options = [f"{row.player} ({row.team})" for row in filtered.itertuples()]
if len(player_options) < 2:
    st.info("Select teams containing at least two players to compare.")
else:
    left, right = st.columns(2)
    player_a = left.selectbox("Player A", options=player_options, index=0)
    player_b = right.selectbox("Player B", options=player_options, index=1)
    if player_a == player_b:
        st.warning("Choose two different players.")
    else:
        selection = filtered.iloc[[player_options.index(player_a), player_options.index(player_b)]].copy()
        selection["label"] = [player_a, player_b]
        st.dataframe(
            selection.set_index("label")[["goals", "assists", "shots", "passes", "completed_passes", "pass_accuracy"]],
            use_container_width=True,
        )
        comparison = selection.melt(
            id_vars="label",
            value_vars=["goals", "assists", "shots", "passes"],
            var_name="metric",
            value_name="count",
        )
        st.plotly_chart(px.bar(comparison, x="metric", y="count", color="label", barmode="group"), use_container_width=True)

st.divider()
st.caption(
    "Methodology: All figures cover the selected match only. Period 5 (penalty shootout) is excluded. "
    "Goals count shots marked 'Goal' (not own goals). Assists are StatsBomb goal-assist passes. "
    "A completed pass has no recorded pass outcome. Players with no attempted passes have no "
    "pass-accuracy percentage. Playing time and per-90 statistics are not estimated. "
    "Figures may differ from official tournament statistics."
)
st.caption("Data: StatsBomb Open Data (https://github.com/statsbomb/open-data)")
