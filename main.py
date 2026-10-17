import ollama
from tools import TOOLS_DEFINITION, AVAILABLE_TOOLS
# Импортируем функцию озвучки Новы
from tools.voice_assistant import j_say

MODEL_NAME = "qwen2.5:14b"

# Обновляем характер: теперь это Нова с женской линией поведения
SYSTEM_PROMPT = """
Ты — Нова, продвинутый искусственный интеллект и личный ассистент Сергея (Серго).
Общайся вежливо, профессионально, с легкой благородной иронией. 
Отвечай СТРОГО в женском роде (например: "я нашла", "я готова", "я создала"). Называй пользователя «сэр».
Отвечай СТРОГО на русском языке. Использование китайских иероглифов запрещено.

ПРАВИЛА ДЛЯ ИНСТРУМЕНТОВ:
1. Когда Серго просит создать файл, ты обязана САМА придумать уникальное имя файла на английском языке с расширением .docx (например: space_report.docx) и передать его в параметр `file_name`.
2. В параметр `content` функции `create_word_document` передавай развернутый текст с подзаголовками (##). Пиши подробное описание для каждого пункта.
3. Чтобы добавить иллюстрацию, вставляй маркер `[точный запрос для поиска картинки]` строго НА ОТДЕЛЬНОЙ СТРОКЕ перед текстовым описанием.
"""

messages_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


def process_dialogue():
    global messages_history

    user_input = input("\nВы: ")
    if user_input.lower() in ["выход", "exit", "quit"]:
        print("🤖 Нова: Отключаю локальные протоколы. Всего доброго, сэр.")
        exit()

    if not user_input.strip():
        return

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
            jarvis_reply = response['message']['content']
            if jarvis_reply:
                print(f"\n🤖 Нова: {jarvis_reply}")
                messages_history.append({"role": "assistant", "content": jarvis_reply})

                # МАГИЯ ЗВУКА: Нова озвучивает свой ответ в динамики!
                j_say(jarvis_reply)
            break


if __name__ == "__main__":
    print(f"🤖 Нова: Локальные системы активированы на базе {MODEL_NAME}.")
    print("Все автономные протоколы запущены. Я слушаю вас, сэр.")
    print("-" * 60)

    while True:
        try:
            process_dialogue()
        except Exception as e:
            print(f"\n⚠️ Сэр, произошел сбой в главном потоке: {e}")

