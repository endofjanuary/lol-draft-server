FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 셸 형식으로 CMD 수정 - 환경 변수 확장이 가능합니다
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
