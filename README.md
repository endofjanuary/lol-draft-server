# LoL Draft Server

리그 오브 레전드 밴픽 시뮬레이터의 백엔드 서버입니다.

## Documentation

- [시작하기](docs/getting-started.md) - 설치 및 실행 가이드
- [데이터 모델](docs/models.md) - 데이터 구조 및 검증 규칙
- [REST API 가이드](docs/api.md) - HTTP API 및 프론트엔드 통합 예제
- [Socket.IO 가이드](docs/socket.md) - 실시간 통신 가이드 및 예제
- [배포 가이드](docs/deployment.md) - Render 배포 및 CORS 설정 가이드
- [개발 예정 기능](docs/upcoming.md) - 로드맵 및 향후 개선 사항

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py --reload
```

자세한 사용법은 각 문서를 참고하세요.

## CORS 설정

서버는 환경 변수를 통해 CORS를 설정합니다:

```bash
# 환경 변수 설정 예시
CORS_ORIGIN_REGEX=https://.*--lol-draft\.netlify\.app|https://lol-draft\.netlify\.app|http://localhost:\d+
```

이 설정으로 다음 도메인들이 허용됩니다:

- Netlify의 모든 브랜치 도메인 (`https://branch--lol-draft.netlify.app`)
- 프로덕션 도메인 (`https://lol-draft.netlify.app`)
- 로컬 개발 환경 (`http://localhost:포트번호`)

## Render 배포 방법

1. GitHub에 코드 푸시:

   ```bash
   git add .
   git commit -m "Update CORS settings for Netlify deployment"
   git push origin main
   ```

2. Render 대시보드에서:

   - "New Web Service" 클릭
   - GitHub 저장소 연결
   - 빌드 및 시작 명령 설정:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python main.py`

3. 환경 변수 설정 (Render 대시보드의 "Environment" 탭):

   ```bash
   CORS_ORIGIN_REGEX=https://.*--lol-draft\.netlify\.app|https://lol-draft\.netlify\.app|http://localhost:\d+
   ENVIRONMENT=production
   ```

4. 배포 확인:

   - Health Check: `https://lol-draft-server.onrender.com/ping`
   - Swagger 문서: `https://lol-draft-server.onrender.com/docs`

5. 프론트엔드에서 API URL 설정:
   ```bash
   # .env.local
   NEXT_PUBLIC_API_URL=https://lol-draft-server.onrender.com
   ```

자세한 배포 가이드는 [배포 문서](docs/deployment.md)를 참고하세요.

## Railway 배포 방법 (대안)

1. GitHub에 코드 푸시:

   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. Railway 대시보드에서:

   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - 해당 저장소 선택
   - "Deploy Now" 클릭

3. 환경 변수 설정 (Railway 대시보드의 "Variables" 탭):

   - `CORS_ORIGIN_REGEX`: `https://.*--lol-draft\.netlify\.app|https://lol-draft\.netlify\.app|http://localhost:\d+`
   - 필요한 경우 추가 환경 변수 설정

4. 배포 확인:

   - Swagger 문서: `https://your-app.up.railway.app/docs`
   - API 엔드포인트: `https://your-app.up.railway.app/api/games`

5. 프론트엔드 Socket.IO 클라이언트 설정:
   ```javascript
   const socket = io("https://your-app.up.railway.app", {
     transports: ["websocket"],
     autoConnect: true,
   });
   ```
