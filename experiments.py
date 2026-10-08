# experiments.py

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from models import (
    EmulationConfig,
    ExperimentResult,
    ExperimentSpec,
)

from results import (
    save_results_csv,
    save_results_json,
)


BASE_DIR = Path(__file__).resolve().parent

RESULTS_DIR = (
    BASE_DIR / "results"
)

LOGS_DIR = (
    RESULTS_DIR / "logs"
)

TABLES_DIR = (
    RESULTS_DIR / "tables"
)


HOST = "127.0.0.1"

SERVER_PORT = 51000
EMULATOR_PORT = 52000

SERVER_TIMEOUT = 2.0


def start_server(
    packets: int,
    log_file: Path,
    result_file: Path,
):
    command = [
        sys.executable,
        str(BASE_DIR / "server.py"),

        "--host",
        HOST,

        "--port",
        str(SERVER_PORT),

        "--packets",
        str(packets),

        "--timeout",
        str(SERVER_TIMEOUT),

        "--log",
        str(log_file),

        "--result",
        str(result_file),
    ]

    return subprocess.Popen(
        command
    )


def start_emulator(
    config: EmulationConfig,
    log_file: Path,
):
    command = [
        sys.executable,
        str(
            BASE_DIR
            / "network_emulator.py"
        ),

        "--listen-host",
        HOST,

        "--listen-port",
        str(EMULATOR_PORT),

        "--target-host",
        HOST,

        "--target-port",
        str(SERVER_PORT),

        "--loss",
        str(config.loss_rate),

        "--duplicate",
        str(config.duplicate_rate),

        "--reorder",
        str(config.reorder_rate),

        "--delay",
        str(config.delay),

        "--jitter",
        str(config.jitter),

        "--reorder-delay",
        str(config.reorder_delay),

        "--log",
        str(log_file),
    ]

    if config.queue_limit is not None:
        command.extend(
            [
                "--queue-limit",
                str(config.queue_limit),
            ]
        )

    if config.service_rate is not None:
        command.extend(
            [
                "--service-rate",
                str(
                    config.service_rate
                ),
            ]
        )

    return subprocess.Popen(
        command
    )


def start_client(
    packets: int,
    interval: float,
):
    command = [
        sys.executable,
        str(BASE_DIR / "client.py"),

        "--host",
        HOST,

        "--port",
        str(EMULATOR_PORT),

        "--packets",
        str(packets),

        "--interval",
        str(interval),
    ]

    start_time = time.time()

    process = subprocess.run(
        command,
        check=True,
    )

    elapsed_time = (
        time.time() - start_time
    )

    return process, elapsed_time


def stop_process(
    process: subprocess.Popen,
):
    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(
            timeout=3
        )
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def wait_for_process(
    process: subprocess.Popen,
    timeout: float,
):
    try:
        return process.wait(
            timeout=timeout
        )

    except subprocess.TimeoutExpired:
        stop_process(process)
        return process.returncode


def run_experiment(
    spec: ExperimentSpec,
    experiment_number: int,
):
    print(
        "\n"
        + "=" * 60
    )

    print(
        f"Эксперимент: "
        f"{spec.name}"
    )

    print(
        f"Пакетов: "
        f"{spec.packets}"
    )

    print(
        f"Интервал: "
        f"{spec.interval:.6f} с"
    )

    theoretical_intensity = (
        1.0 / spec.interval
        if spec.interval > 0
        else float("inf")
    )

    print(
        f"Теоретическая интенсивность: "
        f"{theoretical_intensity:.2f} пак./с"
    )

    if spec.config.service_rate is not None:
        print(
            f"Пропускная способность: "
            f"{spec.config.service_rate:.2f} пак./с"
        )

    if spec.config.queue_limit is not None:
        print(
            f"Размер очереди: "
            f"{spec.config.queue_limit} пак."
        )

    print(
        "=" * 60
    )

    LOGS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TABLES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    server_log = (
        LOGS_DIR
        / f"{experiment_number:03d}_"
          f"{spec.name}_server.csv"
    )

    emulator_log = (
        LOGS_DIR
        / f"{experiment_number:03d}_"
          f"{spec.name}_emulator.log"
    )

    server_result = (
        TABLES_DIR
        / f"{experiment_number:03d}_"
          f"{spec.name}_result.json"
    )

    server_process = None
    emulator_process = None

    try:
        server_process = start_server(
            packets=spec.packets,
            log_file=server_log,
            result_file=server_result,
        )

        time.sleep(0.3)

        emulator_process = start_emulator(
            config=spec.config,
            log_file=emulator_log,
        )

        time.sleep(0.3)

        _, elapsed_time = (
            start_client(
                packets=spec.packets,
                interval=spec.interval,
            )
        )

        # Даём каналу время передать
        # оставшиеся пакеты.
        flush_time = (
            spec.config.delay
            + spec.config.jitter
            + spec.config.reorder_delay
            + 1.0
        )

        if (
            spec.config.service_rate
            is not None
        ):
            service_time = (
                spec.packets
                / spec.config.service_rate
            )

            flush_time = max(
                flush_time,
                service_time + 1.0,
            )

        time.sleep(
            max(
                1.0,
                flush_time,
            )
        )

    finally:
        if emulator_process is not None:
            stop_process(
                emulator_process
            )

        if server_process is not None:
            wait_for_process(
                server_process,
                timeout=(
                    SERVER_TIMEOUT + 3
                ),
            )

    if not server_result.exists():
        raise RuntimeError(
            "Сервер не создал файл "
            f"результатов: {server_result}"
        )

    with server_result.open(
        "r",
        encoding="utf-8",
    ) as file:

        statistics = json.load(
            file
        )

    intensity = (
        spec.packets / elapsed_time
        if elapsed_time > 0
        else 0.0
    )

    result = ExperimentResult(
        name=spec.name,
        packets_sent=spec.packets,
        interval=spec.interval,
        intensity=intensity,
        elapsed_time=elapsed_time,
        statistics=statistics,
    )

    print(
        f"\nФактическая интенсивность: "
        f"{intensity:.2f} пак./с"
    )

    print(
        f"Потери: "
        f"{statistics['lost']} "
        f"({statistics['loss_ratio'] * 100:.2f} %)"
    )

    print(
        f"Дубликаты: "
        f"{statistics['duplicates']} "
        f"({statistics['duplicate_ratio'] * 100:.2f} %)"
    )

    print(
        f"Переупорядочивание: "
        f"{statistics['out_of_order']} "
        f"({statistics['out_of_order_ratio'] * 100:.2f} %)"
    )

    return result


def build_task1_specs(
    packets: int = 1000,
) -> list[ExperimentSpec]:

    intervals = [
        0.010,
        0.005,
        0.002,
        0.001,
        0.0005,
    ]

    specs = []

    for index, interval in enumerate(
        intervals,
        start=1,
    ):
        specs.append(
            ExperimentSpec(
                name=f"task1_{index}",
                packets=packets,
                interval=interval,
                config=EmulationConfig(
                    queue_limit=100,
                    service_rate=500.0,
                ),
            )
        )

    return specs


def build_task2_specs(
    packets: int = 1000,
) -> list[ExperimentSpec]:

    return [
        ExperimentSpec(
            name="task2_duplicate_5",
            packets=packets,
            interval=0.001,
            config=EmulationConfig(
                duplicate_rate=0.05,
            ),
        ),

        ExperimentSpec(
            name="task2_reorder_5",
            packets=packets,
            interval=0.001,
            config=EmulationConfig(
                reorder_rate=0.05,
                reorder_delay=0.020,
            ),
        ),

        ExperimentSpec(
            name="task2_duplicate_reorder",
            packets=packets,
            interval=0.001,
            config=EmulationConfig(
                duplicate_rate=0.05,
                reorder_rate=0.05,
                reorder_delay=0.020,
            ),
        ),
    ]


def build_task3_specs(
    packets: int = 1000,
) -> list[ExperimentSpec]:

    return [
        ExperimentSpec(
            name="task3_delay",
            packets=packets,
            interval=0.001,
            config=EmulationConfig(
                delay=0.010,
            ),
        ),

        ExperimentSpec(
            name="task3_delay_jitter",
            packets=packets,
            interval=0.001,
            config=EmulationConfig(
                delay=0.010,
                jitter=0.005,
            ),
        ),

        ExperimentSpec(
            name="task3_loss_delay_jitter",
            packets=packets,
            interval=0.001,
            config=EmulationConfig(
                loss_rate=0.05,
                delay=0.010,
                jitter=0.005,
            ),
        ),

        ExperimentSpec(
            name="task3_combined",
            packets=packets,
            interval=0.001,
            config=EmulationConfig(
                loss_rate=0.05,
                duplicate_rate=0.05,
                reorder_rate=0.05,
                delay=0.010,
                jitter=0.005,
                reorder_delay=0.020,
            ),
        ),
    ]


def run_task(
    task_name: str,
    specs: list[ExperimentSpec],
):
    results = []

    for number, spec in enumerate(
        specs,
        start=1,
    ):
        result = run_experiment(
            spec=spec,
            experiment_number=number,
        )

        results.append(result)

    task_json = (
        TABLES_DIR
        / f"{task_name}.json"
    )

    task_csv = (
        TABLES_DIR
        / f"{task_name}.csv"
    )

    save_results_json(
        results,
        str(task_json),
    )

    save_results_csv(
        results,
        str(task_csv),
    )

    return results


def print_summary(
    task_name: str,
    results: list[ExperimentResult],
):
    print(
        "\n"
        + "=" * 80
    )

    print(
        f"ИТОГИ {task_name.upper()}"
    )

    print(
        "=" * 80
    )

    print(
        f"{'Эксперимент':<30}"
        f"{'Интенсивность':>15}"
        f"{'Потери':>12}"
        f"{'Дубли':>12}"
        f"{'Порядок':>12}"
    )

    print("-" * 80)

    for result in results:
        stats = result.statistics

        print(
            f"{result.name:<30}"
            f"{result.intensity:>15.2f}"
            f"{stats['loss_ratio'] * 100:>11.2f}%"
            f"{stats['duplicate_ratio'] * 100:>11.2f}%"
            f"{stats['out_of_order_ratio'] * 100:>11.2f}%"
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Запуск экспериментов "
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

    parser.add_argument(
        "--packets",
        type=int,
        default=1000,
        help="Количество пакетов "
             "в одном эксперименте",
    )

    args = parser.parse_args()

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    LOGS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TABLES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if args.task in ("1", "all"):
        results = run_task(
            "task1",
            build_task1_specs(
                args.packets
            ),
        )

        print_summary(
            "task1",
            results,
        )

    if args.task in ("2", "all"):
        results = run_task(
            "task2",
            build_task2_specs(
                args.packets
            ),
        )

        print_summary(
            "task2",
            results,
        )

    if args.task in ("3", "all"):
        results = run_task(
            "task3",
            build_task3_specs(
                args.packets
            ),
        )

        print_summary(
            "task3",
            results,
        )


if __name__ == "__main__":
    main()