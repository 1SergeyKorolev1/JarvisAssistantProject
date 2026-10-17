# Импортируем чистые функции из наших файлов
from .system_commands import shutdown_computer, get_current_time
from .browser_commands import search_internet, create_word_document

# Словарь, по которому main.py будет вызывать функции в коде
AVAILABLE_TOOLS = {
    'shutdown_computer': shutdown_computer,
    'get_current_time': get_current_time,
    'search_internet': search_internet,
    'create_word_document': create_word_document
}

# Описание функций для модели Qwen 2.5 (14B), чтобы она знала, КОГДА их вызывать
TOOLS_DEFINITION = [
    {
        'type': 'function',
        'function': {
            'name': 'shutdown_computer',
            'description': 'Выключить компьютер или завершить работу Windows через указанное количество минут.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'minutes': {'type': 'integer', 'description': 'Через сколько минут выключить ПК'}
                },
                'required': ['minutes']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_current_time',
            'description': 'Узнать точное текущее время и дату на компьютере.'
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'search_internet',
            'description': 'Найти информацию в интернете (гуглить), когда пользователю нужны свежие данные, факты или аналитика.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'Поисковый запрос в поисковую систему'}
                },
                'required': ['query']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'create_word_document',
            'description': 'Создать красивый структурированный файл Word (.docx) на Рабочем столе.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'topic': {'type': 'string', 'description': 'Главный заголовок документа'},
                    'content': {
                        'type': 'string',
                        'description': 'Развернутый текст. Используйте ## для подзаголовков. Чтобы вставить тематическую картинку, добавьте строчку [IMAGE: точный запрос для поиска картинки] строго на отдельной строке.'
                    },
                    'file_name': {'type': 'string', 'description': 'Имя файла, например: ai_report.docx'}
                },
                'required': ['topic', 'content', 'file_name']
            }
        }
    }

]
