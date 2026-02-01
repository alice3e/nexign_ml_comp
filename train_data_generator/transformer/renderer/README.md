# BPMN Renderer (Node.js)

Этот модуль использует **bpmn-js** и **puppeteer** для высококачественного рендеринга BPMN диаграмм в PNG изображения.

## Требования

- **Node.js** >= 18.0.0
- **npm** (устанавливается вместе с Node.js)

## Установка

### 1. Установка Node.js

#### macOS
```bash
# Используя Homebrew
brew install node

# Или скачайте с официального сайта
# https://nodejs.org/
```

#### Linux (Ubuntu/Debian)
```bash
# Используя NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Проверка установки
node --version
npm --version
```

#### Windows
Скачайте установщик с официального сайта: https://nodejs.org/

### 2. Установка зависимостей

Зависимости устанавливаются автоматически при первом запуске Python скрипта.

Для ручной установки:
```bash
cd transformer/renderer
npm install
```

Это установит:
- **puppeteer** - для рендеринга в headless браузере
- **bpmn-js** (загружается через CDN в HTML)

## Использование

### Из Python

```python
from core import BPMNRendererJS, StyleGenerator

# Создать стиль
style_gen = StyleGenerator(config)
style = style_gen.generate_style()

# Создать рендерер
renderer = BPMNRendererJS(style)

# Рендерить BPMN
image = renderer.render(bpmn_xml)
image.save('output.png')
```

### Напрямую из командной строки

```bash
node bpmn_to_png.js input.bpmn output.png '{"width": 2048, "height": 2048}'
```

## Параметры рендеринга

```json
{
  "width": 2048,           // Ширина изображения в пикселях
  "height": 2048,          // Высота изображения в пикселях
  "backgroundColor": "#ffffff",  // Цвет фона (HEX)
  "scale": 1.0,            // Масштаб (не используется в текущей версии)
  "padding": 20            // Отступы от краев в пикселях
}
```

## Преимущества bpmn-js

1. **Стандартное отображение** - соответствует BPMN 2.0 спецификации
2. **Высокое качество** - векторная графика без искажений
3. **Правильная типографика** - корректное отображение текста и символов
4. **Автоматический layout** - правильное позиционирование элементов
5. **Поддержка всех элементов BPMN** - включая сложные конструкции

## Устранение проблем

### Ошибка: "Node.js не найден"
Убедитесь, что Node.js установлен и доступен в PATH:
```bash
node --version
```

### Ошибка: "npm не найден"
npm устанавливается вместе с Node.js. Переустановите Node.js.

### Ошибка при установке puppeteer
Puppeteer требует дополнительных системных библиотек:

**Linux:**
```bash
sudo apt-get install -y \
  ca-certificates \
  fonts-liberation \
  libappindicator3-1 \
  libasound2 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libc6 \
  libcairo2 \
  libcups2 \
  libdbus-1-3 \
  libexpat1 \
  libfontconfig1 \
  libgbm1 \
  libgcc1 \
  libglib2.0-0 \
  libgtk-3-0 \
  libnspr4 \
  libnss3 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libstdc++6 \
  libx11-6 \
  libx11-xcb1 \
  libxcb1 \
  libxcomposite1 \
  libxcursor1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxi6 \
  libxrandr2 \
  libxrender1 \
  libxss1 \
  libxtst6 \
  lsb-release \
  wget \
  xdg-utils
```

### Таймаут при рендеринге
Увеличьте таймаут в `bpmn_renderer_js.py` (по умолчанию 60 секунд).

## Производительность

- Первый запуск: ~5-10 секунд (запуск браузера)
- Последующие рендеры: ~1-3 секунды на диаграмму
- Рекомендуется для батч-обработки использовать параллельные процессы

## Лицензия

MIT