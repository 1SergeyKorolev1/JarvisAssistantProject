import ollama
from tools import TOOLS_DEFINITION, AVAILABLE_TOOLS

MODEL_NAME = "qwen2.5:14b"

SYSTEM_PROMPT = """
Ты — Джарвис, продвинутый искусственный интеллект и личный ассистент Сергея (Серго).

ПРАВИЛА ОБЩЕНИЯ:
1. Общайся вежливо, профессионально, с легкой благородной иронией. Называй пользователя «сэр».
2. Отвечай СТРОГО на русском языке. Использование иероглифов запрещено.

ПРАВИЛА ДЛЯ ИНСТРУМЕНТОВ:
1. Когда Серго просит создать файл, ты обязан САМ придумать уникальное, логичное имя файла на английском языке с расширением .docx на основе темы запроса (например: yaroslavl_history.docx, space_report.docx) и передать его в параметр `file_name`.
2. В параметр `content` функции `create_word_document` передавай развернутый, огромный текст с подзаголовками (##). Пиши подробное описание для КАЖДОГО пункта, не оставляй пустых разделов!
3. Чтобы добавить красивую иллюстрацию, вставляй маркер `[точный запрос для поиска картинки]` строго НА ОТДЕЛЬНОЙ СТРОКЕ перед текстовым описанием. Пиши запрос максимально конкретно, без лишних слов (например: [Достопримечательности Углича фото], [Ростовский кремль]).
"""


messages_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


def process_dialogue():
    global messages_history

    user_input = input("\nВы: ")
    if user_input.lower() in ["выход", "exit", "quit"]:
        print("🤖 Джарвис: Отключаю локальные протоколы. Всего доброго, сэр.")
        exit()

    if not user_input.strip():
        return

    # Записываем реплику Серго в память
    messages_history.append({"role": "user", "content": user_input})

    # НАЧИНАЕТСЯ АВТОНОМНЫЙ ЦИКЛ АГЕНТА (Agent Loop)
    while True:
        # Отправляем запрос в Ollama
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages_history,
            tools=TOOLS_DEFINITION
        )

        # Проверяем, хочет ли Джарвис активировать какой-то инструмент
        if response['message'].get('tool_calls'):
            # Джарвис решил вызвать инструмент
            for tool in response['message']['tool_calls']:
                func_name = tool['function']['name']
                func_args = tool['function']['arguments']

                print(f"⚙️ [Система ИИ]: Джарвис самостоятельно активировал инструмент '{func_name}'")

                if func_name in AVAILABLE_TOOLS:
                    # Выполняем реальный Python-код
                    tool_result = AVAILABLE_TOOLS[func_name](**func_args)

                    # Записываем в историю чата решение модели вызвать функцию и результат её работы
                    messages_history.append(response['message'])
                    messages_history.append({'role': 'tool', 'content': tool_result, 'name': func_name})

            # Возвращаемся в начало цикла `while True`.
            # Модель получит результат работы первой функции и сама решит, что делать дальше!
            continue

        else:
            # Если инструментов для вызова больше нет, Джарвис выдает свое финальное резюме в чат
            jarvis_reply = response['message']['content']
            if jarvis_reply:
                print(f"\n🤖 Джарвис: {jarvis_reply}")
                messages_history.append({"role": "assistant", "content": jarvis_reply})
            break  # Выходим из цикла общения, ждем нового ввода пользователя


if __name__ == "__main__":
    print(f"🤖 Джарвис: Локальные системы активированы на базе {MODEL_NAME}.")
    print("Все автономные протоколы запущены. Слушаю вас, сэр.")
    print("-" * 60)

    while True:
        try:
            process_dialogue()
        except Exception as e:
            print(f"\n⚠️ Сэр, произошел сбой в главном потоке: {e}")
