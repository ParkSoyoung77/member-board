# 베이스 이미지: 요청하신 python:3.11-slim 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 현재 폴더의 모든 내용(app 폴더, .env 등)을 복사
COPY . .

# FastAPI 실행 (main.py가 app 폴더 안에 있으므로 app.main:app으로 실행)
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]