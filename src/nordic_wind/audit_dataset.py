from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from nordic_wind.data_availability import (
    attach_information_time_audit,
    summarize_information_time_audit,
)
from nordic_wind.data_contracts import load_dataset_contract


def load_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)

    if suffix == ".parquet":
        return pd.read_parquet(path)

    raise ValueError(
        f"Unsupported input format '{suffix}'. Use CSV or Parquet."
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a dataset for information-time leakage."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/audits"),
    )
    parser.add_argument(
        "--fail-on-violation",
        action="store_true",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    frame = load_table(arguments.input)
    contract = load_dataset_contract(arguments.contract)
    audited = attach_information_time_audit(frame, contract)

    summary = summarize_information_time_audit(
        audited.loc[
            :,
            [
                "missing_event_time",
                "missing_publication_time",
                "missing_decision_time",
                "publication_after_decision",
                "decision_not_before_event",
                "available_at_decision",
                "information_time_violation",
            ],
        ]
    )

    arguments.output_dir.mkdir(parents=True, exist_ok=True)

    row_output = arguments.output_dir / (
        f"{arguments.input.stem}_information_time_audit.csv"
    )
    summary_output = arguments.output_dir / (
        f"{arguments.input.stem}_information_time_summary.json"
    )

    audited.to_csv(row_output, index=False)

    with summary_output.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print(f"Dataset: {contract.name}")
    print(f"Rows: {summary['total_rows']:,}")
    print(f"Available at decision: {summary['available_rows']:,}")
    print(f"Violations: {summary['violation_rows']:,}")
    print(f"Row audit: {row_output}")
    print(f"Summary: {summary_output}")

    if arguments.fail_on_violation and summary["violation_rows"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
