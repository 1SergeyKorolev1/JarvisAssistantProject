import os
import warnings
import time
import re
import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# =====================================================================
# НАСТРОЙКИ ПРОФЕССИОНАЛЬНОГО ПОТОКОВОГО СТЕКА WHISPER MEDIUM (CUDA)
# =====================================================================
WAKE_WORD = "нова"  # Голосовой триггер для активации
WHISPER_MODEL_SIZE = "medium"  # Ваша скачанная и готовая модель medium
SAMPLE_RATE_INPUT = 48000  # Родная частота вашего микрофона Samson
SAMPLE_RATE_WHISPER = 16000  # Нативная частота для Whisper
SILENCE_TIMEOUT = 1.5  # Сколько секунд тишины ждать после окончания фразы
SILENCE_THRESHOLD = 165  # Безопасный порог отсечки фонового гула Samson + APO
# =====================================================================

# Полностью глушим спам предупреждений Hugging Face в консоли
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
        # float16 активирует тензорные ядра вашей видеокарты для мгновенного инференса
        whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cuda", compute_type="float16")
        print("🎙️ [Система ввода]: Высокоточные слуховые протоколы активированы.")


def wait_for_wake_word() -> str:
    """
    Слушает эфир на частоте 48 кГц в едином непрерывном потоке.
    Нативно определяет конец фразы по тишине и транскрибирует буфер через Whisper Medium.
    """
    init_whisper()

    # Полная очистка очереди перед стартом
    while not audio_queue.empty():
        audio_queue.get()

    print(f"\n💤 [Нова]: Режим ожидания. Произнесите '{WAKE_WORD.capitalize()}' и ваш запрос...")

    # Регулярное выражение ловит "нова", "нову", "новы", а также системные опечатки вроде "ново"
    wake_regex = re.compile(r'\bнов[аеуыоия]\b|\bновой\b', re.IGNORECASE)

    command_audio_buffer = []
    speech_started = False
    last_speech_time = time.time()

    # Открываем единый поток на родной частоте 48000 Гц. Blocksize 12000 = порции по 0.25 сек.
    with sd.RawInputStream(samplerate=SAMPLE_RATE_INPUT, blocksize=12000,
                           dtype='int16', channels=1, callback=callback):

        while True:
            current_time = time.time()

            try:
                # Забираем чанк звука из очереди без блокировок
                data = audio_queue.get_nowait()
                audio_data = np.frombuffer(data, dtype=np.int16)

                # Считаем RMS для определения тишины
                if len(audio_data) > 0:
                    audio_float = audio_data.astype(np.float64)
                    rms = np.sqrt(np.mean(audio_float ** 2))
                    if np.isnan(rms): rms = 0.0
                else:
                    rms = 0.0

                # Если звук превысил порог 165 — это реальный голос сэра
                is_sound_present = rms > SILENCE_THRESHOLD

                if is_sound_present:
                    if not speech_started:
                        speech_started = True
                        print("🎙️ [Слух]: Запись вашей команды...")
                    last_speech_time = current_time

                # Если вы говорите, сохраняем данные в буфер
                if speech_started:
                    command_audio_buffer.append(audio_data)

            except queue.Empty:
                is_sound_present = False
                time.sleep(0.01)

            # Логика отсечки конца фразы по таймеру тишины
            if speech_started and (current_time - last_speech_time > SILENCE_TIMEOUT):
                print("🛑 [Запись]: Фраза завершена. Распознавание на CUDA...")

                # Объединяем все накопленные int16 чанки в один монолитный массив
                full_audio_int16 = np.concatenate(command_audio_buffer)

                # Математический ресэмплинг на лету: берем каждый 3-й элемент (48кГц -> 16кГц)
                downsampled_audio = full_audio_int16[::3]

                # Нормализуем в float32 для Whisper
                audio_array = downsampled_audio.astype(np.float32) / 32768.0

                # Мгновенный инференс Whisper Medium на вашей RTX 4070 с фильтром активности голоса
                segments, info = whisper_model.transcribe(
                    audio_array,
                    language="ru",
                    beam_size=3,
                    vad_filter=True
                )
                full_text = "".join([segment.text for segment in segments]).strip()

                if full_text:
                    print(f"📡 [В эфире поймано]: '{full_text}'")

                    # Ищем совпадение по регулярному выражению триггера
                    match = wake_regex.search(full_text)
                    if match:
                        print(f"✨ [Система ввода]: Высокоточный перехват команды!")
                        matched_word = match.group(0)

                        # Вырезаем команду, идущую строго после имени ассистента
                        command = full_text.split(matched_word, 1)[-1].strip()
                        command = command.lstrip('-,.!? ').rstrip('-,.!? ')

                        if command:
                            return command
                        else:
                            print("🎤 [Нова]: Да, сэр? Я слушаю вас...")

                # Сброс буферов для следующей фразы
                speech_started = False
                command_audio_buffer.clear()
                print(f"\n💤 [Нова]: Режим ожидания. Произнесите '{WAKE_WORD.capitalize()}'...")












