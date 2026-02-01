# Быстрый старт - Трансформер BPMN → PNG

## За 5 минут

### 1. Установите Node.js

```bash
# macOS
brew install node

# Linux (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows - скачайте с https://nodejs.org/
```

### 2. Установите зависимости

```bash
# Python зависимости
cd transformer
pip install -r requirements.txt

# Node.js зависимости
cd renderer
npm install
cd ..
```

### 3. Запустите

```bash
python main.py
```

Готово! 🎉

---

## Подробнее

### Что происходит при запуске?

1. **Поиск BPMN файлов** - в директории `../LLM-gen/output/bpmn/`
2. **Рендеринг** - каждый BPMN файл преобразуется в PNG через bpmn-js
3. **Аугментация** - применяются случайные стилизации
4. **Сохранение** - результаты в `./output/`

### Структура выходных данных

```
output/
├── sample_000001/
│   ├── sample_000001.png          # PNG изображение
│   ├── sample_000001.bpmn         # BPMN XML
│   ├── sample_000001.txt/.md      # Описание
│   ├── sample_000001_ir.json      # IR JSON (если есть)
│   ├── sample_000001_meta.json    # Метаданные
│   └── sample_000001_render.json  # Параметры рендеринга
└── sample_000002/
    └── ...
```

### Настройка

Отредактируйте `config.yaml`:

```yaml
# Входная директория
input_dir: "../LLM-gen/output"

# Разрешение
rendering:
  min_resolution: 1024
  max_resolution: 3096

# Темы
rendering:
  themes:
    - light
    - dark
    - contrast
```

### Проблемы?

**Node.js не найден:**
```bash
node --version  # Проверьте установку
```

**Ошибки puppeteer (Linux):**
```bash
sudo apt-get install -y libgbm1 libnss3 libatk-bridge2.0-0
```

**Подробнее:** См. [`INSTALL.md`](INSTALL.md) и [`MIGRATION.md`](MIGRATION.md)

---

## Примеры использования

### Обработка конкретной директории

```python
# В main.py измените:
self.input_dir = Path('путь/к/вашим/bpmn/файлам')
```

### Изменение разрешения

```yaml
# В config.yaml:
rendering:
  min_resolution: 2048  # Увеличить разрешение
  max_resolution: 4096
```

### Отключение аугментаций

```yaml
# В config.yaml:
augmentation:
  rotation:
    enabled: false
  noise:
    enabled: false
```

### Использование в коде

```python
from core import BPMNRendererJS, StyleGenerator
import yaml

# Загрузить конфиг
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Создать стиль
style_gen = StyleGenerator(config)
style = style_gen.generate_style()

# Создать рендерер
renderer = BPMNRendererJS(style)

# Рендерить BPMN
with open('diagram.bpmn', 'r') as f:
    bpmn_xml = f.read()

image = renderer.render(bpmn_xml)
image.save('output.png')
```

---

## Что дальше?

- 📖 Полная документация: [`README.md`](README.md)
- 🔧 Установка: [`INSTALL.md`](INSTALL.md)
- 🚀 Миграция: [`MIGRATION.md`](MIGRATION.md)
- 📝 История изменений: [`CHANGELOG.md`](CHANGELOG.md)
- 🎨 Документация bpmn-js: https://bpmn.io/toolkit/bpmn-js/

---

## Поддержка

Возникли проблемы? Проверьте:
1. ✅ Node.js >= 18.0.0 установлен
2. ✅ Все зависимости установлены
3. ✅ BPMN файлы существуют во входной директории
4. ✅ Права на запись в выходную директорию

Подробнее см. раздел "Устранение проблем" в [`INSTALL.md`](INSTALL.md)