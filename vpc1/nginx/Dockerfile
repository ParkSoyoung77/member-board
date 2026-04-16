# 베이스 이미지: 요청하신 nginx:1.26-alpine 사용
FROM nginx:1.26-alpine

# 1. 기존 기본 설정 삭제
RUN rm /etc/nginx/conf.d/default.conf

# 2. default.conf 복사 (Dockerfile과 같은 층에 있으므로 바로 복사)
COPY default.conf /etc/nginx/conf.d/

# 3. html 폴더 복사 (Dockerfile과 같은 층에 있는 html 폴더 전체 복사)
COPY ./html /usr/share/nginx/html

# 80 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]