from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "project_name",
    "project_root",
    "legacy_project_root",
    "legacy_data_root",
    "data_root",
    "output_root",
    "timezone",
    "price_areas",
    "model_family",
    "random_seed",
    "strict_information_time",
    "require_exact_weather_vintages",
    "allow_unverified_realtime_generation_features",
    "day_ahead_gate_local_time",
    "forecast_decision_local_time",
    "primary_frequency",
    "fallback_frequency",
}


def load_project_config(
    config_path: str | Path = "configs/project.json",
) -> dict[str, Any]:
    """Load and validate the main project configuration."""

    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")

    with path.open("r", encoding="utf-8") as file:
        config: dict[str, Any] = json.load(file)

    missing = sorted(REQUIRED_KEYS.difference(config))
    if missing:
        raise ValueError(f"Missing required configuration keys: {missing}")

    if config["model_family"].lower() != "lightgbm":
        raise ValueError("The rebuilt project must use LightGBM as its model family.")

    if not config["strict_information_time"]:
        raise ValueError("strict_information_time must remain enabled.")

    if config["allow_unverified_realtime_generation_features"]:
        raise ValueError(
            "Unverified real-time generation features must remain disabled."
        )

    price_areas = config["price_areas"]
    if sorted(price_areas) != ["DK1", "DK2"]:
        raise ValueError("price_areas must contain exactly DK1 and DK2.")

    return config