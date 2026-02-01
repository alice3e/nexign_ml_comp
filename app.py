import io
import os
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from peft import PeftModel
import uvicorn

ADAPTER_PATH = os.getenv("MODEL_PATH", os.path.join("model_vlm", "weights"))
BASE_MODEL_ID = "Qwen/Qwen2-VL-2B-Instruct"

model = None
processor = None

async def load_model():
    global model, processor
    print(f"🔄 Запуск сервиса...")
    print(f"📂 Путь к весам: {ADAPTER_PATH}")
    
    print("⚙️ Загрузка базовой модели Qwen2-VL...")
    base_model = Qwen2VLForConditionalGeneration.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    if os.path.exists(ADAPTER_PATH):
        try:
            model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
            print(f"✅ Адаптеры успешно загружены!")
        except Exception as e:
            print(f"❌ Ошибка загрузки адаптеров: {e}")
            model = base_model
    else:
        print(f"⚠️ Путь {ADAPTER_PATH} не найден. Работаем на базовой модели.")
        model = base_model

    try:
        processor = AutoProcessor.from_pretrained(ADAPTER_PATH, min_pixels=256*28*28, max_pixels=512*28*28)
    except:
        processor = AutoProcessor.from_pretrained(BASE_MODEL_ID, min_pixels=256*28*28, max_pixels=512*28*28)
        
    print("🚀 Сервис готов!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_model()
    yield

app = FastAPI(title="BPMN Intelligent Service", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "BPMN Intelligent Service is running"}

@app.post("/predict")
async def predict_bpmn(file: UploadFile = File(...)):
    if not model or not processor:
        return {"error": "Model or processor not loaded"}
    
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as e:
        return {"error": f"Bad image: {e}"}
    
    prompt = "Ты эксперт по BPMN. Твоя задача — проанализировать диаграмму и создать структурированную таблицу Markdown с шагами алгоритма."
    
    # Альтернативный способ без qwen_vl_utils
    messages = [{
        "role": "user", 
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": prompt}
        ]
    }]
    
    # Простой способ - напрямую через процессор
    inputs = processor(
        messages,
        padding=True,
        return_tensors="pt"
    ).to(model.device)
    
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False
        )
    
    generated_ids_trimmed = generated_ids[:, inputs.input_ids.shape[1]:]
    output_text = processor.decode(generated_ids_trimmed[0], skip_special_tokens=True)
    
    return {"description": output_text}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)