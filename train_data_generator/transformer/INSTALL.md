# Инструкция по установке трансформера BPMN → PNG

## Системные требования

- **Python** >= 3.8
- **Node.js** >= 18.0.0
- **npm** (устанавливается с Node.js)

## Пошаговая установка

### Шаг 1: Установка Python зависимостей

```bash
cd transformer
pip install -r requirements.txt
```

Это установит:
- `lxml` - для парсинга BPMN XML
- `Pillow` - для работы с изображениями
- `pyyaml` - для конфигурации
- `numpy` - для численных операций
- `opencv-python` - для аугментаций
- `scipy` - для научных вычислений

### Шаг 2: Установка Node.js

#### macOS

```bash
# Используя Homebrew
brew install node

# Проверка установки
node --version  # должно быть >= 18.0.0
npm --version
```

#### Linux (Ubuntu/Debian)

```bash
# Установка Node.js 18.x через NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Проверка установки
node --version
npm --version
```

#### Linux (Fedora/RHEL)

```bash
# Установка Node.js 18.x
sudo dnf install nodejs

# Или через NodeSource
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install nodejs

# Проверка установки
node --version
npm --version
```

#### Windows

1. Скачайте установщик с официального сайта: https://nodejs.org/
2. Запустите установщик и следуйте инструкциям
3. Перезапустите терминал
4. Проверьте установку:
```cmd
node --version
npm --version
```

### Шаг 3: Установка Node.js зависимостей

```bash
cd transformer/renderer
npm install
```

Это установит:
- `puppeteer` - headless браузер для рендеринга

**Важно:** При первом запуске puppeteer скачает Chromium (~150 MB). Это нормально.

#### Дополнительные зависимости для Linux

Puppeteer требует системных библиотек:

```bash
# Ubuntu/Debian
sudo apt-get install -y \
  ca-certificates \
  fonts-liberation \
  libappindicator3-1 \
  libasound2 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libcups2 \
  libdbus-1-3 \
  libgbm1 \
  libgtk-3-0 \
  libnss3 \
  libx11-xcb1 \
  libxcomposite1 \
  libxdamage1 \
  libxrandr2 \
  xdg-utils

# Fedora/RHEL
sudo dnf install -y \
  alsa-lib \
  atk \
  cups-libs \
  gtk3 \
  libXcomposite \
  libXdamage \
  libXrandr \
  mesa-libgbm \
  nss \
  pango
```

### Шаг 4: Проверка установки

```bash
# Вернуться в директорию transformer
cd ..

# Запустить тестовый рендеринг
python -c "
from core import BPMNRendererJS, StyleGenerator
import yaml

# Загрузить конфиг
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Создать стиль
style_gen = StyleGenerator(config)
style = style_gen.generate_style()

# Создать рендерер (проверит Node.js и зависимости)
renderer = BPMNRendererJS(style)
print('✅ Рендерер успешно инициализирован!')
"
```

Если вы видите сообщение "✅ Рендерер успешно инициализирован!", установка прошла успешно!

## Устранение проблем

### Ошибка: "Node.js не найден"

**Решение:**
1. Убедитесь, что Node.js установлен: `node --version`
2. Если команда не найдена, переустановите Node.js
3. Перезапустите терминал после установки

### Ошибка: "npm не найден"

**Решение:**
npm устанавливается вместе с Node.js. Переустановите Node.js с официального сайта.

### Ошибка при установке puppeteer

**Причина:** Отсутствуют системные библиотеки

**Решение для Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y libgbm1 libnss3 libatk-bridge2.0-0

# Fedora/RHEL
sudo dnf install -y mesa-libgbm nss atk
```

### Ошибка: "Таймаут при рендеринге"

**Причина:** Медленная система или большая диаграмма

**Решение:**
Увеличьте таймаут в `core/bpmn_renderer_js.py`:
```python
# Строка ~120
timeout=120  # увеличить с 60 до 120 секунд
```

### Ошибка: "Cannot find module 'puppeteer'"

**Причина:** Зависимости не установлены

**Решение:**
```bash
cd transformer/renderer
rm -rf node_modules package-lock.json
npm install
```

## Альтернативная установка (Docker)

Если у вас возникают проблемы с установкой, можно использовать Docker:

```dockerfile
FROM node:18

# Установить Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Установить системные зависимости для puppeteer
RUN apt-get install -y \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgbm1 \
    libgtk-3-0 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils

# Копировать проект
WORKDIR /app
COPY . .

# Установить зависимости
RUN pip3 install -r transformer/requirements.txt
RUN cd transformer/renderer && npm install

# Запуск
CMD ["python3", "transformer/main.py"]
```

## Проверка работоспособности

После установки запустите полный тест:

```bash
cd transformer
python main.py
```

Если все настроено правильно, вы увидите:
```
Найдено X BPMN файлов для трансформации...
[1/X] Обработка sample_000001...
Rendering BPMN to PNG: ...
Successfully rendered: ...
```

## Дополнительная информация

- [Документация bpmn-js](https://bpmn.io/toolkit/bpmn-js/)
- [Документация puppeteer](https://pptr.dev/)
- [Node.js официальный сайт](https://nodejs.org/)

## Поддержка

При возникновении проблем:
1. Проверьте версии: `node --version`, `python --version`
2. Убедитесь, что все зависимости установлены
3. Проверьте логи ошибок
4. См. раздел "Устранение проблем" выше