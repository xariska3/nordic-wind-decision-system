import pandas as pd
import pytest

from nordic_wind.data_availability import (
    audit_information_time,
    summarize_information_time_audit,
)
from nordic_wind.data_contracts import DatasetContract


CONTRACT = DatasetContract(
    name="test",
    event_time_column="target_time",
    publication_time_column="publication_time",
    decision_time_column="decision_time",
    required_columns=("price_area",),
)


def test_information_time_audit_flags_late_publication() -> None:
    frame = pd.DataFrame(
        {
            "price_area": ["DK1", "DK1"],
            "target_time": [
                "2026-01-02T00:00:00+01:00",
                "2026-01-02T01:00:00+01:00",
            ],
            "decision_time": [
                "2026-01-01T11:00:00+01:00",
                "2026-01-01T11:00:00+01:00",
            ],
            "publication_time": [
                "2026-01-01T10:30:00+01:00",
                "2026-01-01T11:30:00+01:00",
            ],
        }
    )

    audit = audit_information_time(frame, CONTRACT)
    summary = summarize_information_time_audit(audit)

    assert audit["available_at_decision"].tolist() == [True, False]
    assert audit["publication_after_decision"].tolist() == [False, True]
    assert summary["available_rows"] == 1
    assert summary["violation_rows"] == 1


def test_information_time_audit_rejects_naive_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "price_area": ["DK1"],
            "target_time": ["2026-01-02 00:00:00"],
            "decision_time": ["2026-01-01T11:00:00+01:00"],
            "publication_time": ["2026-01-01T10:30:00+01:00"],
        }
    )

    with pytest.raises(ValueError, match="timezone-naive"):
        audit_information_time(frame, CONTRACT)
