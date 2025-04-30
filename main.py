from flask import Flask
from flasgger import Swagger
from app.task_routes import task_controller

from dotenv import load_dotenv


app = Flask(__name__, template_folder="./templates")
Swagger(app)

app.register_blueprint(task_controller)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
