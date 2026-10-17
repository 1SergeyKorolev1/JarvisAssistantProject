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
    """Умное дробление текста на законченные предложения для Silero TTS с поддержкой списков"""
    if not text:
        return []

    # 1. Очищаем от Markdown и системных маркеров документов
    text = re.sub(r'\[.*?\]', '', text)  # Удаляем картинки [IMAGE: ...]
    text = text.replace('#', '')  # Удаляем заголовки ##
    text = text.replace('*', '')  # Удаляем жирный/курсивный шрифт **
    text = text.replace('`', '')  # Удаляем маркеры кода

    # 2. Красиво преобразуем нумерованные списки (например, "1. " -> "Пункт первый. ")
    # Чтобы Silero не ломался об одиночные цифры с точками
    digits_map = {
        "1": "Пункт первый", "2": "Пункт второй", "3": "Пункт третий",
        "4": "Пункт четвертый", "5": "Пункт пятый", "6": "Пункт шестой",
        "7": "Пункт седьмой", "8": "Пункт восьмой", "9": "Пункт девятый"
    }

    def replace_digit_list(match):
        digit = match.group(1)
        return digits_map.get(digit, f"Пункт {digit}") + ". "

    # Ищем конструкции вида "1. ", "2. " в начале строк или после пробелов
    text = re.sub(r'(?:^|\n)\s*(\d+)\.\s+', replace_digit_list, text)

    # Заменяем обычные маркеры-дефисы списков на красивую вводную паузу
    text = re.sub(r'^\s*-\s+', 'Также: ', text, flags=re.MULTILINE)

    # 3. Регулярное выражение для деления на предложения
    # Игнорируем точки внутри сокращений и проверяем, чтобы после точки шла заглавная буква или пробел
    sentence_end = re.compile(r'(?<!\bт\.(?:и)\.)(?<!\bт\.(?:д)\.)(?<!\bисп\.)(?<=[.!?])\s+')
    raw_sentences = sentence_end.split(text)

    sentences = []
    for s in raw_sentences:
        if s is None:
            continue

        s_clean = s.strip()
        if not s_clean or len(s_clean) < 2:  # Игнорируем случайные одиночные символы
            continue

        # Заменяем дефисы на длинные тире для лучшей интонации
        s_clean = re.sub(r'\s+', ' ', s_clean)

        # Если предложение длинное, аккуратно бьем по запятым
        if len(s_clean) > 250:
            parts = re.split(r'(?<=,)\s+', s_clean)
            sentences.extend([p.strip() for p in parts if p and len(p.strip()) > 1])
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





