# models.py

from dataclasses import dataclass


@dataclass
class EmulationConfig:
    """
    Параметры эмуляции сетевого канала.
    """

    # Вероятностные нарушения
    loss_rate: float = 0.0
    duplicate_rate: float = 0.0
    reorder_rate: float = 0.0

    # Задержка и джиттер
    delay: float = 0.0
    jitter: float = 0.0
    reorder_delay: float = 0.02

    # Ограничения канала
    queue_limit: int | None = None
    service_rate: float | None = None

    def validate(self):
        rates = {
            "loss_rate": self.loss_rate,
            "duplicate_rate": self.duplicate_rate,
            "reorder_rate": self.reorder_rate,
        }

        for name, value in rates.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} должен быть от 0 до 1."
                )

        if self.delay < 0:
            raise ValueError(
                "delay не может быть отрицательным."
            )

        if self.jitter < 0:
            raise ValueError(
                "jitter не может быть отрицательным."
            )

        if self.reorder_delay < 0:
            raise ValueError(
                "reorder_delay не может быть отрицательным."
            )

        if self.queue_limit is not None:
            if self.queue_limit <= 0:
                raise ValueError(
                    "queue_limit должен быть больше 0."
                )

        if self.service_rate is not None:
            if self.service_rate <= 0:
                raise ValueError(
                    "service_rate должен быть больше 0."
                )


@dataclass
class ExperimentResult:
    name: str
    packets_sent: int
    interval: float
    intensity: float
    elapsed_time: float
    statistics: dict


@dataclass
class ExperimentSpec:
    name: str
    packets: int
    interval: float
    config: EmulationConfig