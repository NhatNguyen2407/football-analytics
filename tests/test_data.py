"""Regression tests for event definitions and missing-data cases."""

import sys
import types
import unittest
from unittest.mock import patch

import pandas as pd

if "streamlit" not in sys.modules:
    try:
        import streamlit
    except ImportError:
        fake_streamlit = types.ModuleType("streamlit")
        fake_streamlit.cache_data = lambda **kwargs: lambda function: function
        sys.modules["streamlit"] = fake_streamlit

if "statsbombpy" not in sys.modules:
    try:
        import statsbombpy
    except ImportError:
        fake_statsbomb = types.ModuleType("statsbombpy")
        fake_statsbomb.sb = types.SimpleNamespace(competitions=lambda: None, matches=lambda **kwargs: None)
        sys.modules["statsbombpy"] = fake_statsbomb

from src.data import summarise_events, matches


class EventSummaryTests(unittest.TestCase):
    def setUp(self):
        self.events = pd.DataFrame([
            {"period": 1, "player": "A", "team": "Blue", "type": "Shot", "shot_outcome": "Goal", "pass_outcome": None, "pass_goal_assist": None},
            {"period": 2, "player": "A", "team": "Blue", "type": "Pass", "shot_outcome": None, "pass_outcome": None, "pass_goal_assist": True},
            {"period": 2, "player": "A", "team": "Blue", "type": "Pass", "shot_outcome": None, "pass_outcome": "Incomplete", "pass_goal_assist": None},
            {"period": 4, "player": "B", "team": "Red", "type": "Shot", "shot_outcome": "Saved", "pass_outcome": None, "pass_goal_assist": None},
            {"period": 5, "player": "A", "team": "Blue", "type": "Shot", "shot_outcome": "Goal", "pass_outcome": None, "pass_goal_assist": None},
            {"period": 1, "player": None, "team": "Red", "type": "Shot", "shot_outcome": "Goal", "pass_outcome": None, "pass_goal_assist": None},
        ])

    def test_counts_and_shootout_exclusion(self):
        result = summarise_events(self.events).set_index("player")
        self.assertEqual(result.loc["A", ["shots", "goals", "assists", "passes", "completed_passes"]].tolist(), [1, 1, 1, 2, 1])
        self.assertEqual(result.loc["A", "pass_accuracy"], 50)
        self.assertEqual(result.loc["B", "shots"], 1)
        self.assertEqual(result["goals"].sum(), 1)

    def test_zero_passes_are_undefined_accuracy(self):
        result = summarise_events(self.events).set_index("player")
        self.assertTrue(pd.isna(result.loc["B", "pass_accuracy"]))

    def test_empty_input(self):
        result = summarise_events(pd.DataFrame())
        self.assertTrue(result.empty)
        self.assertIn("pass_accuracy", result.columns)

    def test_missing_required_field(self):
        with self.assertRaisesRegex(ValueError, "period"):
            summarise_events(self.events.drop(columns="period"))

    def test_missing_pass_outcome_not_counted_as_success(self):
        with self.assertRaisesRegex(ValueError, "Pass outcome"):
            summarise_events(self.events.drop(columns="pass_outcome"))

    def test_no_goal_assist_column(self):
        result = summarise_events(self.events.drop(columns="pass_goal_assist"))
        self.assertEqual(result["assists"].sum(), 0)

    def test_shootout_only_returns_empty(self):
        result = summarise_events(self.events.loc[self.events["period"].eq(5)])
        self.assertTrue(result.empty)

    def test_match_selection(self):
        comps = pd.DataFrame([
            {"competition_name": "FIFA World Cup", "season_name": "2022", "competition_id": 43, "season_id": 106},
            {"competition_name": "FIFA World Cup", "season_name": "2018", "competition_id": 43, "season_id": 3},
        ])
        fixtures = pd.DataFrame([{"match_date": "2022-12-18", "match_id": 10}, {"match_date": "2022-11-20", "match_id": 1}])
        with patch("src.data.sb.competitions", return_value=comps), patch("src.data.sb.matches", return_value=fixtures) as get_matches:
            result = matches()
        get_matches.assert_called_once_with(competition_id=43, season_id=106)
        self.assertEqual(result.iloc[0]["match_id"], 10)


if __name__ == "__main__":
    unittest.main()
