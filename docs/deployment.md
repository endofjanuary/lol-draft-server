# 배포 가이드

## Render 배포 설정

### 환경 변수 설정

Render 대시보드에서 다음 환경 변수를 설정하세요:

#### 필수 환경 변수

```bash
# CORS 설정 - Netlify 도메인 허용
CORS_ORIGIN_REGEX=https://.*--lol-draft\.netlify\.app|https://lol-draft\.netlify\.app|http://localhost:\d+

# 환경 구분
ENVIRONMENT=production
```

#### 선택적 환경 변수

```bash
# 포트 설정 (Render에서 자동 설정되지만 명시적으로 설정 가능)
PORT=8000

# 로그 레벨
LOG_LEVEL=INFO
```

### CORS 패턴 설명

현재 설정된 정규식 패턴은 다음 도메인들을 허용합니다:

- `https://develop--lol-draft.netlify.app` - 개발 브랜치
- `https://feature-xyz--lol-draft.netlify.app` - 기능 브랜치들
- `https://lol-draft.netlify.app` - 프로덕션 도메인
- `http://localhost:3000` - 로컬 개발 환경
- `http://localhost:8080` - 로컬 개발 환경 (다른 포트)

### 배포 확인

배포 후 다음 엔드포인트로 서버 상태를 확인할 수 있습니다:

```
GET https://lol-draft-server.onrender.com/ping
```

응답에서 `cors_pattern` 필드를 통해 현재 적용된 CORS 패턴을 확인할 수 있습니다.

### 문제 해결

#### CORS 에러가 계속 발생하는 경우

1. Render 대시보드에서 환경 변수가 올바르게 설정되었는지 확인
2. 서버가 재배포되었는지 확인
3. 브라우저 캐시를 클리어하고 다시 시도
4. `/ping` 엔드포인트로 `cors_pattern` 값 확인

#### 새로운 도메인 추가가 필요한 경우

`CORS_ORIGIN_REGEX` 환경 변수를 수정하여 새로운 패턴을 추가:

```bash
# 예: 새로운 도메인 패턴 추가
CORS_ORIGIN_REGEX=https://.*--lol-draft\.netlify\.app|https://lol-draft\.netlify\.app|https://new-domain\.com|http://localhost:\d+
```
