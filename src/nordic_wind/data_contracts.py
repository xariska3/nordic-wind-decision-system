from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class DatasetContract:
    name: str
    event_time_column: str
    publication_time_column: str
    decision_time_column: str
    required_columns: tuple[str, ...] = ()
    entity_columns: tuple[str, ...] = ()
    target_column: str | None = None

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "DatasetContract":
        return cls(
            name=str(values["name"]),
            event_time_column=str(values["event_time_column"]),
            publication_time_column=str(values["publication_time_column"]),
            decision_time_column=str(values["decision_time_column"]),
            required_columns=tuple(values.get("required_columns", ())),
            entity_columns=tuple(values.get("entity_columns", ())),
            target_column=values.get("target_column"),
        )

    def validate_columns(self, columns: Iterable[str]) -> None:
        available = set(columns)
        required = {
            self.event_time_column,
            self.publication_time_column,
            self.decision_time_column,
            *self.required_columns,
            *self.entity_columns,
        }

        if self.target_column is not None:
            required.add(self.target_column)

        missing = sorted(required.difference(available))
        if missing:
            raise ValueError(
                f"Dataset '{self.name}' is missing required columns: {missing}"
            )


def load_dataset_contract(path: str | Path) -> DatasetContract:
    contract_path = Path(path)

    if not contract_path.exists():
        raise FileNotFoundError(
            f"Dataset contract not found: {contract_path.resolve()}"
        )

    with contract_path.open("r", encoding="utf-8") as file:
        values = json.load(file)

    return DatasetContract.from_mapping(values)
