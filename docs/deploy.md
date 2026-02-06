# Docker 배포 가이드 (GCR + GCP VM)

## 사전 준비
- GCP 프로젝트 및 GCR 사용 가능
- VM에 Docker + Docker Compose 설치
- VM에 레포지토리 클론 (예: `/opt/resumaker-backend`)

## VM 설정
1) 레포지토리 클론
```
git clone <REPO_URL> /opt/resumaker-backend
```

2) `.env` 작성 (VM 내부) - 자동 생성 방식 사용 시 생략 가능
```
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=your.domain.com,api.your.domain.com
SECURE_SSL_REDIRECT=True
CSRF_TRUSTED_ORIGINS=https://your.domain.com,https://api.your.domain.com
GEMINI_API_KEY=...
GCP_PROJECT_ID=your-gcp-project-id
APP_NAME=resumaker-backend
```

3) GCR 로그인(택1)
- VM에 `gcloud`가 있다면:
```
gcloud auth configure-docker gcr.io
```
- 또는 서비스 계정 키 사용:
```
export GCP_SA_KEY='{"type":"service_account", ... }'
echo "$GCP_SA_KEY" | docker login -u _json_key --password-stdin https://gcr.io
```
 
## GitHub Actions에서 자동 로그인
- `deploy.yml`이 SSH 단계에서 `GCP_SA_KEY`를 VM으로 전달해 `deploy.sh`가 자동 로그인합니다.
- 따라서 VM에 별도 `gcloud login`을 해두지 않아도 됩니다.

## GitHub Secrets
- `GCP_PROJECT_ID`: GCP 프로젝트 ID
- `GCP_SA_KEY`: 서비스 계정 JSON 키 (GCR push 권한 필요)
- `APP_NAME`: 이미지 이름 (예: `resumaker-backend`)
- `SSH_HOST`: VM 외부 IP/도메인
- `SSH_USER`: VM 접속 유저
- `SSH_KEY`: SSH 개인키
- `APP_DIR`: VM 내 레포지토리 경로 (예: `/opt/resumaker-backend`)
- `.env 자동 생성용`: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `SECURE_SSL_REDIRECT`, `CSRF_TRUSTED_ORIGINS`, `GEMINI_API_KEY`

## 배포 흐름
1) `dev` 브랜치에 push
2) GitHub Actions가 GCR에 이미지 빌드/푸시
3) SSH로 VM 접속 후 `scripts/deploy.sh` 실행
4) VM에서 `docker compose pull && docker compose up -d`
