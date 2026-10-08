# client.py

import argparse
import socket
import time

from packet import create_packet


def run_client(
    server_host: str,
    server_port: int,
    packets: int,
    interval: float,
):
    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    server_address = (
        server_host,
        server_port,
    )

    print(
        f"Отправка {packets} пакетов "
        f"на {server_host}:{server_port}"
    )

    start_time = time.time()

    for sequence_number in range(packets):
        packet = create_packet(sequence_number)

        client_socket.sendto(
            packet,
            server_address,
        )

        if interval > 0:
            time.sleep(interval)

    elapsed_time = time.time() - start_time

    client_socket.close()

    print("\n===== Отправка завершена =====")
    print(f"Пакетов отправлено: {packets}")
    print(f"Время передачи:     {elapsed_time:.3f} с")

    if elapsed_time > 0:
        packets_per_second = packets / elapsed_time

        print(
            f"Интенсивность:      "
            f"{packets_per_second:.2f} пак./с"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "UDP-клиент для лабораторной "
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
        help="Количество отправляемых пакетов",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=0.001,
        help="Интервал между пакетами в секундах",
    )

    args = parser.parse_args()

    run_client(
        args.host,
        args.port,
        args.packets,
        args.interval,
    )