import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from ultralytics import YOLO
from huggingface_hub import hf_hub_download
import logging
from transformers import logging as hf_logging
import easyocr


# Инициализация моделей (выполняется один раз при импорте)
def init_models():
    # 1. Глушим подробные логи HF
    hf_logging.set_verbosity_error()

    # 2. Скачиваем и загружаем модель YOLO
    model_path = hf_hub_download(
        repo_id="armvectores/yolov8n_handwritten_text_detection",
        filename="best.pt"
    )
    yolo_model = YOLO(model_path)
    print("yolo log")

    # 3. Загружаем модель и токенизатор TrOCR
    trocr_processor = TrOCRProcessor.from_pretrained("kazars24/trocr-base-handwritten-ru")
    trocr_model = VisionEncoderDecoderModel.from_pretrained("kazars24/trocr-base-handwritten-ru")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    trocr_model.to(device)

    reader = easyocr.Reader(['ru'], gpu=True, verbose=False)
    print("end log")

    return {
        "yolo_model": yolo_model,
        "trocr_processor": trocr_processor,
        "trocr_model": trocr_model,
        "device": device,
        "reader" : reader
    }

# Инициализируем модели сразу при импорте
models = init_models()