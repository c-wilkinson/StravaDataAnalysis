"""Tests for dashboard-only formatting helpers."""

import pandas as pd

from dashboard.formatting import rounded_numeric


def test_rounded_numeric_handles_nat_and_zero_values():
    """Nullable display columns do not call ``round`` on ``NaT`` objects."""
    values = pd.Series([171.234, pd.NaT, 0], dtype="object")

    result = rounded_numeric(values, decimals=1, zero_as_missing=True)

    assert result.iloc[0] == 171.2
    assert pd.isna(result.iloc[1])
    assert pd.isna(result.iloc[2])
    assert str(result.dtype) == "Float64"
