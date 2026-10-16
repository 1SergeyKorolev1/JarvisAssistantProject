import datetime
import os


def shutdown_computer(minutes: int = 1) -> str:
    """
    Выключает компьютер или завершает работу Windows через заданное количество минут.

    :param minutes: Количество минут, через которое нужно выключить ПК.
    """
    seconds = minutes * 60
    os.system(f"shutdown /s /t {seconds}")
    return f"Запущено выключение системы. Компьютер завершит работу через {minutes} мин, сэр."


def get_current_time() -> str:
    """
    Узнать точное текущее время на компьютере.
    """
    now = datetime.datetime.now().strftime("%H:%M")
    return f"Сейчас ровно {now}, сэр."
