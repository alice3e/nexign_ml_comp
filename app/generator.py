import json
import requests
import streamlit as st
class LLMTableGenerator:
    def __init__(self, model_name="llama3.2", base_url="http://localhost:11434/api"):
        self.model_name = model_name
        self.base_url = base_url

    def generate_table(self, graph_data):
        """
        Преобразует данные графа в итоговую Markdown-таблицу.
        """
        # 1. Подготовка данных: убираем лишнее, оставляем суть для контекста
        nodes_simplified = []
        for n in graph_data.get("nodes", []):
            if n.get("text") and len(n["text"].strip()) > 1:
                nodes_simplified.append({
                    "id": n["id"],
                    "role": n.get("role", "Не определена"),
                    "action": n["text"].replace("\n", " ")
                })

        # Если данных нет, возвращаем сообщение
        if not nodes_simplified:
            return "Ошибка: На схеме не удалось распознать текст действий."

        # 2. Формируем промпт
        # Мы просим модель не просто скопировать, а выступить в роли бизнес-аналитика
        prompt = f"""
        Ты — ведущий бизнес-аналитик. Твоя задача — составить таблицу регламента процесса на основе данных OCR с BPMN-схемы.
        
        Входные данные (могут содержать опечатки OCR):
        {json.dumps(nodes_simplified, ensure_ascii=False)}
        
        Инструкции:
        1. Исправь опечатки в тексте (например, 'Принятне' -> 'Принятие', 'технологин' -> 'технологии').
        2. Если одна и та же роль написана по-разному из-за ошибок OCR, приведи её к единому стандарту.
        3. Удали явные дубликаты действий.
        4. Сформируй таблицу Markdown со столбцами: № | Наименование действия | Роль.
        5. Отвечай ТОЛЬКО готовой таблицей, без лишних вступлений и пояснений.
        """
        

        # 3. Запрос к Ollama
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Низкая температура для точности
                        "top_p": 0.9
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get('response', "Ошибка: Модель вернула пустой ответ.")
        
        except requests.exceptions.RequestException as e:
            return f"Ошибка связи с Ollama: {str(e)}. Убедитесь, что сервер Ollama запущен."

def ensure_model_exists(model_name="llama3.2", base_url="http://localhost:11434/api"):
    """
    Проверяет наличие модели и скачивает её через API Ollama с выводом статуса в Streamlit.
    """
    try:
        # Проверка списка моделей
        check_res = requests.get(f"{base_url}/tags")
        existing_models = [m['name'] for m in check_res.json().get('models', [])]
        
        if any(model_name in m for m in existing_models):
            return True

        # Если модели нет, начинаем загрузку
        st.info(f"Загрузка модели {model_name}... Это нужно сделать только один раз.")
        progress_bar = st.progress(0)
        
        with requests.post(f"{base_url}/pull", json={"name": model_name}, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    status = json.loads(line)
                    # Обновление прогресса, если Ollama отдает цифры
                    if 'completed' in status and 'total' in status:
                        progress = status['completed'] / status['total']
                        progress_bar.progress(progress)
                    elif status.get('status') == 'success':
                        progress_bar.progress(1.0)
        return True
        
    except Exception as e:
        st.error(f"Не удалось проверить/загрузить модель: {e}")
        return False