import logging

from flask import Blueprint, render_template, request, jsonify
from werkzeug.datastructures import FileStorage
from flasgger import swag_from
import base64
from io import BytesIO
from PIL import Image


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
        # Проверка, что файл действительно является изображением
        img = Image.open(image)

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

        # Выводим размер изображения в консоль
        print(f"Image size: {img.size} pixels (width x height)")
        print(f"Image format: {img.format}")
        print(f"Image mode: {img.mode}")

        # Сохраняем изображение в память в формате PNG
        img_io = BytesIO()
        img.save(img_io, "PNG")
        img_io.seek(0)

        # Преобразуем изображение в строку Base64
        # img_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")

        # Формируем результат с изображением и данными
        result = {
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
                },
                {
                    "id": "Xk8Pq93mL1",
                    "type": "textarea",
                    "value": {
                        "x": 200.54,
                        "y": 346.86,
                        "text": ["Осинин"],
                        "width": 128.85,
                        "height": 33.44,
                        "rotation": 0,
                    },
                },
                {
                    "id": "T5hR72nBv9",
                    "type": "textarea",
                    "value": {
                        "x": 200.54,
                        "y": 380.86,
                        "text": ["Аркадьевич"],
                        "width": 150.85,
                        "height": 65.44,
                        "rotation": 0,
                    },
                },
            ]
        }
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error creating task with image: {e}")
        return jsonify({"error": str(e)}), 500
