#!/bin/bash
# 1. 환경 변수 설정
REGION="ap-south-2"
ACCOUNT_ID=""
ECR_REPO="st7/nginx"  
IMAGE_TAG="latest"
ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_URL="${ECR_URL}/${ECR_REPO}:${IMAGE_TAG}"

# 2. Log 파일 설정
exec > >(tee -a /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

# 3. ECR 로그인
aws ecr get-login-password --region ${REGION} | \
docker login --username AWS --password-stdin ${ECR_URL}

# 4. 기존 컨테이너 및 서비스 정리
docker stop nginx-container || true
docker rm nginx-container || true
systemctl stop nginx || true
systemctl disable nginx || true

# 5. 이미지 Pull (항상 최신 이미지를 가져옴)
docker pull ${IMAGE_URL}

# 6. 컨테이너 실행 (볼륨 마운트 제거)
docker run -d --name nginx-container \
-p 80:80 \
--restart always \
${IMAGE_URL}