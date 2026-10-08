# network_emulator.py

import argparse
import heapq
import random
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from models import EmulationConfig
from packet import parse_packet


@dataclass(order=True)
class ScheduledPacket:
    send_time: float
    order: int
    data: bytes


class NetworkEmulator:
    def __init__(
        self,
        listen_host: str,
        listen_port: int,
        target_host: str,
        target_port: int,
        config: EmulationConfig,
        log_file: str | None = None,
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port

        self.target_host = target_host
        self.target_port = target_port

        self.config = config
        self.config.validate()

        self.log_file = log_file

        self.running = False

        self.input_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        self.input_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        self.input_socket.bind(
            (
                self.listen_host,
                self.listen_port,
            )
        )

        self.input_socket.settimeout(
            0.2
        )

        self.output_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        self.queue = []

        self.queue_condition = (
            threading.Condition()
        )

        self.order_counter = 0

        self.queue_drop_count = 0
        self.forward_count = 0

    def log_event(
        self,
        event: str,
        sequence_number: int | None = None,
    ):
        if self.log_file is None:
            return

        path = Path(
            self.log_file
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = time.time()

        with path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                f"{timestamp:.6f};"
                f"{event};"
                f"{'' if sequence_number is None else sequence_number}\n"
            )

    def calculate_delay(
        self,
        reordered: bool = False,
    ) -> float:
        delay = self.config.delay

        if self.config.jitter > 0:
            delay += random.uniform(
                -self.config.jitter,
                self.config.jitter,
            )

        if reordered:
            delay += (
                self.config.reorder_delay
            )

        return max(
            0.0,
            delay,
        )

    def schedule_packet(
        self,
        data: bytes,
        delay: float,
    ) -> bool:

        with self.queue_condition:

            if (
                self.config.queue_limit
                is not None
                and len(self.queue)
                >= self.config.queue_limit
            ):
                self.queue_drop_count += 1
                return False

            send_time = (
                time.monotonic()
                + delay
            )

            self.order_counter += 1

            heapq.heappush(
                self.queue,
                ScheduledPacket(
                    send_time=send_time,
                    order=self.order_counter,
                    data=data,
                ),
            )

            self.queue_condition.notify()

        return True

    def process_packet(
        self,
        data: bytes,
    ):
        try:
            (
                sequence_number,
                _,
            ) = parse_packet(data)

        except ValueError:
            sequence_number = None

        # Потеря пакета
        if (
            random.random()
            < self.config.loss_rate
        ):
            self.log_event(
                "lost",
                sequence_number,
            )
            return

        # Переупорядочивание
        reordered = (
            random.random()
            < self.config.reorder_rate
        )

        delay = self.calculate_delay(
            reordered=reordered
        )

        if reordered:
            self.log_event(
                "reorder",
                sequence_number,
            )

        scheduled = (
            self.schedule_packet(
                data,
                delay,
            )
        )

        if scheduled:
            self.log_event(
                "forward",
                sequence_number,
            )
        else:
            self.log_event(
                "queue_drop",
                sequence_number,
            )

        # Дублирование
        if (
            random.random()
            < self.config.duplicate_rate
        ):
            duplicate_delay = (
                self.calculate_delay()
            )

            scheduled = (
                self.schedule_packet(
                    data,
                    duplicate_delay,
                )
            )

            if scheduled:
                self.log_event(
                    "duplicate",
                    sequence_number,
                )
            else:
                self.log_event(
                    "queue_drop_duplicate",
                    sequence_number,
                )

    def receiver_loop(self):
        while self.running:

            try:
                data, _ = (
                    self.input_socket.recvfrom(
                        4096
                    )
                )

            except socket.timeout:
                continue

            except OSError:
                if self.running:
                    raise
                break

            self.process_packet(data)

    def sender_loop(self):
        next_send_time = (
            time.monotonic()
        )

        while self.running:

            with self.queue_condition:

                while (
                    self.running
                    and not self.queue
                ):
                    self.queue_condition.wait(
                        timeout=0.1
                    )

                if not self.running:
                    break

                packet = self.queue[0]

                now = time.monotonic()

                wait_time = max(
                    0.0,
                    packet.send_time - now,
                    next_send_time - now,
                )

                if wait_time > 0:
                    self.queue_condition.wait(
                        timeout=wait_time
                    )
                    continue

                heapq.heappop(
                    self.queue
                )

            try:
                self.output_socket.sendto(
                    packet.data,
                    (
                        self.target_host,
                        self.target_port,
                    ),
                )

                self.forward_count += 1

            except OSError:
                if self.running:
                    raise

            if (
                self.config.service_rate
                is not None
            ):
                service_interval = (
                    1.0
                    / self.config.service_rate
                )

                next_send_time = max(
                    next_send_time,
                    time.monotonic(),
                ) + service_interval

    def run(self):
        self.running = True

        receiver_thread = threading.Thread(
            target=self.receiver_loop,
            daemon=True,
        )

        sender_thread = threading.Thread(
            target=self.sender_loop,
            daemon=True,
        )

        receiver_thread.start()
        sender_thread.start()

        print(
            f"Эмулятор запущен: "
            f"{self.listen_host}:"
            f"{self.listen_port} -> "
            f"{self.target_host}:"
            f"{self.target_port}"
        )

        try:
            while self.running:
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass

        finally:
            self.stop()

            receiver_thread.join(
                timeout=1.0
            )

            sender_thread.join(
                timeout=1.0
            )

    def stop(self):
        self.running = False

        with self.queue_condition:
            self.queue_condition.notify_all()

        try:
            self.input_socket.close()
        except OSError:
            pass

        try:
            self.output_socket.close()
        except OSError:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Эмулятор сетевого канала "
            "для лабораторной работы №4"
        )
    )

    parser.add_argument(
        "--listen-host",
        default="127.0.0.1",
    )

    parser.add_argument(
        "--listen-port",
        type=int,
        default=5001,
    )

    parser.add_argument(
        "--target-host",
        default="127.0.0.1",
    )

    parser.add_argument(
        "--target-port",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--loss",
        type=float,
        default=0.0,
        help="Вероятность потери",
    )

    parser.add_argument(
        "--duplicate",
        type=float,
        default=0.0,
        help="Вероятность дублирования",
    )

    parser.add_argument(
        "--reorder",
        type=float,
        default=0.0,
        help="Вероятность переупорядочивания",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Базовая задержка в секундах",
    )

    parser.add_argument(
        "--jitter",
        type=float,
        default=0.0,
        help="Максимальный джиттер в секундах",
    )

    parser.add_argument(
        "--reorder-delay",
        type=float,
        default=0.02,
        help=(
            "Дополнительная задержка "
            "для переупорядочиваемых пакетов"
        ),
    )

    parser.add_argument(
        "--queue-limit",
        type=int,
        default=None,
        help="Максимальный размер очереди",
    )

    parser.add_argument(
        "--service-rate",
        type=float,
        default=None,
        help=(
            "Максимальная скорость "
            "передачи пакетов, пак./с"
        ),
    )

    parser.add_argument(
        "--log",
        default=None,
        help="Файл журнала эмулятора",
    )

    args = parser.parse_args()

    config = EmulationConfig(
        loss_rate=args.loss,
        duplicate_rate=args.duplicate,
        reorder_rate=args.reorder,
        delay=args.delay,
        jitter=args.jitter,
        reorder_delay=args.reorder_delay,
        queue_limit=args.queue_limit,
        service_rate=args.service_rate,
    )

    emulator = NetworkEmulator(
        listen_host=args.listen_host,
        listen_port=args.listen_port,
        target_host=args.target_host,
        target_port=args.target_port,
        config=config,
        log_file=args.log,
    )

    emulator.run()