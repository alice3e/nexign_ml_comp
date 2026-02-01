Аутентификация
OAuth:
Header в запросах: Authorization: OAuth <token>

Как попробовать
Запрос в gpt-5-mini
```
import requests
import os

url = "https://api.eliza.yandex.net/openai/v1/chat/completions"

payload = {
    "model": "gpt-5-mini",
    "messages": [
        {
            "role": "user",
            "content": "Hello!"
        }
    ]
}
headers = {
    "authorization": f"OAuth {os.environ['SOY_TOKEN']}",
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

Или

```
# pip3 install openai
# echo SOY_TOKEN=<token>

import os
from openai import OpenAI

client = OpenAI(base_url="https://api.eliza.yandex.net/raw/openai/v1", api_key=os.getenv("SOY_TOKEN"))

completion = client.chat.completions.create(
  model="gpt-5",
  messages=[
    {"role": "user", "content": "Hello, world!"}
  ]
)

print(completion.choices[0].message)
```

Eliza сохраняет исходный интерфейс внешних api, в большинстве случаев тело запроса летит в исходном виде.

Использование параметров и выбор моделей

Вы можете использовать в целом любые параметры из документации провейдера (например OpenAI) - не обязательно искать их в нашей доке.

Провайдером может быть не только разработчик, но и прокси как OpenRouter или Together

Но Вы не можете ходить в любую ручку - список ручек мы ограничиваем, потому что только там мы можем быть уверены, что правильно посчитали стоимость каждого запроса

Формат ответа:
Eliza API оборачивает ответ модели в response, добавляя метаданные

```json
{
    "key": "ORG_SPECIAL_KEY_11", - использованный ключ. может быть важно, если Вы используете свои ключи
    "response": {
        "id": "chatcmpl-BPXoIoWWg0kIsbzMASFCFonza3E4L",
        "object": "chat.completion",
         "created": 1745427866,
         "model": "gpt-4.1-mini-2025-04-14",
         "choices": 
          [
              {
                  "index": 0,
                   "message": {
                   "role": "assistant",
                   "content": "Hello! How can I assist you today?",
                   "refusal": null,
                   "annotations": []
             },
            "finish_reason": "stop"
          ]
     }, - тут лежит ответ полученный от модели

    "attempt_count": 1, - количество ретраев сделанный прокси
    "cost": 0.0000204, - стоимость запроса
    "cost_info": "model: gpt-4.1-mini-2025-04-14, input_tokens_price: 0.000400, output_tokens_price: 0.001600",
    "stats": {
        "provider": "api", - может быть api/soy...
        "user": "test_user", - пользователь, задавший запрос, опеределяется по soy_token
        "pool": "pool", если использовался eliza_pool - именно на него будет начислен usage, подробнее https://wiki.yandex-team.ru/eliza/quotasold/#eliza-pool-obshij-dostup-k-kvote-dlya-komandy
        "model_family": "gpt-4",
    }
}
```
Получение ответа AS IS (например для SDK)
    ИЛИ использовать префикс /raw (например: https://api.eliza.yandex.net/raw/{endpoint})
    ИЛИ использовать header: Need-Raw-Answer: true

Тогда ручка будет выдавать сырой ответ. Это работает абсолютно для всех моделей

Примеры использования SDK ищите на страничке соответствующего вендора

Получить список моделей

GET https://api.eliza.yandex.net/v1/models

Возвращает список доступных моделей

curl --request GET \
  --url https://api.eliza.yandex.net/v1/models \
  --header "authorization: OAuth $ELIZA_TOKEN"

 
Получить текущие лимиты

GET https://api.eliza.yandex.net/quota

Возвращает квоту по семействам моделей

Для пула указать header Ya-Pool: <your_pool>

curl --request GET \
  --url https://api.eliza.yandex.net/quota \
  --header "authorization: OAuth $ELIZA_TOKEN"

 
Получить данные по тратам

GET http://api.eliza.yandex.net/usage

Возвращает usage по семействам моделей

Для пула указать header Ya-Pool: <your_pool>

curl --request GET \
  --url https://api.eliza.yandex.net/usage \
  --header "authorization: OAuth $ELIZA_TOKEN"


Решение проблем:

При ошибке API Streaming Failed (Connection error), попробовать следующее:
Connection to api.eliza.yandex.net timed out

Если делаете запрос локально, то замените http на https: https://api.eliza.yandex.net.

Если с удаленной машинки - возможно недостаточно сетевых доступов.
SSL: CERTIFICATE_VERIFY_FAILED

Варианты решения:

    Отключить проверку SSL: в python3 requests.get(url, verify=False); curl - --insecure.

    Выполнить следующие команды:

    python3 -m certifi
    curl https://crls.yandex.net/allCAs.pem | tee -a $(python3 -m certifi)

    Попробовать это   Как исправить проблемы валидации серверных сертификатов в TLS/SSL-сервисах #vpython

Connection error

Выполнить следующие команды (взято отсюда):

sudo mkdir -p /etc/ssl/certs; sudo curl http://crls.yandex.net/allCAs.pem -o /etc/ssl/certs/YandexInternalCA.pem; echo export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/YandexInternalCA.pem >> ~/.zshrc; echo export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/YandexInternalCA.pem >> ~/.bashrc

Unauthorized (code 401)

Для прямых запросов необходима авторизация.
При прокачке через Niravana в additional_params нужно добавить "is_eliza_pumps": true.
Для SOY - в параметрах создания скачки нужно указать "is_eliza_pumps" : true

В кубике eliza_soy + в пуле eliza_default этот флажок проставляется автоматически.

Endpoints
Обновлено 30 декабря 2025, 18:24
Основной хост eliza api.eliza.yandex.net

После этого идет разделение по провайдерам (openai, anthropic и тд) - у каждого провайдера есть своя вики страничка
Для внутренних моделей основной endpoint /internal