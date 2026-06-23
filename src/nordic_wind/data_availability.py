from __future__ import annotations

from typing import Any

import pandas as pd

from nordic_wind.data_contracts import DatasetContract


AUDIT_COLUMNS = (
    "missing_event_time",
    "missing_publication_time",
    "missing_decision_time",
    "publication_after_decision",
    "decision_not_before_event",
    "available_at_decision",
    "information_time_violation",
)


def _parse_timezone_aware_series(
    values: pd.Series,
    column_name: str,
) -> pd.Series:
    parsed: list[pd.Timestamp] = []
    naive_rows: list[Any] = []

    for index, value in values.items():
        if pd.isna(value):
            parsed.append(pd.NaT)
            continue

        try:
            timestamp = pd.Timestamp(value)
        except (TypeError, ValueError):
            parsed.append(pd.NaT)
            continue

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            naive_rows.append(index)
            parsed.append(pd.NaT)
            continue

        parsed.append(timestamp.tz_convert("UTC"))

    if naive_rows:
        preview = naive_rows[:10]
        raise ValueError(
            f"Column '{column_name}' contains timezone-naive timestamps "
            f"at rows {preview}. Store timestamps with an explicit timezone."
        )

    return pd.Series(
        pd.DatetimeIndex(parsed),
        index=values.index,
        name=column_name,
        dtype="datetime64[ns, UTC]",
    )


def audit_information_time(
    frame: pd.DataFrame,
    contract: DatasetContract,
) -> pd.DataFrame:
    contract.validate_columns(frame.columns)

    event_time = _parse_timezone_aware_series(
        frame[contract.event_time_column],
        contract.event_time_column,
    )
    publication_time = _parse_timezone_aware_series(
        frame[contract.publication_time_column],
        contract.publication_time_column,
    )
    decision_time = _parse_timezone_aware_series(
        frame[contract.decision_time_column],
        contract.decision_time_column,
    )

    audit = pd.DataFrame(index=frame.index)

    audit["missing_event_time"] = event_time.isna()
    audit["missing_publication_time"] = publication_time.isna()
    audit["missing_decision_time"] = decision_time.isna()

    audit["publication_after_decision"] = (
        publication_time.notna()
        & decision_time.notna()
        & publication_time.gt(decision_time)
    )

    audit["decision_not_before_event"] = (
        decision_time.notna()
        & event_time.notna()
        & decision_time.ge(event_time)
    )

    violation_columns = [
        "missing_event_time",
        "missing_publication_time",
        "missing_decision_time",
        "publication_after_decision",
        "decision_not_before_event",
    ]

    audit["information_time_violation"] = audit[
        violation_columns
    ].any(axis=1)

    audit["available_at_decision"] = ~audit[
        "information_time_violation"
    ]

    return audit.loc[:, AUDIT_COLUMNS]


def attach_information_time_audit(
    frame: pd.DataFrame,
    contract: DatasetContract,
) -> pd.DataFrame:
    audit = audit_information_time(frame, contract)
    return pd.concat(
        [frame.reset_index(drop=True), audit.reset_index(drop=True)],
        axis=1,
    )


def filter_available_at_decision(
    frame: pd.DataFrame,
    contract: DatasetContract,
) -> pd.DataFrame:
    audit = audit_information_time(frame, contract)
    return frame.loc[audit["available_at_decision"]].copy()


def summarize_information_time_audit(
    audit: pd.DataFrame,
) -> dict[str, int | float]:
    missing = sorted(set(AUDIT_COLUMNS).difference(audit.columns))
    if missing:
        raise ValueError(
            f"Audit frame is missing required audit columns: {missing}"
        )

    total_rows = int(len(audit))
    available_rows = int(audit["available_at_decision"].sum())
    violation_rows = int(audit["information_time_violation"].sum())

    return {
        "total_rows": total_rows,
        "available_rows": available_rows,
        "violation_rows": violation_rows,
        "availability_rate": (
            float(available_rows / total_rows) if total_rows else 0.0
        ),
        "missing_event_time": int(audit["missing_event_time"].sum()),
        "missing_publication_time": int(
            audit["missing_publication_time"].sum()
        ),
        "missing_decision_time": int(
            audit["missing_decision_time"].sum()
        ),
        "publication_after_decision": int(
            audit["publication_after_decision"].sum()
        ),
        "decision_not_before_event": int(
            audit["decision_not_before_event"].sum()
        ),
    }
