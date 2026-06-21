from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class InformationTimeContract:
    target_time: datetime
    decision_time: datetime
    gate_closure_time: datetime

    def validate(self) -> None:
        times = {
            "target_time": self.target_time,
            "decision_time": self.decision_time,
            "gate_closure_time": self.gate_closure_time,
        }

        for name, value in times.items():
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(
                    f"{name} must be timezone-aware: {value!r}"
                )

        if self.decision_time > self.gate_closure_time:
            raise ValueError(
                "decision_time cannot be later than gate_closure_time."
            )

        if self.gate_closure_time >= self.target_time:
            raise ValueError(
                "gate_closure_time must be earlier than target_time."
            )

    def data_is_available(self, publication_time: datetime) -> bool:
        if (
            publication_time.tzinfo is None
            or publication_time.utcoffset() is None
        ):
            raise ValueError(
                "publication_time must be timezone-aware."
            )

        return publication_time <= self.decision_time
