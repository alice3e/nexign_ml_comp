"""
Словари для генерации текстов на русском и английском языках.
Содержит действия, объекты, условия и метки для BPMN элементов.
"""

# Словарь действий (глаголы для Task)
ACTIONS = {
    "ru": [
        "Проверить", "Создать", "Отправить", "Получить", "Обработать",
        "Утвердить", "Отклонить", "Зарегистрировать", "Подготовить", "Выполнить",
        "Сохранить", "Удалить", "Обновить", "Загрузить", "Выгрузить",
        "Сформировать", "Рассчитать", "Проанализировать", "Оценить", "Согласовать",
        "Подписать", "Архивировать", "Уведомить", "Запросить", "Подтвердить"
    ],
    "en": [
        "Check", "Create", "Send", "Receive", "Process",
        "Approve", "Reject", "Register", "Prepare", "Execute",
        "Save", "Delete", "Update", "Upload", "Download",
        "Generate", "Calculate", "Analyze", "Evaluate", "Coordinate",
        "Sign", "Archive", "Notify", "Request", "Confirm"
    ]
}

# Словарь объектов (существительные для Task)
OBJECTS = {
    "ru": [
        "заказ", "документ", "заявку", "отчет", "счет",
        "платеж", "товар", "услугу", "данные", "информацию",
        "запрос", "ответ", "уведомление", "договор", "акт",
        "накладную", "спецификацию", "протокол", "резюме", "задачу",
        "проект", "план", "бюджет", "смету", "расчет"
    ],
    "en": [
        "order", "document", "request", "report", "invoice",
        "payment", "product", "service", "data", "information",
        "query", "response", "notification", "contract", "act",
        "waybill", "specification", "protocol", "resume", "task",
        "project", "plan", "budget", "estimate", "calculation"
    ]
}

# Словарь условий для XOR Gateway
CONDITIONS = {
    "ru": [
        "Одобрено?", "Оплачено?", "Доступно?", "Корректно?", "Завершено?",
        "Валидно?", "Подтверждено?", "Согласовано?", "Готово?", "Успешно?",
        "Проверено?", "Активно?", "Доступен?", "Существует?", "Требуется?"
    ],
    "en": [
        "Approved?", "Paid?", "Available?", "Correct?", "Completed?",
        "Valid?", "Confirmed?", "Coordinated?", "Ready?", "Successful?",
        "Checked?", "Active?", "Accessible?", "Exists?", "Required?"
    ]
}

# Метки для веток XOR (да/нет)
BRANCH_LABELS = {
    "ru": {
        "yes": ["Да", "Успех", "Одобрено", "Корректно", "Валидно"],
        "no": ["Нет", "Ошибка", "Отклонено", "Некорректно", "Невалидно"]
    },
    "en": {
        "yes": ["Yes", "Success", "Approved", "Correct", "Valid"],
        "no": ["No", "Error", "Rejected", "Incorrect", "Invalid"]
    }
}

# Метки для циклов
LOOP_LABELS = {
    "ru": {
        "repeat": ["Повторить", "Еще раз", "Продолжить"],
        "exit": ["Завершить", "Выход", "Готово"]
    },
    "en": {
        "repeat": ["Repeat", "Again", "Continue"],
        "exit": ["Finish", "Exit", "Done"]
    }
}

# Метки для параллельных веток
PARALLEL_LABELS = {
    "ru": ["Ветка A", "Ветка B", "Ветка C", "Процесс 1", "Процесс 2", "Процесс 3"],
    "en": ["Branch A", "Branch B", "Branch C", "Process 1", "Process 2", "Process 3"]
}

# Шаблоны для генерации имен задач
TASK_TEMPLATES = {
    "ru": [
        "{action} {object}",
        "{action} и проверить {object}",
        "{action} {object} в системе"
    ],
    "en": [
        "{action} {object}",
        "{action} and verify {object}",
        "{action} {object} in system"
    ]
}

# Названия событий
EVENT_NAMES = {
    "ru": {
        "start": "Начало процесса",
        "end": "Конец процесса"
    },
    "en": {
        "start": "Process start",
        "end": "Process end"
    }
}

# Шаблоны для текстового описания (формат Steps)
STEPS_TEMPLATES = {
    "ru": {
        "start": "Старт процесса",
        "task": "Выполнить: {name}",
        "xor_split": "Проверка условия: {condition}",
        "xor_branch_yes": "Если {condition} = Да:",
        "xor_branch_no": "Если {condition} = Нет:",
        "and_split": "Параллельное выполнение:",
        "and_branch": "  - {name}",
        "and_join": "Ожидание завершения всех параллельных веток",
        "loop_check": "Проверка: {condition}",
        "loop_repeat": "Если нужно повторить - возврат к шагу {step}",
        "end": "Завершение процесса"
    },
    "en": {
        "start": "Process start",
        "task": "Execute: {name}",
        "xor_split": "Check condition: {condition}",
        "xor_branch_yes": "If {condition} = Yes:",
        "xor_branch_no": "If {condition} = No:",
        "and_split": "Parallel execution:",
        "and_branch": "  - {name}",
        "and_join": "Wait for all parallel branches to complete",
        "loop_check": "Check: {condition}",
        "loop_repeat": "If repeat needed - return to step {step}",
        "end": "Process end"
    }
}

# Шаблоны для текстового описания (формат Pseudocode)
PSEUDOCODE_TEMPLATES = {
    "ru": {
        "start": "START",
        "end": "END",
        "task": "{name}",
        "if": "IF {condition} THEN",
        "else": "ELSE",
        "endif": "ENDIF",
        "while": "WHILE {condition} DO",
        "endwhile": "ENDWHILE",
        "fork": "FORK",
        "join": "JOIN",
        "branch": "  BRANCH: {name}"
    },
    "en": {
        "start": "START",
        "end": "END",
        "task": "{name}",
        "if": "IF {condition} THEN",
        "else": "ELSE",
        "endif": "ENDIF",
        "while": "WHILE {condition} DO",
        "endwhile": "ENDWHILE",
        "fork": "FORK",
        "join": "JOIN",
        "branch": "  BRANCH: {name}"
    }
}