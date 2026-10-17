import sounddevice as sd


def get_audio_diagnostic_info() -> dict:
    """
    Сканирует систему и автоматически находит лучшие индексы для NVIDIA Broadcast
    и Samson по протоколу WASAPI, а также собирает текстовый отчет.
    """
    devices = sd.query_devices()
    api_info = sd.query_hostapis()

    # Ищем индекс WASAPI в системе
    wasapi_index = None
    for idx, api in enumerate(api_info):
        if "WASAPI" in api['name']:
            wasapi_index = idx
            break

    broadcast_idx = None
    samson_idx = None
    default_input_idx = sd.default.device[0]

    # Текстовый список для отчета ИИ
    input_devices_list = []
    output_devices_list = []

    for idx, dev in enumerate(devices):
        name = dev['name']
        max_in = dev['max_input_channels']
        max_out = dev['max_output_channels']
        host_api = dev['hostapi']

        # Фильтруем только WASAPI устройства для максимальной стабильности
        if wasapi_index is not None and host_api == wasapi_index:
            if max_in > 0:
                input_devices_list.append(f"ID {idx}: {name}")
                if "NVIDIA Broadcast" in name:
                    broadcast_idx = idx
                elif "Samson" in name and samson_idx is None:
                    samson_idx = idx
            if max_out > 0:
                output_devices_list.append(f"ID {idx}: {name}")

    # Страховочный выбор устройства для записи
    chosen_idx = default_input_idx
    status_msg = "Используется системное устройство по умолчанию."

    if broadcast_idx is not None:
        chosen_idx = broadcast_idx
        status_msg = "Обнаружен и успешно подключен премиальный поток NVIDIA Broadcast (WASAPI)."
    elif samson_idx is not None:
        chosen_idx = samson_idx
        status_msg = "NVIDIA Broadcast не найден. Автоматически активирован сырой WASAPI-драйвер Samson C01U Pro."
    else:
        if default_input_idx is not None:
            chosen_idx = default_input_idx
            status_msg = "Внимание, шеф: Broadcast и Samson не найдены. Подключен стандартный микрофон Windows."

    return {
        "chosen_input_id": chosen_idx,
        "status_message": status_msg,
        "available_inputs": input_devices_list,
        "available_outputs": output_devices_list
    }


def check_audio_devices() -> str:
    """Функция-инструмент для Агента Ollama. Возвращает текстовый отчет о железе."""
    info = get_audio_diagnostic_info()

    report = (
            f"Статус аудио-протоколов: {info['status_message']}\n\n"
            f"Доступные микрофоны (WASAPI):\n" + "\n".join(info['available_inputs']) + "\n\n"
                                                                                       f"Доступные динамики (WASAPI):\n" + "\n".join(
        info['available_outputs'])
    )
    return report
