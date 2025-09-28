from usfiscaldata import datatypes

import pandas as pd


def test_registry():
    assert datatypes.TYPE_REGISTRY["STRING"] is datatypes.cast_string


def test_cast_date():
    s = pd.Series(["2000-01-01", "2001-06-11", "null"])
    expected = pd.Series(
        [
            pd.Timestamp(year=2000, month=1, day=1),
            pd.Timestamp(year=2001, month=6, day=11),
            pd.NaT,
        ]
    )
    actual = datatypes.cast_date(s, fmt="YYYY-MM-DD")
    pd.testing.assert_series_equal(actual, expected)


def test_cast_string():
    s = pd.Series(["Yes", "No", "null"])
    expected = pd.Series(["Yes", "No", ""])
    actual = datatypes.cast_string(s, fmt="String")
    pd.testing.assert_series_equal(actual, expected)


def test_cast_number():
    s = pd.Series(["1123", "3049000", "null"])
    expected = pd.to_numeric(pd.Series([1123, 3049000, pd.NA]))
    actual = datatypes.cast_number(s, fmt="10.2")
    pd.testing.assert_series_equal(actual, expected)
