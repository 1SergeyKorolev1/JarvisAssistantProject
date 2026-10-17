import os
import warnings
import time
import re
import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
# ИМПОРТ: Подключаем наш умный сканер железа
from tools.audio_hardware import get_audio_diagnostic_info

# =====================================================================
# НАСТРОЙКИ ПРОФЕССИОНАЛЬНОГО ПОТОКОВОГО СТЕКА WHISPER MEDIUM (CUDA)
# =====================================================================
WAKE_WORD = "нова"  # Голосовой триггер для активации
WHISPER_MODEL_SIZE = "medium"  # Ваша скачанная и готовая модель medium
SAMPLE_RATE_INPUT = 48000  # Родная частота микрофонов Samson/Broadcast
SAMPLE_RATE_WHISPER = 16000  # Нативная частота для Whisper
SILENCE_TIMEOUT = 1.5  # Сколько секунд тишины ждать после окончания фразы
SILENCE_THRESHOLD = 165  # Безопасный порог отсечки фонового гула Samson + APO
# =====================================================================

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "true"
warnings.filterwarnings("ignore", category=UserWarning)

audio_queue = queue.Queue()
whisper_model = None


def callback(indata, frames, time_info, status):
    """Фоновый сбор аудио-данных из микрофона в очередь"""
    audio_queue.put(bytes(indata))


def init_whisper():
    """Инициализация Whisper строго в памяти видеокарты RTX 4070 CUDA"""
    global whisper_model
    if whisper_model is None:
        print(
            f"🔄 [Система ввода]: Загрузка нейросети Whisper ({WHISPER_MODEL_SIZE.capitalize()}) из локального кэша в VRAM...")
        whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cuda", compute_type="float16")
        print("🎙️ [Система ввода]: Высокоточные слуховые протоколы активированы.")


def wait_for_wake_word() -> str:
    """
    Слушает эфир в едином непрерывном потоковом режиме.
    Автоматически определяет индекс микрофона через динамический сканер портов.
    """
    init_whisper()

    # ДИНАМИЧЕСКИЙ ПЕРЕХВАТ ПОРТА: Спрашиваем у сканера, где сейчас Broadcast или Samson
    hardware_info = get_audio_diagnostic_info()
    active_device_id = hardware_info["chosen_input_id"]

    # Очистка буферов перед стартом
    while not audio_queue.empty():
        audio_queue.get()

    print(f"\n📡 [Слух]: {hardware_info['status_message']}")
    print(
        f"💤 [Нова]: Режим ожидания (ID устройства: {active_device_id}). Произнесите '{WAKE_WORD.capitalize()}' и ваш запрос...")

    wake_regex = re.compile(r'\bнов[аеуыоия]\b|\bновой\b', re.IGNORECASE)

    command_audio_buffer = []
    speech_started = False
    last_speech_time = time.time()

    # Передаем active_device_id напрямую в поток sounddevice
    with sd.RawInputStream(samplerate=SAMPLE_RATE_INPUT, blocksize=12000,
                           dtype='int16', channels=1, callback=callback, device=active_device_id):

        while True:
            current_time = time.time()

            try:
                data = audio_queue.get_nowait()
                audio_data = np.frombuffer(data, dtype=np.int16)

                if len(audio_data) > 0:
                    audio_float = audio_data.astype(np.float64)
                    rms = np.sqrt(np.mean(audio_float ** 2))
                    if np.isnan(rms): rms = 0.0
                else:
                    rms = 0.0

                is_sound_present = rms > SILENCE_THRESHOLD

                if is_sound_present:
                    if not speech_started:
                        speech_started = True
                        print("🎙️ [Слух]: Запись вашей команды...")
                    last_speech_time = current_time

                if speech_started:
                    command_audio_buffer.append(audio_data)

            except queue.Empty:
                is_sound_present = False
                time.sleep(0.01)

            if speech_started and (current_time - last_speech_time > SILENCE_TIMEOUT):
                print("🛑 [Запись]: Фраза завершена. Распознавание на CUDA...")
                break

    if not command_audio_buffer:
        return ""

    full_audio_int16 = np.concatenate(command_audio_buffer)
    downsampled_audio = full_audio_int16[::3]
    audio_array = downsampled_audio.astype(np.float32) / 32768.0

    segments, info = whisper_model.transcribe(audio_array, language="ru", beam_size=3, vad_filter=True)
    full_text = "".join([segment.text for segment in segments]).strip()

    if full_text:
        print(f"📡 [В эфире поймано]: '{full_text}'")

        match = wake_regex.search(full_text)
        if match:
            print(f"✨ [Система ввода]: Высокоточный перехват команды!")
            matched_word = match.group(0)
            command = full_text.split(matched_word, 1)[-1].strip()
            command = command.lstrip('-,.!? ').rstrip('-,.!? ')

            if command:
                return command
            else:
                print("🎤 [Нова]: Да, сэр? Я слушаю вас...")

    return ""













