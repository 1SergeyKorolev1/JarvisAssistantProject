import os
import torch
import sounddevice as sd
import re
import warnings
from num2words import num2words
# Импортируем наши изолированные инструменты нормализации
from tools.text_normalizer import translate_english_terms, convert_numbers_to_words, fallback_transliterate

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = None


def init_tts():
    """Инициализация модели голоса Новы Silero v5 в VRAM видеокарты"""
    global model
    if model is None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)

            print("🔊 [Система звука]: Загрузка локального голоса Новы (Версия V5)...")
            safe_path = "C:/voiceModel/v5_ru.pt"

            if not os.path.exists(safe_path):
                raise FileNotFoundError(f"Сэр, файл 'v5_ru.pt' не найден по пути {safe_path}!")

            print("🔄 [Система звука]: Загрузка модели в память видеокарты RTX 4070...")
            model = torch.package.PackageImporter(safe_path).load_pickle("tts_models", "model")
            model.to(device)
            print("🔊 [Система звука]: Нова успешно подключена к голосовым протоколам.")


def split_text_into_sentences(text: str) -> list:
    """Полная подготовка и умное дробление текста на понятные для Silero чанки"""
    if not text:
        return []

    # Очищаем разметку Markdown
    text = text.replace('```', '')
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('#', '')
    text = text.replace('*', '')
    text = text.replace('`', '')

    # Преобразуем нумерованные списки ИИ ("1. " -> "Номер один. ")
    def list_replacer(match):
        num = int(match.group(1))
        try:
            num_str = num2words(num, lang='ru')
            return f"Номер {num_str}. "
        except:
            return "Пункт. "

    text = re.sub(r'(?:^|\n)\s*(\d+)\.\s+', list_replacer, text)
    text = re.sub(r'^\s*-\s+', 'Также: ', text, flags=re.MULTILINE)

    # Лингвистический перевод терминов и чисел через выделенный модуль
    text = translate_english_terms(text)
    text = convert_numbers_to_words(text)

    # Нарезаем монолог на предложения
    sentence_end = re.compile(r'(?<!\bт\.(?:и)\.)(?<!\bт\.(?:д)\.)(?<!\bисп\.)(?<=[.!?])\s+')
    raw_sentences = sentence_end.split(text)

    sentences = []
    for s in raw_sentences:
        if s is None:
            continue

        s_clean = s.strip()
        if not s_clean or len(s_clean) < 2:
            continue

        s_clean = re.sub(r'\s+', ' ', s_clean)

        # Если в предложении осталась необработанная латиница (например, стих), побуквенно транслитерируем её
        if re.search(r'[a-zA-Z]', s_clean):
            s_clean = fallback_transliterate(s_clean)

        if len(s_clean) > 250:
            parts = re.split(r'(?<=,)\s+', s_clean)
            sentences.extend([p.strip() for p in parts if p and len(p.strip()) > 1])
        else:
            sentences.append(s_clean)

    return sentences


def j_say(text: str):
    """Озвучивает текст, отправляя в Silero v5 исключительно чистую кириллицу"""
    try:
        init_tts()
        sentences = split_text_into_sentences(text)

        if not sentences:
            return

        sample_rate = 48000
        speaker = 'baya'

        for sentence in sentences:
            if not sentence.strip():
                continue

            # Финальная фильтрация: оставляем только кириллицу и знаки препинания
            sentence_sanitized = re.sub(r'[^а-яА-ЯёЁ\s.,!?-]', '', sentence).strip()
            if not sentence_sanitized or len(sentence_sanitized) < 2:
                continue

            audio = model.apply_tts(text=sentence_sanitized, speaker=speaker, sample_rate=sample_rate)
            sd.play(audio, sample_rate)
            sd.wait()

    except Exception as e:
        print(f"⚠️ [Ошибка звука]: Не удалось озвучить текст. Ошибка: {e}")
