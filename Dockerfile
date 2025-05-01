FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cnss

EXPOSE 8000

CMD ["python", "main.py"]
