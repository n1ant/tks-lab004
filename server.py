# server.py

import argparse
import csv
import json
import socket
import time
from pathlib import Path

from packet import parse_packet
from packet_statistics import calculate_statistics
from packet_statistics import print_statistics


def run_server(
    host: str,
    port: int,
    total_packets: int,
    timeout: float,
    log_file: str | None = None,
    result_file: str | None = None,
):
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    server_socket.bind(
        (host, port)
    )

    server_socket.settimeout(
        timeout
    )

    print(
        f"Сервер запущен на "
        f"{host}:{port}"
    )

    received_packets = []
    delays = []

    log_handle = None
    log_writer = None

    if log_file is not None:
        log_path = Path(log_file)

        log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        log_handle = log_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        )

        log_writer = csv.writer(
            log_handle,
            delimiter=";",
        )

        log_writer.writerow(
            [
                "receive_time",
                "sequence_number",
                "send_timestamp",
                "delay_ms",
            ]
        )

    try:
        while True:
            try:
                data, _ = (
                    server_socket.recvfrom(
                        4096
                    )
                )

            except socket.timeout:
                break

            receive_time = time.time()

            try:
                (
                    sequence_number,
                    timestamp,
                ) = parse_packet(data)

            except ValueError:
                continue

            delay_ms = (
                receive_time - timestamp
            ) * 1000

            received_packets.append(
                sequence_number
            )

            delays.append(
                delay_ms
            )

            if log_writer is not None:
                log_writer.writerow(
                    [
                        f"{receive_time:.6f}",
                        sequence_number,
                        f"{timestamp:.6f}",
                        f"{delay_ms:.3f}",
                    ]
                )

    finally:
        if log_handle is not None:
            log_handle.close()

        server_socket.close()

    results = calculate_statistics(
        received_packets=received_packets,
        total_sent=total_packets,
        delays=delays,
    )

    if result_file is not None:
        result_path = Path(
            result_file
        )

        result_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with result_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                results,
                file,
                ensure_ascii=False,
                indent=4,
            )

    print_statistics(results)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "UDP-сервер для лабораторной "
            "работы №4"
        )
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="IP-адрес сервера",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="UDP-порт сервера",
    )

    parser.add_argument(
        "--packets",
        type=int,
        default=1000,
        help="Ожидаемое количество "
             "исходных пакетов",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Время ожидания новых пакетов",
    )

    parser.add_argument(
        "--log",
        default=None,
        help="CSV-файл журнала",
    )

    parser.add_argument(
        "--result",
        default=None,
        help="JSON-файл с результатами",
    )

    args = parser.parse_args()

    run_server(
        host=args.host,
        port=args.port,
        total_packets=args.packets,
        timeout=args.timeout,
        log_file=args.log,
        result_file=args.result,
    )