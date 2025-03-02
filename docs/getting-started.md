# Getting Started

## Prerequisites

- Python 3.8 이상
- pip (Python 패키지 관리자)

## Installation & Setup

1. 필요한 패키지 설치:

```bash
pip install -r requirements.txt
```

## Running the Server

다음 명령어들을 통해 서버를 실행할 수 있습니다:

1. 개발 모드로 실행 (자동 리로드):

```bash
python run.py --reload
```

2. 특정 호스트와 포트로 실행:

```bash
python run.py --host 0.0.0.0 --port 8080
```

3. 프로덕션 모드로 실행:

```bash
python run.py --host 0.0.0.0
```

4. 로그 레벨 설정:

```bash
python run.py --reload --log-level debug
```

## Access Points

서버가 실행되면 다음 주소에서 접근 가능합니다:

- 개발 환경: http://127.0.0.1:8000
- API 문서 (Swagger UI): http://127.0.0.1:8000/docs
- API 문서 (ReDoc): http://127.0.0.1:8000/redoc
