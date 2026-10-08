# statistics.py

from collections import Counter
from statistics import mean, pstdev


def calculate_statistics(
    received_packets: list[int],
    total_sent: int,
    delays: list[float] | None = None,
) -> dict:
    """
    Рассчитывает статистику доставки пакетов.
    """

    received_count = len(received_packets)

    packet_counts = Counter(received_packets)

    # Количество лишних копий пакетов.
    duplicate_count = sum(
        count - 1
        for count in packet_counts.values()
        if count > 1
    )

    # Определение потерянных пакетов
    expected_packets = set(
        range(total_sent)
    )

    received_unique = set(
        received_packets
    )

    lost_packets = (
        expected_packets - received_unique
    )

    lost_count = len(lost_packets)

    # Определение переупорядоченных пакетов
    out_of_order_packets = []

    seen_packets = set()
    highest_sequence = -1

    for sequence_number in received_packets:

        # Дубликат уже учитывается отдельно.
        if sequence_number in seen_packets:
            continue

        if sequence_number < highest_sequence:
            out_of_order_packets.append(
                sequence_number
            )

        highest_sequence = max(
            highest_sequence,
            sequence_number,
        )

        seen_packets.add(sequence_number)

    out_of_order_count = len(
        out_of_order_packets
    )

    # Коэффициенты
    if total_sent > 0:
        loss_ratio = (
            lost_count / total_sent
        )

        duplicate_ratio = (
            duplicate_count / total_sent
        )

        out_of_order_ratio = (
            out_of_order_count / total_sent
        )
    else:
        loss_ratio = 0.0
        duplicate_ratio = 0.0
        out_of_order_ratio = 0.0

    # Задержка и джиттер
    if delays:
        average_delay = mean(delays)
        min_delay = min(delays)
        max_delay = max(delays)

        jitter = (
            pstdev(delays)
            if len(delays) > 1
            else 0.0
        )

    else:
        average_delay = 0.0
        min_delay = 0.0
        max_delay = 0.0
        jitter = 0.0

    return {
        "sent": total_sent,
        "received": received_count,
        "unique_received": len(
            received_unique
        ),
        "lost": lost_count,
        "duplicates": duplicate_count,
        "out_of_order": out_of_order_count,

        "loss_ratio": loss_ratio,
        "duplicate_ratio": duplicate_ratio,
        "out_of_order_ratio": (
            out_of_order_ratio
        ),

        "average_delay": average_delay,
        "min_delay": min_delay,
        "max_delay": max_delay,
        "jitter": jitter,

        "lost_packets": sorted(
            lost_packets
        ),

        "out_of_order_packets": sorted(
            out_of_order_packets
        ),
    }


def print_statistics(results: dict):
    print(
        "\n===== Результаты эксперимента ====="
    )

    print(
        f"Отправлено:             "
        f"{results['sent']}"
    )

    print(
        f"Принято:                "
        f"{results['received']}"
    )

    print(
        f"Уникальных пакетов:     "
        f"{results['unique_received']}"
    )

    print(
        f"\nПотеряно:               "
        f"{results['lost']}"
    )

    print(
        f"Доля потерь:            "
        f"{results['loss_ratio'] * 100:.2f} %"
    )

    print(
        f"\nДубликатов:             "
        f"{results['duplicates']}"
    )

    print(
        f"Доля дубликатов:        "
        f"{results['duplicate_ratio'] * 100:.2f} %"
    )

    print(
        f"\nПереупорядочено:        "
        f"{results['out_of_order']}"
    )

    print(
        f"Доля переупорядочивания: "
        f"{results['out_of_order_ratio'] * 100:.2f} %"
    )

    print(
        f"\nСредняя задержка:       "
        f"{results['average_delay']:.3f} мс"
    )

    print(
        f"Минимальная задержка:   "
        f"{results['min_delay']:.3f} мс"
    )

    print(
        f"Максимальная задержка:  "
        f"{results['max_delay']:.3f} мс"
    )

    print(
        f"Джиттер:                "
        f"{results['jitter']:.3f} мс"
    )

    if results["lost_packets"]:
        print(
            "\nНомера потерянных пакетов:"
        )

        print(
            results["lost_packets"]
        )

    if results[
        "out_of_order_packets"
    ]:
        print(
            "\nНомера переупорядоченных "
            "пакетов:"
        )

        print(
            results[
                "out_of_order_packets"
            ]
        )