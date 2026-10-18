"""Retrieve World Cup matches and summarise StatsBomb player events."""

import pandas as pd
import streamlit as st
from statsbombpy import sb

COMPETITION = "FIFA World Cup"
SEASON = "2022"
METRICS = ["shots", "goals", "assists", "passes", "completed_passes"]


@st.cache_data(ttl=86400, show_spinner=False)
def matches():
    competitions = sb.competitions()
    selected = competitions.loc[
        competitions["competition_name"].eq(COMPETITION)
        & competitions["season_name"].astype(str).eq(SEASON)
    ]
    if selected.empty:
        raise ValueError("2022 FIFA World Cup data is not available from StatsBomb.")
    competition = selected.iloc[0]
    games = sb.matches(
        competition_id=int(competition["competition_id"]),
        season_id=int(competition["season_id"]),
    )
    if games.empty:
        raise ValueError("No matches were returned for the 2022 World Cup.")
    return games.sort_values(["match_date", "match_id"], ascending=False).reset_index(drop=True)


def summarise_events(events):
    """Count on-field actions only; period 5 is a penalty shootout."""
    columns = ["team", "player", *METRICS, "pass_accuracy"]
    if events.empty:
        return pd.DataFrame(columns=columns)

    required = {"period", "player", "team", "type"}
    missing = required.difference(events.columns)
    if missing:
        raise ValueError(f"Missing required event fields: {', '.join(sorted(missing))}")

    valid = events.loc[events["period"].isin([1, 2, 3, 4]) & events["player"].notna()].copy()
    if valid.empty:
        return pd.DataFrame(columns=columns)

    is_shot = valid["type"].eq("Shot")
    is_pass = valid["type"].eq("Pass")
    if is_shot.any() and "shot_outcome" not in valid:
        raise ValueError("Shot outcome information is unavailable.")
    if is_pass.any() and "pass_outcome" not in valid:
        raise ValueError("Pass outcome information is unavailable.")

    shot_outcome = valid.get("shot_outcome", pd.Series(index=valid.index, dtype="object"))
    pass_outcome = valid.get("pass_outcome", pd.Series(index=valid.index, dtype="object"))
    goal_assist = valid.get("pass_goal_assist", pd.Series(False, index=valid.index))
    valid = valid.assign(
        shots=is_shot.astype(int),
        goals=(is_shot & shot_outcome.eq("Goal")).astype(int),
        assists=(is_pass & goal_assist.eq(True)).astype(int),
        passes=is_pass.astype(int),
        completed_passes=(is_pass & pass_outcome.isna()).astype(int),
    )
    result = valid.groupby(["team", "player"], as_index=False)[METRICS].sum()
    result["pass_accuracy"] = (
        100 * result["completed_passes"] / result["passes"].replace(0, float("nan"))
    ).round(1)
    return result.sort_values(["goals", "shots", "passes"], ascending=False).reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def match_players(match_id):
    return summarise_events(sb.events(match_id=int(match_id)))
