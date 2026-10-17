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


def get_current_time():
    """Возвращает точную текущую дату, год и время на компьютере"""
    now = datetime.datetime.now()
    ru_months = ["января", "февраля", "марта", "апреля", "мая", "июня",
                 "июля", "августа", "сентября", "октября", "ноября", "декабря"]

    return (
        f"Текущая дата на ПК: {now.day} {ru_months[now.month - 1]} {now.year} года. "
        f"Точное время: {now.strftime('%H:%M:%S')}."
    )
