# Развертывание на Ubuntu 24.04 с NVIDIA T4

Пошаговая инструкция по развертыванию сервиса распознавания диаграмм на облачном сервере с GPU.

## Системные требования

- **ОС**: Ubuntu 24.04 LTS
- **GPU**: NVIDIA T4 (16 GB VRAM)
- **RAM**: 16+ GB
- **Диск**: 50+ GB свободного места
- **CPU**: 4+ ядра

## Шаг 1: Подготовка системы

### 1.1 Обновление системы

```bash
# Обновить список пакетов
sudo apt update && sudo apt upgrade -y

# Установить базовые утилиты
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    build-essential \
    software-properties-common
```

### 1.2 Проверка GPU

```bash
# Проверить наличие GPU
lspci | grep -i nvidia

# Должно вывести что-то вроде:
# 00:1e.0 3D controller: NVIDIA Corporation TU104GL [Tesla T4] (rev a1)
```

## Шаг 2: Установка NVIDIA драйверов

### 2.1 Установка драйверов

```bash
# Добавить репозиторий NVIDIA
sudo add-apt-repository ppa:graphics-drivers/ppa -y
sudo apt update

# Установить рекомендуемый драйвер
sudo ubuntu-drivers devices
sudo ubuntu-drivers autoinstall

# Или установить конкретную версию (рекомендуется 535+)
sudo apt install -y nvidia-driver-535

# Перезагрузить систему
sudo reboot
```

### 2.2 Проверка установки драйвера

```bash
# После перезагрузки проверить
nvidia-smi

# Должно вывести информацию о GPU:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2     |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  Tesla T4            Off  | 00000000:00:1E.0 Off |                    0 |
# | N/A   32C    P8     9W /  70W |      0MiB / 15360MiB |      0%      Default |
# +-------------------------------+----------------------+----------------------+
```

## Шаг 3: Установка Docker

### 3.1 Установка Docker Engine

```bash
# Удалить старые версии (если есть)
sudo apt remove -y docker docker-engine docker.io containerd runc

# Установить зависимости
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Добавить официальный GPG ключ Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Добавить репозиторий Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установить Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Проверить установку
docker --version
docker compose version
```

### 3.2 Настройка Docker

```bash
# Добавить текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Применить изменения (или перелогиниться)
newgrp docker

# Проверить работу без sudo
docker run hello-world

# Настроить автозапуск Docker
sudo systemctl enable docker
sudo systemctl start docker
```

## Шаг 4: Установка NVIDIA Container Toolkit

### 4.1 Установка toolkit

```bash
# Настроить репозиторий
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Установить toolkit
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Настроить Docker для использования NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Перезапустить Docker
sudo systemctl restart docker
```

### 4.2 Проверка NVIDIA Container Toolkit

```bash
# Запустить тестовый контейнер с GPU
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Должно вывести информацию о GPU внутри контейнера
```

## Шаг 5: Подготовка проекта

### 5.1 Копирование файлов

```bash
# Если еще не скопировали, используйте scp или rsync
# На локальной машине:
# rsync -avz -e ssh ./Deploy/ user@server-ip:/home/user/Deploy/

# На сервере перейти в директорию
cd ~/Deploy

# Проверить структуру
ls -la
# Должны быть: docker-compose.yml, backend/, frontend/, ML-container/, и т.д.
```

### 5.2 Проверка весов модели

```bash
# Проверить наличие LoRA адаптеров
ls -la ML-container/docker-volumes/weights/

# Должны быть файлы:
# adapter_config.json
# adapter_model.safetensors
# и другие

# Проверить размер
du -sh ML-container/docker-volumes/weights/
```

### 5.3 Создание .env файла

```bash
# Создать .env из примера
cp .env.example .env

# Отредактировать для GPU
vim .env
```

Содержимое `.env` для GPU:

```bash
# VLM Inference Service
DEVICE=cuda
TORCH_DTYPE=float16
MAX_NEW_TOKENS=384

# Backend Service
REQUEST_TIMEOUT=120

# Database Service
DB_PATH=/data/requests.db
```

## Шаг 6: Настройка docker-compose для GPU

### 6.1 Проверка конфигурации

Убедитесь, что в `docker-compose.yml` есть секция для GPU:

```yaml
vlm-inference:
  # ... другие настройки ...
  environment:
    - DEVICE=cuda
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Если этой секции нет, добавьте её в `docker-compose.yml`.

## Шаг 7: Запуск сервиса

### 7.1 Сборка образов

```bash
cd ~/Deploy

# Собрать все образы
docker compose build

# Это займет 10-15 минут при первом запуске
```

### 7.2 Запуск контейнеров

```bash
# Запустить все сервисы
docker compose up -d

# Проверить статус
docker compose ps

# Должны быть запущены все 5 сервисов:
# - backend
# - frontend
# - vlm-inference
# - adapter
# - database
```

### 7.3 Мониторинг запуска

```bash
# Следить за логами всех сервисов
docker compose logs -f

# Или только VLM сервиса (самый долгий запуск)
docker compose logs -f vlm-inference

# Дождаться сообщения:
# ✅ Модель успешно инициализирована за XX.XX сек
# ✅ Сервис готов к работе
```

### 7.4 Проверка использования GPU

```bash
# В отдельном терминале запустить мониторинг GPU
watch -n 1 nvidia-smi

# Должно показывать использование памяти VLM контейнером
# Примерно 4-6 GB для Qwen3-VL-2B-Instruct
```

## Шаг 8: Проверка работоспособности

### 8.1 Healthcheck всех сервисов

```bash
# Backend
curl http://localhost:8000/health

# VLM Inference
curl http://localhost:8002/health

# Adapter
curl http://localhost:8001/health

# Database
curl http://localhost:8003/health

# Frontend (должен вернуть HTML)
curl http://localhost:8501
```

### 8.2 Тестовый запрос

```bash
# Скачать тестовое изображение
wget https://example.com/test-diagram.png -O test.png

# Отправить на обработку
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@test.png" \
  -H "Content-Type: multipart/form-data"

# Должен вернуть JSON с описанием
```

### 8.3 Проверка метрик

```bash
# Метрики VLM сервиса
curl http://localhost:8002/metrics

# Должно показать:
# - inference_count
# - avg_inference_time
# - gpu_memory_allocated_gb
# - gpu_memory_reserved_gb
```

## Шаг 9: Настройка firewall (опционально)

### 9.1 UFW (Uncomplicated Firewall)

```bash
# Установить UFW
sudo apt install -y ufw

# Разрешить SSH (ВАЖНО!)
sudo ufw allow 22/tcp

# Разрешить порты сервиса
sudo ufw allow 8000/tcp  # Backend API
sudo ufw allow 8501/tcp  # Frontend UI

# Включить firewall
sudo ufw enable

# Проверить статус
sudo ufw status
```

### 9.2 Настройка nginx reverse proxy (рекомендуется)

```bash
# Установить nginx
sudo apt install -y nginx

# Создать конфигурацию
sudo vim /etc/nginx/sites-available/diagram-service
```

Содержимое конфигурации:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен

    client_max_body_size 50M;

    # Frontend
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активация конфигурации:

```bash
# Создать символическую ссылку
sudo ln -s /etc/nginx/sites-available/diagram-service /etc/nginx/sites-enabled/

# Проверить конфигурацию
sudo nginx -t

# Перезапустить nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Шаг 10: Настройка автозапуска

### 10.1 Systemd service для docker-compose

```bash
# Создать systemd unit
sudo vim /etc/systemd/system/diagram-service.service
```

Содержимое:

```ini
[Unit]
Description=Diagram Recognition Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/Deploy
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable diagram-service

# Запустить сервис
sudo systemctl start diagram-service

# Проверить статус
sudo systemctl status diagram-service
```

## Шаг 11: Мониторинг и логи

### 11.1 Просмотр логов

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f vlm-inference

# Последние 100 строк
docker compose logs --tail=100 vlm-inference

# Логи с временными метками
docker compose logs -f -t
```

### 11.2 Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование GPU
nvidia-smi

# Непрерывный мониторинг GPU
watch -n 1 nvidia-smi

# Использование диска
df -h
du -sh ~/Deploy/DB/docker-volumes/sqlite-db/
```

### 11.3 Установка monitoring stack (опционально)

```bash
# Prometheus + Grafana для продвинутого мониторинга
# Добавьте в docker-compose.yml или используйте отдельный стек
```

## Troubleshooting

### Проблема: GPU не обнаруживается в контейнере

**Решение:**
```bash
# Проверить nvidia-smi на хосте
nvidia-smi

# Проверить NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Перезапустить Docker
sudo systemctl restart docker

# Пересобрать контейнер
docker compose down
docker compose up -d --build vlm-inference
```

### Проблема: Out of Memory (OOM)

**Решение:**
```bash
# Проверить использование памяти
nvidia-smi

# Уменьшить batch size или использовать квантование
# В .env:
TORCH_DTYPE=float16  # Вместо float32

# Или использовать int8 квантование (требует изменений в коде)
```

### Проблема: Медленная загрузка модели

**Решение:**
```bash
# Модель загружается из HuggingFace при первом запуске
# Проверить наличие кэша
ls -la ~/Deploy/ML-container/docker-volumes/base-model/hub/

# Если пусто, модель скачивается (это нормально при первом запуске)
# Следить за прогрессом:
docker compose logs -f vlm-inference
```

### Проблема: Контейнер постоянно перезапускается

**Решение:**
```bash
# Проверить логи
docker compose logs vlm-inference

# Проверить доступные ресурсы
free -h
df -h

# Увеличить лимиты в docker-compose.yml
```

## Бэкап и восстановление

### Создание бэкапа

```bash
# Остановить сервисы
docker compose down

# Создать архив
tar -czf diagram-service-backup-$(date +%Y%m%d).tar.gz \
    ~/Deploy/DB/docker-volumes/sqlite-db/ \
    ~/Deploy/ML-container/docker-volumes/weights/ \
    ~/Deploy/.env

# Скопировать на другой сервер или в облако
```

### Восстановление из бэкапа

```bash
# Распаковать архив
tar -xzf diagram-service-backup-YYYYMMDD.tar.gz -C ~/

# Запустить сервисы
cd ~/Deploy
docker compose up -d
```

## Обновление системы

### Обновление кода

```bash
# Остановить сервисы
docker compose down

# Получить обновления (если используется git)
git pull

# Пересобрать образы
docker compose build

# Запустить
docker compose up -d
```

### Обновление модели

```bash
# Остановить VLM сервис
docker compose stop vlm-inference

# Заменить веса
cp new_weights/* ~/Deploy/ML-container/docker-volumes/weights/

# Запустить
docker compose up -d vlm-inference
```

## Производительность на NVIDIA T4

### Ожидаемые показатели

| Метрика | Значение |
|---------|----------|
| Время загрузки модели | 30-60 сек |
| Время инференса (простая диаграмма) | 3-5 сек |
| Время инференса (сложная диаграмма) | 5-10 сек |
| Использование VRAM | 4-6 GB |
| Throughput | 6-12 запросов/мин |

### Оптимизация

1. **Использовать float16** вместо float32
2. **Batch processing** для нескольких изображений
3. **Кэширование** результатов в БД
4. **Масштабирование** - запустить несколько реплик VLM сервиса

## Безопасность

### Рекомендации для продакшна

1. **Настроить HTTPS** через Let's Encrypt
2. **Добавить аутентификацию** для API
3. **Ограничить доступ** к портам через firewall
4. **Регулярно обновлять** систему и Docker
5. **Настроить мониторинг** и алерты
6. **Делать регулярные бэкапы** БД

## Полезные команды

```bash
# Перезапуск всех сервисов
docker compose restart

# Перезапуск конкретного сервиса
docker compose restart vlm-inference

# Просмотр использования ресурсов
docker stats

# Очистка неиспользуемых образов
docker system prune -a

# Просмотр логов с фильтрацией
docker compose logs vlm-inference | grep ERROR

# Вход в контейнер для отладки
docker compose exec vlm-inference bash
```

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker compose logs`
2. Проверьте статус GPU: `nvidia-smi`
3. Проверьте использование ресурсов: `docker stats`
4. Обратитесь к основной документации: `README.md`