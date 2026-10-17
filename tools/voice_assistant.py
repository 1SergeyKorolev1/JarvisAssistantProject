import os
import torch
import sounddevice as sd
import re

# Настраиваем вашу мощную RTX 4070 (CUDA)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = None


def init_tts():
    """Инициализация модели строго из корня диска C, где нет кириллицы"""
    global model
    if model is None:
        print("🔊 [Система звука]: Загрузка локального голоса Новы (Версия V5)...")

        # Указываем ваш новый точный путь, где лежит скачанный руками файл
        safe_path = "C:/voiceModel/v5_ru.pt"

        # Проверяем, лежит ли файл на месте
        if not os.path.exists(safe_path):
            raise FileNotFoundError(
                f"Сэр, файл 'v5_ru.pt' не найден по пути {safe_path}! "
                f"Пожалуйста, убедитесь, что вы создали папку C:\\voiceModel\\ и положили файл туда."
            )

        print("🔄 [Система звука]: Загрузка модели в память видеокарты RTX 4070...")
        # Загружаем локальный файл пакета
        model = torch.package.PackageImporter(safe_path).load_pickle("tts_models", "model")
        model.to(device)
        print("🔊 [Система звука]: Нова успешно подключена к голосовым протоколам.")


def split_text_into_sentences(text: str) -> list:
    """Умное дробление текста на законченные предложения для Silero TTS"""
    # 1. Очищаем от Markdown и системных маркеров документов
    text = re.sub(r'\[.*?\]', '', text)  # Удаляем картинки [IMAGE: ...]
    text = text.replace('#', '')  # Удаляем заголовки ##
    text = text.replace('*', '')  # Удаляем жирный/курсивный шрифт **
    text = text.replace('`', '')  # Удаляем маркеры кода
    text = re.sub(r'^-\s+', '', text, flags=re.MULTILINE)  # Удаляем дефисы списков

    # ИСПРАВЛЕНО: Добавлены ?: внутри скобок, чтобы регулярка не возвращала None в split
    sentence_end = re.compile(r'(?<!\bт\.(?:и)\.)(?<!\bт\.(?:д)\.)(?<!\bисп\.)(?<=[.!?])\s+')
    raw_sentences = sentence_end.split(text)

    sentences = []
    for s in raw_sentences:
        # Проверяем, что s не является None и является строкой
        if s is None:
            continue

        s_clean = s.strip()
        if not s_clean:
            continue

        # Заменяем дефисы на длинные тире для лучшей интонации и убираем лишние пробелы
        s_clean = re.sub(r'\s+', ' ', s_clean)

        # Если предложение получилось аномально длинным (редко, но бывает), бьем его по запятым
        if len(s_clean) > 250:
            parts = re.split(r'(?<=,)\s+', s_clean)
            sentences.extend([p.strip() for p in parts if p and p.strip()])
        else:
            sentences.append(s_clean)

    return sentences

def j_say(text: str):
    """Озвучивает текст приятным женским голосом 'baya', разбивая его на чанки"""
    try:
        init_tts()

        # Разбиваем монолог Новы на аккуратные порции
        sentences = split_text_into_sentences(text)

        if not sentences:
            return

        sample_rate = 48000
        speaker = 'baya'  # Приятный женский голос ИИ

        # Последовательно проговариваем каждое предложение
        for sentence in sentences:
            # Дополнительная проверка на пустую строку перед отправкой в модель
            if not sentence.strip():
                continue

            # Генерируем аудио для текущего предложения (на RTX 4070 это займет миллисекунды)
            audio = model.apply_tts(text=sentence,
                                    speaker=speaker,
                                    sample_rate=sample_rate)

            # Воспроизводим через динамики Windows
            sd.play(audio, sample_rate)
            sd.wait()  # Ждем завершения текущего предложения перед переходом к следующему

    except Exception as e:
        print(f"⚠️ [Ошибка звука]: Не удалось озвучить текст. Ошибка: {e}")





