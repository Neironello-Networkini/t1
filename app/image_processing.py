import os
from datetime import datetime
import cv2
import numpy as np
import glob
import re
import torch
import shutil
from PIL import Image
from .models import models

def process_image(image_path, base_output_dir="."):
    output_crops_dir = None

    # --- Создание папки вывода ---
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
    output_crops_dir = os.path.join(base_output_dir, f"output_{timestamp}")
    os.makedirs(output_crops_dir, exist_ok=True)

    # --- Инициализация EasyOCR ---
    reader = models["reader"]

    # --- Загрузка изображения ---
    image = cv2.imread(image_path)

    # --- Детекция текста ---
    results = reader.readtext(image, detail=1, paragraph=False)

    # --- Обработка результатов ---
    all_metadata = []
    crop_id_counter = 1

    for (bbox, text, conf) in results:
        polygon_points = np.array(bbox, dtype=np.int32)
        x, y, w, h = cv2.boundingRect(polygon_points)

        if w <= 1 or h <= 1:
            continue  # Пропускаем слишком маленькие

        crop_image = image[y:y + h, x:x + w]
        if crop_image.size == 0:
            continue  # Пропускаем пустые

        # Сохранить кроп в созданную папку
        crop_filename = f"{crop_id_counter}.png"
        crop_filepath = os.path.join(output_crops_dir, crop_filename)
        write_status = cv2.imwrite(crop_filepath, crop_image)

        # Подготовить метаданные (БЕЗ rotation, как в исходном коде)
        coordinates_for_json = [[int(p[0]), int(p[1])] for p in bbox]

        metadata_item = {
            "id": str(crop_id_counter),
            "value": {
                "coordinates": coordinates_for_json,
                "text": [],  # Пустой список, как в исходном коде
            }
        }
        all_metadata.append(metadata_item)
        crop_id_counter += 1

    # --- Возврат результата ---
    return output_crops_dir, all_metadata


def classificator_model(photo_user):
    def is_handwritten(img, conf_thresh: float = 0.4) -> bool:
        results = models["yolo_model"].predict(source=img, conf=conf_thresh, verbose=False)[0]
        return results.boxes.shape[0] > 0  # модель нашла по крайней мере один фрагмент рукописного текста

    def extract_number(filename: str) -> str | None:
        # Берём только имя файла, отбрасывая путь
        base = os.path.basename(filename)  # '70.png'
        name, _ = os.path.splitext(base)  # ('70', '.png')
        match = re.search(r'(\d+)$', name)  # ищем цифры в конце строки
        return match.group(1) if match else None

    def set_is_handwritten(data: list[dict], target_id: str, handwritten: int) -> bool:
        for item in data:
            if item.get('id') == target_id:
                val = item.setdefault('value', {})
                # чтобы гарантировать, что is_handwritten идёт после text,
                # соберём OrderedDict в нужном порядке:
                coords = val.get('coordinates')
                text = val.get('text')
                # перестроим словарь в нужном порядке
                new_val = {}
                if coords is not None:
                    new_val['coordinates'] = coords
                if text is not None:
                    new_val['text'] = text
                new_val['is_handwritten'] = int(handwritten)
                # заменяем старый value
                item['value'] = new_val
                return True
        return False

    path_to_crops, data = process_image(photo_user)

    for img_path in glob.glob(f"{path_to_crops}/*.png"):
        # ―― читаем цветное
        crop = Image.open(img_path)

        id_img = extract_number(img_path)
        # print(f"id_img: {id_img}")
        if is_handwritten(crop):
            set_is_handwritten(data, id_img, 1)
        else:
            set_is_handwritten(data, id_img, 0)

    return data, path_to_crops


def recognize_model(image_path):
    data, path_to_crops = classificator_model(image_path)
    new_data = []
    for item in data:
        img_path = f"{path_to_crops}/{item['id']}.png"

        # 3. Перебираем все PNG-файлы в папке
        img = Image.open(img_path)

        # print(f"\nФайл: {img_path}")
        # display(img)

        # 4. Преобразуем картинку для модели
        inputs = models["trocr_processor"](
            img,
            return_tensors="pt",
            do_resize=True,
            do_normalize=True
        ).pixel_values.to(models["device"])

        # 5. Генерируем результат
        with torch.no_grad():
            generated_ids = models["trocr_model"].generate(
                inputs,
                early_stopping=True
            )

        # 6. Декодируем в текст
        text = models["trocr_processor"].batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0].strip()

        # 3) Строим новый словарь и добавляем в результирующий список
        new_item = {
            'id': item['id'],
            'value': {
                'coordinates': item['value']['coordinates'],
                'text': text,
                'is_handwritten': item['value']['is_handwritten']
            }
        }
        new_data.append(new_item)

        # print(f"Распознанный текст: {text}")

    shutil.rmtree(path_to_crops)

    return {"results" : new_data}