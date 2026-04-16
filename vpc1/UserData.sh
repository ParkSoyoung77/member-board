#!/bin/bash
# [단계 1] 로그 설정: 모든 실행 과정을 파일로 기록하여 디버깅 용이하게 함
exec > >(tee -a /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

# [단계 2] 환경 변수 설정 (소영님의 설정값 반영)
REGION="ap-south-2"
ACCOUNT_ID=""
ECR_REPO="st7/nginx"
IMAGE_TAG="latest"
ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_URL="${ECR_URL}/${ECR_REPO}:${IMAGE_TAG}"

echo "Starting UserData Script Execution..."

# [단계 3] 패키지 업데이트 및 도커 설치
dnf update -y
dnf install -y docker

# [단계 4] 도커 서비스 시작 및 활성화
systemctl start docker
systemctl enable docker

# [단계 5] ec2-user 권한 부여
usermod -aG docker ec2-user

# [단계 6] Docker Compose V2 설치
DOCKER_CONFIG=${DOCKER_CONFIG:-/usr/local/lib/docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# [단계 7] ECR 로그인 (인스턴스 프로파일에 ECR 권한이 있어야 함)
aws ecr get-login-password --region ${REGION} | \
docker login --username AWS --password-stdin ${ECR_URL}

# [단계 8] 기존 컨테이너 및 서비스 정리
docker stop nginx-container || true
docker rm nginx-container || true
systemctl stop nginx || true
systemctl disable nginx || true

# [단계 9] 이미지 Pull (ECR에서 최신 이미지 가져오기)
docker pull ${IMAGE_URL}

# [단계 10] 컨테이너 실행
docker run -d --name nginx-container \
-p 80:80 \
--restart always \
${IMAGE_URL}

# [단계 11] 정리 및 설치 확인
rm -rf /root/.docker/config.json
rm -rf /home/ec2-user/.docker/config.json
docker compose version
echo "UserData Script Execution Completed!"