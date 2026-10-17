import re
from num2words import num2words


def translate_english_terms(text: str) -> str:
    """Переводит английские IT-термины, бренды и единицы в русскую фонетическую транскрипцию"""
    translations = {
        r'\bid\b': 'айди',
        r'\bpc\b': 'пи си',
        r'\busd\b': 'долларов',
        r'\beur\b': 'евро',
        r'\bapi\b': 'апиай',
        r'\bcpu\b': 'сипию',
        r'\bgpu\b': 'джипию',
        r'\bhdmi\b': 'эйчдиэмай',
        r'\bspdif\b': 'эспэдиф',
        r'\bwasapi\b': 'васапи',
        r'\bmme\b': 'эмэми',
        r'\bspeakers\b': 'спикерс',
        r'\bdocx\b': 'докс',
        r'\bmain\b': 'мейн',
        r'\bpython\b': 'пайтон',
        r'\bllm\b': 'элэлэм',
        r'\bvad\b': 'вэд',
        r'\bcuda\b': 'куда',
        r'\brtx\b': 'эр тэ икс',
        r'\bwhisper\b': 'виспер',
        r'\bollama\b': 'оллама',
        r'\bqwen\b': 'квен',
        r'\bnvidia\b': 'энвидеа',
        r'\bbroadcast\b': 'бродкаст',
        r'\bsamson\b': 'самсон'
    }

    for eng_pattern, ru_word in translations.items():
        text = re.sub(eng_pattern, ru_word, text, flags=re.IGNORECASE)
    return text


def fallback_transliterate(text: str) -> str:
    """Позвуковой перевод оставшихся латинских символов (Spelling), если они отсутствуют в словаре"""
    alphabet_map = {
        'a': 'а', 'b': 'б', 'c': 'ц', 'd': 'д', 'e': 'э', 'f': 'ф', 'g': 'ж',
        'h': 'ш', 'i': 'ай', 'j': 'ж', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н',
        'o': 'о', 'p': 'п', 'q': 'к', 'r': 'рэ', 't': 'тэ', 'u': 'у', 'v': 'в',
        'w': 'в', 'x': 'кс', 'y': 'ю', 'z': 'зз'
    }
    result = []
    for char in text.lower():
        if char in alphabet_map:
            result.append(alphabet_map[char])
        else:
            result.append(char)
    return "".join(result)


def convert_numbers_to_words(text: str) -> str:
    """Интеллектуальный перевод любых цифр, времени и дат в русские слова с правильными падежами"""
    months_genitive = ["января", "февраля", "марта", "апреля", "мая", "июня",
                       "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    months_pattern = "|".join(months_genitive)

    # 1. Обработка дат формата "17 октября"
    def date_replacer(match):
        day_num = int(match.group(1))
        month_name = match.group(2)
        try:
            day_words = num2words(day_num, lang='ru', to='ordinal')
            if day_words.endswith("ый"):
                day_words = day_words[:-2] + "ое"
            elif day_words.endswith("ий"):
                day_words = day_words[:-2] + "ее"
            return f"{day_words} {month_name}"
        except:
            return match.group(0)

    text = re.sub(r'\b(\d{1,2})\s+(' + months_pattern + r')\b', date_replacer, text, flags=re.IGNORECASE)

    # 2. Обработка годов формата "2026 года"
    def year_replacer(match):
        year_num = int(match.group(1))
        suffix = match.group(2)
        try:
            year_words = num2words(year_num, lang='ru', to='ordinal')
            if year_words.endswith("ый"):
                year_words = year_words[:-2] + "ого"
            return f"{year_words} {suffix}"
        except:
            return match.group(0)

    text = re.sub(r'\b(\d{4})\s+(года|году)\b', year_replacer, text, flags=re.IGNORECASE)

    # 3. Переводим время формата ЧЧ:ММ (например, 23:14)
    def time_replacer(match):
        hours = int(match.group(1))
        minutes = int(match.group(2))
        hours_words = num2words(hours, lang='ru')
        if minutes == 0:
            minutes_words = "ровно"
        elif minutes < 10:
            minutes_words = "ноль " + num2words(minutes, lang='ru')
        else:
            minutes_words = num2words(minutes, lang='ru')
        return f"{hours_words} {minutes_words}"

    text = re.sub(r'\b(\d{1,2}):(\d{2})\b', time_replacer, text)

    # 4. Переводим любые другие изолированные или встроенные числа
    def number_replacer(match):
        number = int(match.group(0))
        try:
            return num2words(number, lang='ru')
        except:
            return match.group(0)

    text = re.sub(r'\d+', number_replacer, text)
    return text
