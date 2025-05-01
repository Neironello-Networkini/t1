import logging

from flask import Blueprint, render_template, request, jsonify
from werkzeug.datastructures import FileStorage
from flasgger import swag_from
import base64
from datetime import datetime
import os
from io import BytesIO
from PIL import Image
from .image_processing import recognize_model

logger = logging.getLogger(__name__)
task_controller = Blueprint("task_controller", __name__)


@task_controller.route("/", methods=["GET"])
def view():
    """Страница загрузки и отображения результата."""
    try:
        return render_template("task.html"), 200
    except Exception as e:
        logger.error(f"Error rendering view: {e}")
        return render_template("task.html", init_error=str(e)), 500


@task_controller.route("/create", methods=["POST"])
@swag_from(
    {
        "tags": ["Tasks"],
        "consumes": ["multipart/form-data"],
        "parameters": [
            {
                "name": "image",
                "in": "formData",
                "type": "file",
                "required": True,
                "description": "Изображение для обработки (JPG, JPEG или PNG, макс. 50MB)",
            }
        ],
        "responses": {
            200: {
                "description": "Результат обработки изображения",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "results": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {
                                                "type": "string",
                                                "description": "Уникальный идентификатор элемента",
                                                "example": "cKN57KAHI2",
                                            },
                                            "type": {
                                                "type": "string",
                                                "description": "Тип элемента",
                                                "example": "textarea",
                                            },
                                            "value": {
                                                "type": "object",
                                                "properties": {
                                                    "x": {
                                                        "type": "number",
                                                        "description": "X-координата элемента",
                                                        "example": 603.54,
                                                    },
                                                    "y": {
                                                        "type": "number",
                                                        "description": "Y-координата элемента",
                                                        "example": 346.86,
                                                    },
                                                    "text": {
                                                        "type": "array",
                                                        "items": {"type": "string"},
                                                        "description": "Распознанный текст",
                                                        "example": ["Евгений"],
                                                    },
                                                    "width": {
                                                        "type": "number",
                                                        "description": "Ширина элемента",
                                                        "example": 128.85,
                                                    },
                                                    "height": {
                                                        "type": "number",
                                                        "description": "Высота элемента",
                                                        "example": 30.44,
                                                    },
                                                    "rotation": {
                                                        "type": "number",
                                                        "description": "Угол поворота",
                                                        "example": 0,
                                                    },
                                                },
                                            },
                                        },
                                    },
                                }
                            },
                            "example": {
                                "results": [
                                    {
                                        "id": "cKN57KAHI2",
                                        "type": "textarea",
                                        "value": {
                                            "x": 603.54,
                                            "y": 346.86,
                                            "text": ["Евгений"],
                                            "width": 128.85,
                                            "height": 30.44,
                                            "rotation": 0,
                                        },
                                    }
                                ]
                            },
                        }
                    }
                },
            },
            400: {
                "description": "Ошибка: Файл не передан, неподдерживаемый формат файла, файл не является изображением, превышен максимальный размер"
            },
            500: {"description": "Внутренняя ошибка сервера при обработке изображения"},
        },
    }
)
def create_task():
    """
    Принимает multipart/form-data с полем 'image',
    отдаёт JSON-результат обработки и обновлённую картинку.
    """
    image: FileStorage = request.files.get("image")
    if not image:
        return jsonify({"error": "Файл не передан"}), 400

    # Проверка расширения файла
    allowed_extensions = {"jpg", "jpeg", "png"}
    filename = image.filename.lower()
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return (
            jsonify(
                {
                    "error": "Неподдерживаемый формат файла. Разрешены только JPG, JPEG и PNG"
                }
            ),
            400,
        )

    try:
        # Открываем изображение и проверяем его
        img = Image.open(image.stream)
        
        # Проверка формата изображения
        if img.format not in ["JPEG", "PNG"]:
            return (
                jsonify(
                    {
                        "error": f"Неподдерживаемый формат изображения: {img.format}. Разрешены только JPEG и PNG"
                    }
                ),
                400,
            )

        # Выводим информацию об изображении
        print(f"Image size: {img.size} pixels (width x height)")
        print(f"Image format: {img.format}")
        print(f"Image mode: {img.mode}")

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f"{timestamp}.png"  # всегда сохраняем как PNG
    
        # Сохраняем изображение
        save_path = os.path.join('images', filename)
        img.save(save_path, format='PNG')

        # Формируем результат с изображением и данными
        result = recognize_model(save_path)
        os.remove(save_path)
        return jsonify(result), 200
        
    except IOError as e:
        logger.error(f"Invalid image file: {e}")
        return jsonify({"error": "Файл не является корректным изображением"}), 400
    except Exception as e:
        logger.error(f"Error creating task with image: {e}")
        return jsonify({"error": str(e)}), 500