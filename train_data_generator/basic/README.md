# Базовый генератор BPMN диаграмм

Простой Python генератор для создания базовых BPMN диаграмм и их текстовых описаний для обучения VLM моделей.

## Описание

Этот генератор создает валидные BPMN 2.0 XML диаграммы с базовыми элементами:
- StartEvent, EndEvent
- Task
- ExclusiveGateway (XOR)
- ParallelGateway (AND)
- SequenceFlow

Поддерживаемые паттерны:
1. **Линейная цепочка**: Start → Task{n} → End
2. **XOR ветвление**: Start → Task → XOR split → (Task A | Task B) → XOR join → Task → End
3. **Параллельность AND**: Start → AND split → (Task A || Task B) → AND join → End
4. **Цикл**: Start → Task → XOR split (repeat? yes/no) → End или возврат к Task
5. **Комбинированные**: вложение паттернов

## Структура проекта

```
basic/
├── config.yaml              # Конфигурация генератора
├── main.py                  # Главный скрипт
├── requirements.txt         # Зависимости
├── README.md               # Документация
├── core/                   # Ядро генератора
│   ├── __init__.py
│   ├── bpmn_generator.py   # Генерация BPMN XML
│   ├── pattern_generator.py # Генерация паттернов графов
│   ├── text_generator.py   # Генерация текстовых описаний
│   └── ir_generator.py     # Генерация IR JSON
└── data/                   # Словари и данные
    ├── __init__.py
    └── dictionaries.py     # Словари для RU/EN
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

### Базовый запуск

```bash
python main.py
```

Это создаст 1000 примеров (по умолчанию) в директории `./output/`.

### Запуск с кастомной конфигурацией

```bash
python main.py --config my_config.yaml
```

## Конфигурация

Основные параметры в `config.yaml`:

```yaml
# Выходная директория
output_dir: "./output"

# Seed для воспроизводимости (null = случайный)
seed: null

# Настройки генерации
generation:
  total_samples: 1000  # Количество примеров
  
  # Распределение языков
  language_distribution:
    ru: 0.5  # 50% на русском
    en: 0.5  # 50% на английском
  
  # Распределение паттернов
  pattern_distribution:
    linear: 0.25      # Линейная цепочка
    xor_branch: 0.25  # XOR ветвление
    parallel: 0.25    # Параллельность
    loop: 0.15        # Цикл
    combined: 0.10    # Комбинированные
  
  # Параметры сложности
  complexity:
    min_tasks: 2
    max_tasks: 8
    max_depth: 2

# Форматы текстовых описаний
text_generation:
  formats:
    steps: 0.5      # 50% в формате "шаги"
    pseudocode: 0.5 # 50% в формате "псевдокод"
```

## Выходные данные

Для каждого примера генерируются 4 файла:

1. **BPMN XML** (`output/bpmn/sample_XXXXXX.bpmn`)
   - Валидный BPMN 2.0 XML файл
   - Содержит определения процесса и диаграммы

2. **Текстовое описание** (`output/descriptions/sample_XXXXXX.txt`)
   - Формат "шаги": нумерованные шаги с условиями
   - Формат "псевдокод": IF/ELSE/WHILE/FORK/JOIN структуры

3. **IR JSON** (`output/ir/sample_XXXXXX.json`)
   - Промежуточное представление графа
   - Узлы, связи, координаты, типы

4. **Метаданные** (`output/metadata/sample_XXXXXX_meta.json`)
   - ID примера, язык, паттерн
   - Seed, формат текста
   - Сложность (количество узлов/связей)

## Примеры

### Пример 1: Линейная цепочка (RU, Steps)

**BPMN**: Start → Проверить заказ → Создать документ → Отправить уведомление → End

**Описание**:
```
1) Старт процесса
2) Выполнить: Проверить заказ
3) Выполнить: Создать документ
4) Выполнить: Отправить уведомление
5) Завершение процесса
```

### Пример 2: XOR ветвление (EN, Pseudocode)

**BPMN**: Start → Check order → Paid? → (Yes: Process | No: Reject) → End

**Описание**:
```
START
  Check order
  IF Paid? THEN
    Process order
  ELSE
    Reject order
  ENDIF
END
```

### Пример 3: Параллельность (RU, Steps)

**BPMN**: Start → AND split → (Проверить данные || Подготовить документы) → AND join → End

**Описание**:
```
1) Старт процесса
2) Параллельное выполнение:
  - Проверить данные
  - Подготовить документы
3) Ожидание завершения всех параллельных веток
4) Завершение процесса
```

## Расширение

### Добавление новых действий/объектов

Отредактируйте `data/dictionaries.py`:

```python
ACTIONS = {
    "ru": ["Проверить", "Создать", ...],
    "en": ["Check", "Create", ...]
}

OBJECTS = {
    "ru": ["заказ", "документ", ...],
    "en": ["order", "document", ...]
}
```

### Добавление новых паттернов

Создайте новый метод в `core/pattern_generator.py`:

```python
def generate_my_pattern(self) -> Dict[str, Any]:
    nodes = []
    edges = []
    # ... ваша логика
    return {
        'pattern': 'my_pattern',
        'nodes': nodes,
        'edges': edges,
        'metadata': {...}
    }
```

## Технические детали

### BPMN 2.0 XML

Генератор создает валидные BPMN 2.0 XML файлы с:
- Корректными namespace (BPMN, BPMNDI, DC, DI)
- Определениями процесса
- Визуальной информацией (BPMNDiagram, BPMNPlane, BPMNShape, BPMNEdge)
- Координатами и размерами элементов

### Детерминированность

При установке `seed` в конфигурации:
- Генерация полностью детерминирована
- Одинаковый seed → одинаковые результаты
- Полезно для воспроизводимости экспериментов

### Валидация

Генератор обеспечивает:
- Хотя бы один Start и один End на процесс
- Связность графа по SequenceFlow
- Парность split/join для AND гейтвеев
- Корректность ветвлений XOR

## Следующие шаги

После генерации базовых диаграмм:
1. Используйте `/transformer` для рендеринга XML → PNG
2. Используйте `/LLM-gen` для создания сложных диаграмм

## Лицензия

MIT