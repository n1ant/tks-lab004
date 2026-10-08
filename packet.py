# packet.py

import struct
import time


PACKET_FORMAT = "!Id"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)


def create_packet(sequence_number: int) -> bytes:
    """
    Создаёт UDP-пакет с номером последовательности
    и временной меткой отправки.
    """
    timestamp = time.time()
    return struct.pack(
        PACKET_FORMAT,
        sequence_number,
        timestamp,
    )


def parse_packet(data: bytes) -> tuple[int, float]:
    """
    Разбирает пакет и возвращает:
    (номер последовательности, временная метка).
    """
    if len(data) != PACKET_SIZE:
        raise ValueError(
            f"Некорректный размер пакета: "
            f"{len(data)} байт, ожидалось {PACKET_SIZE}"
        )

    sequence_number, timestamp = struct.unpack(
        PACKET_FORMAT,
        data,
    )

    return sequence_number, timestamp


def calculate_rtt(timestamp: float) -> float:
    """
    Рассчитывает задержку доставки пакета в миллисекундах.
    """
    return (time.time() - timestamp) * 1000