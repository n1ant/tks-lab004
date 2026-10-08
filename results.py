# results.py

import csv
import json
from dataclasses import asdict
from pathlib import Path

from models import ExperimentResult


def save_results_csv(
    results: list[ExperimentResult],
    filename: str,
):
    path = Path(filename)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "experiment",
        "name",
        "packets_sent",
        "interval",
        "intensity",
        "elapsed_time",
        "received",
        "unique_received",
        "lost",
        "loss_ratio",
        "duplicates",
        "duplicate_ratio",
        "out_of_order",
        "out_of_order_ratio",
        "average_delay",
        "min_delay",
        "max_delay",
        "jitter",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for number, result in enumerate(
            results,
            start=1,
        ):
            stats = result.statistics

            writer.writerow(
                {
                    "experiment": number,
                    "name": result.name,
                    "packets_sent": (
                        result.packets_sent
                    ),
                    "interval": (
                        result.interval
                    ),
                    "intensity": (
                        result.intensity
                    ),
                    "elapsed_time": (
                        result.elapsed_time
                    ),
                    "received": (
                        stats["received"]
                    ),
                    "unique_received": (
                        stats[
                            "unique_received"
                        ]
                    ),
                    "lost": stats["lost"],
                    "loss_ratio": (
                        stats["loss_ratio"]
                    ),
                    "duplicates": (
                        stats["duplicates"]
                    ),
                    "duplicate_ratio": (
                        stats[
                            "duplicate_ratio"
                        ]
                    ),
                    "out_of_order": (
                        stats["out_of_order"]
                    ),
                    "out_of_order_ratio": (
                        stats[
                            "out_of_order_ratio"
                        ]
                    ),
                    "average_delay": (
                        stats[
                            "average_delay"
                        ]
                    ),
                    "min_delay": (
                        stats["min_delay"]
                    ),
                    "max_delay": (
                        stats["max_delay"]
                    ),
                    "jitter": (
                        stats["jitter"]
                    ),
                }
            )

    print(
        f"Результаты сохранены: {path}"
    )


def save_results_json(
    results: list[ExperimentResult],
    filename: str,
):
    path = Path(filename)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = [
        asdict(result)
        for result in results
    ]

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )

    print(
        f"Результаты сохранены: {path}"
    )