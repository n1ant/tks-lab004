# graphs.py

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent

RESULTS_DIR = (
    BASE_DIR / "results"
)

GRAPHS_DIR = (
    RESULTS_DIR / "graphs"
)


def load_results(
    filename: str,
) -> list[dict]:

    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Файл не найден: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def save_graph(
    filename: str,
):
    GRAPHS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        GRAPHS_DIR / filename
    )

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=200,
    )

    plt.close()

    print(
        f"График сохранён: {path}"
    )


def graph_loss_vs_intensity(
    results: list[dict],
):
    intensities = [
        result["intensity"]
        for result in results
    ]

    losses = [
        result["statistics"][
            "loss_ratio"
        ] * 100
        for result in results
    ]

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        intensities,
        losses,
        marker="o",
    )

    plt.xlabel(
        "Интенсивность передачи, пак./с"
    )

    plt.ylabel(
        "Коэффициент потерь, %"
    )

    plt.title(
        "Зависимость потерь от "
        "интенсивности передачи"
    )

    plt.grid(
        True,
        alpha=0.3,
    )

    save_graph(
        "task1_loss_vs_intensity.png"
    )


def graph_delivery_violations(
    results: list[dict],
):
    names = [
        result["name"]
        for result in results
    ]

    losses = [
        result["statistics"][
            "loss_ratio"
        ] * 100
        for result in results
    ]

    duplicates = [
        result["statistics"][
            "duplicate_ratio"
        ] * 100
        for result in results
    ]

    reordered = [
        result["statistics"][
            "out_of_order_ratio"
        ] * 100
        for result in results
    ]

    x = range(len(names))

    width = 0.25

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        [
            value - width
            for value in x
        ],
        losses,
        width=width,
        label="Потери",
    )

    plt.bar(
        x,
        duplicates,
        width=width,
        label="Дублирование",
    )

    plt.bar(
        [
            value + width
            for value in x
        ],
        reordered,
        width=width,
        label="Переупорядочивание",
    )

    plt.xticks(
        list(x),
        names,
        rotation=20,
        ha="right",
    )

    plt.ylabel(
        "Доля пакетов, %"
    )

    plt.title(
        "Обнаруженные нарушения доставки"
    )

    plt.legend()

    plt.grid(
        axis="y",
        alpha=0.3,
    )

    save_graph(
        "delivery_violations.png"
    )


def graph_delay_and_jitter(
    results: list[dict],
):
    names = [
        result["name"]
        for result in results
    ]

    average_delay = [
        result["statistics"][
            "average_delay"
        ]
        for result in results
    ]

    jitter = [
        result["statistics"][
            "jitter"
        ]
        for result in results
    ]

    x = range(len(names))

    width = 0.35

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        [
            value - width / 2
            for value in x
        ],
        average_delay,
        width=width,
        label="Средняя задержка",
    )

    plt.bar(
        [
            value + width / 2
            for value in x
        ],
        jitter,
        width=width,
        label="Джиттер",
    )

    plt.xticks(
        list(x),
        names,
        rotation=20,
        ha="right",
    )

    plt.ylabel(
        "Время, мс"
    )

    plt.title(
        "Задержка и джиттер"
    )

    plt.legend()

    plt.grid(
        axis="y",
        alpha=0.3,
    )

    save_graph(
        "task3_delay_jitter.png"
    )


def graph_received_vs_sent(
    results: list[dict],
):
    names = [
        result["name"]
        for result in results
    ]

    sent = [
        result["statistics"][
            "sent"
        ]
        for result in results
    ]

    received = [
        result["statistics"][
            "received"
        ]
        for result in results
    ]

    x = range(len(names))

    width = 0.35

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        [
            value - width / 2
            for value in x
        ],
        sent,
        width=width,
        label="Отправлено",
    )

    plt.bar(
        [
            value + width / 2
            for value in x
        ],
        received,
        width=width,
        label="Принято",
    )

    plt.xticks(
        list(x),
        names,
        rotation=20,
        ha="right",
    )

    plt.ylabel(
        "Количество пакетов"
    )

    plt.title(
        "Количество отправленных "
        "и принятых пакетов"
    )

    plt.legend()

    plt.grid(
        axis="y",
        alpha=0.3,
    )

    save_graph(
        "sent_vs_received.png"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Построение графиков "
            "лабораторной работы №4"
        )
    )

    parser.add_argument(
        "--task",
        choices=[
            "1",
            "2",
            "3",
            "all",
        ],
        default="all",
        help="Номер задания",
    )

    args = parser.parse_args()

    task_files = {
        "1": (
            RESULTS_DIR
            / "tables"
            / "task1.json"
        ),

        "2": (
            RESULTS_DIR
            / "tables"
            / "task2.json"
        ),

        "3": (
            RESULTS_DIR
            / "tables"
            / "task3.json"
        ),
    }

    if args.task in ("1", "all"):
        task1 = load_results(
            str(task_files["1"])
        )

        graph_loss_vs_intensity(
            task1
        )

    if args.task in ("2", "all"):
        task2 = load_results(
            str(task_files["2"])
        )

        graph_delivery_violations(
            task2
        )

    if args.task in ("3", "all"):
        task3 = load_results(
            str(task_files["3"])
        )

        graph_delay_and_jitter(
            task3
        )

        graph_received_vs_sent(
            task3
        )

    print(
        "\nВсе графики построены."
    )


if __name__ == "__main__":
    main()