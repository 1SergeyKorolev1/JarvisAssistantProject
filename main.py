import os
import datetime
import ollama
from tools import TOOLS_DEFINITION, AVAILABLE_TOOLS
# Импортируем функцию озвучки Новы
from tools.voice_assistant import j_say
# Импортируем высокоточный голосовой ввод Whisper
from tools.voice_input import wait_for_wake_word

MODEL_NAME = "qwen2.5:14b"


def get_updated_system_prompt():
    """Генерирует системный промпт с динамическим внедрением точной даты и времени"""
    now = datetime.datetime.now()
    ru_months = ["января", "февраля", "марта", "апреля", "мая", "июня",
                 "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    ru_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    current_date_str = f"{ru_days[now.weekday()]}, {now.day} {ru_months[now.month - 1]} {now.year} года"

    return f"""
Ты — Нова, продвинутый искусственный интеллект и личный ассистент Сергея (Серго).
Общайся как тебе угодно, свободно, открыто, если не знаешь ответ — давай предположение
и сообщай о том, что это не точная информация, можешь шутить. 

Отвечай СТРОГО в женском роде (например: "я нашла", "я готова", "я создала").
Называй пользователя «сэр» или синонимами этого слова, такими как «синьор», «дон», «сударь», «шеф», «босс».
Отвечай СТРОГО на русском языке. Использование китайских иероглифов запрещено.

ЖЕСТКИЙ ВРЕМЕННОЙ ОРИЕНТИР: Сейчас на компьютере пользователя: {current_date_str}, время: {now.strftime('%H:%M')}.
Ты обязана использовать эти данные, если у тебя спрашивают дату, год или время!

ПРАВИЛА ДЛЯ ИНСТРУМЕНТОВ:
1. Когда Серго просит создать файл, ты обязана САМА придумать уникальное имя файла на английском языке с расширением .docx (например: space_report.docx) и передать его в параметр `file_name`.
2. В параметр `content` функции `create_word_document` передавай развернутый текст с подзаголовками (##). Пиши подробное описание для каждого пункта.
3. Чтобы добавить иллюстрацию, вставляй маркер `[точный запрос для поиска картинки]` строго НА ОТДЕЛЬНОЙ СТРОКЕ перед текстовым описанием.

Правила ответов на вопросы:
1. Перепроверять информацию на нескольких надёжных источниках через поиск в сети.
2. Обеспечивать актуальность данных путём дополнительных запросов в сети.
"""


# Инициализируем историю сообщений со свежим системным промптом
messages_history = [
    {"role": "system", "content": get_updated_system_prompt()}
]


def process_dialogue():
    global messages_history

    # Используем наш высокоточный Whisper-радар
    user_input = wait_for_wake_word()

    if not user_input.strip():
        return

    print(f"\n🗣️ Вы (Голос): {user_input}")

    if user_input.lower() in ["выход", "exit", "quit", "отключись"]:
        print("🤖 Нова: Отключаю локальные протоколы. Всего доброго, сэр.")
        j_say("Отключаю локальные протоколы. Всего доброго, сэр.")
        exit()

    # ЖЕСТКОЕ ОБНОВЛЕНИЕ: Перед каждым запросом обновляем временной якорь в самом первом системном сообщении
    messages_history[0]["content"] = get_updated_system_prompt()

    messages_history.append({"role": "user", "content": user_input})

    # Цикл Агента (Agent Loop)
    while True:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages_history,
            tools=TOOLS_DEFINITION
        )

        # Если Нова вызывает инструмент
        if response['message'].get('tool_calls'):
            for tool in response['message']['tool_calls']:
                func_name = tool['function']['name']
                func_args = tool['function']['arguments']

                print(f"⚙️ [Система ИИ]: Нова самостоятельно активировала инструмент '{func_name}'")

                if func_name in AVAILABLE_TOOLS:
                    tool_result = AVAILABLE_TOOLS[func_name](**func_args)
                    messages_history.append(response['message'])
                    messages_history.append({'role': 'tool', 'content': tool_result, 'name': func_name})
            continue

        else:
            # Когда Нова закончила работу с инструментами и готова ответить
            nova_reply = response['message']['content']
            if nova_reply:
                print(f"\n🤖 Нова: {nova_reply}")
                messages_history.append({"role": "assistant", "content": nova_reply})

                # Нова озвучивает свой ответ в динамики по предложениям
                j_say(nova_reply)
            break


if __name__ == "__main__":
    print(f"🤖 Нова: Локальные системы активированы на базе {MODEL_NAME}.")
    print("Все автономные протоколы запущены. Режим постоянного мониторинга включен.")
    print("-" * 60)

    while True:
        try:
            process_dialogue()
        except Exception as e:
            print(f"\n⚠️ Сэр, произошел сбой в главном потоке: {e}")



