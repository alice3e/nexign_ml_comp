import json
import re
import requests
import sys

# Настройки
MODEL_NAME = "llama3.2"  # Легкая и быстрая модель
OLLAMA_URL = "http://localhost:11434/api"

def ensure_model_exists(model_name):
    """Проверяет наличие модели и скачивает её, если нужно."""
    print(f"🔎 Проверка модели {model_name}...")
    
    # Проверяем список установленных моделей
    response = requests.get(f"{OLLAMA_URL}/tags")
    models = [m['name'] for m in response.json().get('models', [])]
    
    if any(model_name in m for m in models):
        print(f"✅ Модель {model_name} уже установлена.")
        return

    print(f"📥 Модель {model_name} не найдена. Начинаю скачивание...")
    
    # Запрос на скачивание (stream=True для отслеживания прогресса)
    payload = {"name": model_name}
    with requests.post(f"{OLLAMA_URL}/pull", json=payload, stream=True) as r:
        for line in r.iter_lines():
            if line:
                status = json.loads(line)
                if 'completed' in status and 'total' in status:
                    percent = (status['completed'] / status['total']) * 100
                    print(f"\rЗагрузка: {percent:.2f}%", end="")
                elif 'status' in status:
                    print(f"\rСтатус: {status['status']}", end="")
    print(f"\n✅ Модель {model_name} успешно загружена!")

def extract_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'```json\s+(.*?)\s+```', content, re.DOTALL)
    return json.loads(match.group(1)) if match else None

def generate_table(json_data):
    # Очищаем данные от лишних координат для экономии контекста
    nodes = [{"role": n.get("role"), "text": n.get("text")} 
             for n in json_data.get("nodes", []) if n.get("text")]

    prompt = f"""
    Дан список элементов BPMN процесса (после OCR). 
    Исправь опечатки, удали дубликаты и составь красивую таблицу Markdown.
    
    Колонки: №, Наименование действия, Роль.
    
    Данные:
    {json.dumps(nodes, ensure_ascii=False)}
    """

    print("🧠 Генерация таблицы...")
    response = requests.post(f"{OLLAMA_URL}/generate", json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })
    return response.json().get('response')

# --- ЗАПУСК ---
if __name__ == "__main__":
    INPUT_FILE = "graph_result.md"
    
    try:
        # 1. Проверяем Ollama
        try:
            requests.get(OLLAMA_URL)
        except:
            print("❌ Ошибка: Ollama не запущена. Запустите приложение Ollama и повторите.")
            sys.exit(1)

        # 2. Скачиваем модель если надо
        ensure_model_exists(MODEL_NAME)

        # 3. Обрабатываем файл
        data = extract_json(INPUT_FILE)
        if data:
            result = generate_table(data)
            with open("table_result.md", "w", encoding="utf-8") as f:
                f.write(result)
            print("🚀 Готово! Результат сохранен в table_result.md")
        else:
            print("❌ JSON в файле не найден.")
            
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")