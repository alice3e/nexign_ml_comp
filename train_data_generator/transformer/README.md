# Трансформер BPMN → PNG

Модуль для преобразования BPMN XML диаграмм в PNG изображения с разнообразной стилизацией и аугментацией.

## Описание

Трансформер принимает на вход BPMN XML файлы (из генератора `basic` или `LLM-gen`) и создает PNG изображения с:
- **Высококачественным рендерингом через bpmn-js** - стандартное отображение BPMN 2.0
- Различными цветовыми темами (светлая, темная, контрастная)
- Вариативной геометрией (толщина линий, размеры элементов)
- Аугментациями (поворот, шум, размытие, JPEG артефакты и др.)

## Новая версия рендерера

**Важно:** Модуль теперь использует библиотеку **bpmn-js** для рендеринга, что обеспечивает:
- ✅ Отсутствие искажений и артефактов
- ✅ Правильное отображение всех элементов BPMN 2.0
- ✅ Корректную типографику и расположение текста
- ✅ Соответствие стандарту BPMN 2.0

Рендеринг выполняется через Node.js с использованием headless браузера (puppeteer).

## Структура проекта

```
transformer/
├── config.yaml              # Конфигурация трансформера
├── main.py                  # Главный скрипт
├── requirements.txt         # Зависимости
├── README.md               # Документация
└── core/                   # Ядро трансформера
    ├── __init__.py
    ├── bpmn_renderer.py    # Рендеринг BPMN в изображение
    ├── style_generator.py  # Генерация случайных стилей
    └── image_augmentor.py  # Аугментация изображений
```

## Установка

### 1. Установите Python зависимости:
```bash
pip install -r requirements.txt
```

### 2. Установите Node.js (>= 18.0.0)

**macOS:**
```bash
brew install node
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows:**
Скачайте установщик с https://nodejs.org/

### 3. Установите Node.js зависимости

Зависимости устанавливаются автоматически при первом запуске. Для ручной установки:
```bash
cd transformer/renderer
npm install
```

Подробнее см. [`renderer/README.md`](renderer/README.md)

## Использование

### Базовый запуск

```bash
python main.py
```

Это обработает все BPMN файлы из `../basic/output/` и создаст PNG изображения в `./output/`.

### Запуск с кастомной конфигурацией

```bash
python main.py --config my_config.yaml
```

## Конфигурация

Основные параметры в `config.yaml`:

### Пути

```yaml
input_dir: "../basic/output"  # Входная директория с BPMN файлами
output_dir: "./output"         # Выходная директория
```

### Рендеринг

```yaml
rendering:
  min_resolution: 1024  # Минимальное разрешение (длинная сторона)
  max_resolution: 2048  # Максимальное разрешение
  
  themes:               # Доступные темы
    - light
    - dark
    - contrast
  
  theme_weights:        # Вероятности выбора темы
    light: 0.5
    dark: 0.3
    contrast: 0.2
```

### Цветовые палитры

Для каждой темы определены палитры цветов:
- `background` - цвет фона
- `task_fill` / `task_stroke` - заливка и обводка задач
- `gateway_fill` / `gateway_stroke` - заливка и обводка гейтвеев
- `event_fill` / `event_stroke` - заливка и обводка событий
- `flow_stroke` - цвет связей
- `text_color` - цвет текста

### Шрифты

```yaml
fonts:
  available:
    - "DejaVu Sans"
    - "Liberation Sans"
    - "FreeSans"
  
  task_name_size: [10, 12, 14]
  gateway_name_size: [9, 10, 11]
  event_name_size: [8, 9, 10]
  flow_label_size: [8, 9, 10]
```

### Геометрия

```yaml
geometry:
  task_stroke_width: [1.5, 2.0, 2.5]
  gateway_stroke_width: [2.0, 2.5, 3.0]
  event_stroke_width: [2.0, 2.5, 3.0]
  flow_stroke_width: [1.0, 1.5, 2.0]
  task_corner_radius: [3, 5, 8]
  arrow_size: [8, 10, 12]
```

### Аугментации

```yaml
augmentation:
  # Поворот изображения
  rotation:
    enabled: true
    min_angle: -2
    max_angle: 2
  
  # Зум и панорамирование
  zoom_pan:
    enabled: true
    zoom_range: [0.95, 1.05]
    pan_range: [-20, 20]
  
  # JPEG артефакты
  jpeg_artifacts:
    enabled: true
    quality_range: [85, 95]
  
  # Гауссово размытие
  gaussian_blur:
    enabled: true
    kernel_size: [0, 1, 3]
    sigma: [0.3, 0.5, 0.7]
  
  # Шум
  noise:
    enabled: true
    noise_level: [0, 5, 10]
  
  # Яркость и контраст
  brightness_contrast:
    enabled: true
    brightness_range: [-20, 20]
    contrast_range: [0.9, 1.1]
  
  # Перспективная дисторсия
  perspective:
    enabled: true
    max_distortion: 0.02
```

### Вероятности аугментаций

```yaml
augmentation_probabilities:
  label_offset: 0.3
  rotation: 0.5
  zoom_pan: 0.3
  jpeg_artifacts: 0.4
  gaussian_blur: 0.2
  noise: 0.3
  brightness_contrast: 0.4
  perspective: 0.2
```

## Выходные данные

Для каждого примера создается отдельная директория `sample_XXXXXX/` содержащая:

1. **PNG изображение** (`sample_XXXXXX.png`)
   - Рендеренная BPMN диаграмма
   - С применением стилизации и аугментаций

2. **BPMN XML** (`sample_XXXXXX.bpmn`)
   - Копия исходного BPMN файла

3. **Текстовое описание** (`sample_XXXXXX.txt`)
   - Копия текстового описания из basic генератора

4. **IR JSON** (`sample_XXXXXX_ir.json`)
   - Промежуточное представление графа

5. **Метаданные генерации** (`sample_XXXXXX_meta.json`)
   - Метаданные из basic генератора

6. **Параметры рендеринга** (`sample_XXXXXX_render.json`)
   - Использованная тема, цвета, шрифты
   - Примененные аугментации
   - Разрешение изображения

## Примеры

### Пример структуры выходной директории

```
output/
├── sample_000001/
│   ├── sample_000001.png          # PNG изображение
│   ├── sample_000001.bpmn         # BPMN XML
│   ├── sample_000001.txt          # Текстовое описание
│   ├── sample_000001_ir.json      # IR JSON
│   ├── sample_000001_meta.json    # Метаданные генерации
│   └── sample_000001_render.json  # Параметры рендеринга
├── sample_000002/
│   └── ...
└── sample_000003/
    └── ...
```

### Пример параметров рендеринга

```json
{
  "style": {
    "theme": "light",
    "resolution": 1536,
    "font_family": "DejaVu Sans",
    "colors": {
      "background": "#FFFFFF",
      "task_fill": "#E3F2FD",
      "task_stroke": "#1976D2",
      "gateway_fill": "#FFF9C4",
      "gateway_stroke": "#F57F17",
      "event_fill": "#E1F5FE",
      "event_stroke": "#0277BD",
      "flow_stroke": "#424242",
      "text_color": "#212121"
    },
    "geometry": {
      "task_stroke_width": 2.0,
      "gateway_stroke_width": 2.5,
      "event_stroke_width": 2.0,
      "flow_stroke_width": 1.5,
      "task_corner_radius": 5,
      "arrow_size": 10,
      "text_padding": 5,
      "line_spacing": 1.2
    }
  },
  "augmentation": {
    "rotation": 1.5,
    "jpeg_quality": 90,
    "brightness": -5,
    "contrast": 1.05
  }
}
```

## Технические детали

### Рендеринг BPMN элементов

Рендеринг выполняется с использованием **bpmn-js** - официальной библиотеки для работы с BPMN 2.0:

- **Task**: Прямоугольник со скругленными углами (согласно BPMN 2.0)
- **StartEvent**: Круг с тонкой обводкой
- **EndEvent**: Круг с двойной обводкой
- **ExclusiveGateway**: Ромб с X внутри
- **ParallelGateway**: Ромб с + внутри
- **SequenceFlow**: Линия со стрелкой и опциональной меткой
- **SubProcess, Pools, Lanes** и другие сложные элементы

### Архитектура рендеринга

1. **Python** (transformer/main.py) - управление процессом
2. **Node.js** (renderer/bpmn_to_png.js) - рендеринг через bpmn-js
3. **Puppeteer** - headless браузер для выполнения JavaScript
4. **bpmn-js** - библиотека для отображения BPMN (загружается через CDN)

### Масштабирование

Изображение автоматически масштабируется так, чтобы длинная сторона соответствовала целевому разрешению (1024-2048 px).

### Аугментации

Аугментации применяются в следующем порядке:
1. Зум и панорамирование
2. Поворот
3. Перспективная дисторсия
4. Яркость и контраст
5. Гауссово размытие
6. Шум
7. JPEG артефакты

### Детерминированность

Если в метаданных примера указан `seed`, он используется для генерации стиля, обеспечивая воспроизводимость.

## Интеграция с другими модулями

### С basic генератором

```bash
# 1. Генерация BPMN диаграмм
cd basic
python main.py

# 2. Трансформация в PNG
cd ../transformer
python main.py
```

### С LLM-gen генератором

```bash
# 1. Генерация сложных BPMN диаграмм
cd LLM-gen
python main.py

# 2. Трансформация в PNG
cd ../transformer
python main.py --config config_llm.yaml
```

## Расширение

### Добавление новой темы

Отредактируйте `config.yaml`:

```yaml
rendering:
  themes:
    - light
    - dark
    - contrast
    - my_theme  # новая тема

color_palettes:
  my_theme:
    background: ["#..."]
    task_fill: ["#..."]
    # ... остальные цвета
```

### Добавление новой аугментации

1. Добавьте метод в `core/image_augmentor.py`:

```python
def _apply_my_augmentation(self, image: Image.Image) -> Image.Image:
    # ваша логика
    return modified_image
```

2. Добавьте вызов в метод `augment()`:

```python
if 'my_param' in self.params:
    img = self._apply_my_augmentation(img)
```

3. Добавьте параметры в `config.yaml`

## Производительность

- Обработка одного примера: ~0.5-2 секунды (зависит от разрешения и аугментаций)
- Рекомендуется для больших датасетов: использовать параллельную обработку

## Требования

- Python 3.8+
- PIL/Pillow для работы с изображениями
- OpenCV для продвинутых аугментаций
- NumPy для численных операций
- lxml для парсинга BPMN XML

## Лицензия

MIT