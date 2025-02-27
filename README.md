# League of Legends Draft Webpage - Server

---

## Getting Started

### Prerequisites

- Python 3.8 이상
- pip (Python 패키지 관리자)

### Installation & Setup

1. 필요한 패키지 설치:

```bash
pip install -r requirements.txt
```

### Running the Server

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

서버가 실행되면 다음 주소에서 접근 가능합니다:

- 개발 환경: http://127.0.0.1:8000
- API 문서 (Swagger UI): http://127.0.0.1:8000/docs
- API 문서 (ReDoc): http://127.0.0.1:8000/redoc

---

## Models

### Game

| Name      | Type   | Description                    |
| --------- | ------ | ------------------------------ |
| gameCode  | string | 8개의 16진수로 이루어진 문자열 |
| createdAt | number | 생성된 시점의 nanosecond값     |

```json
// example
{
  "gameCode": "9876abcd",
  "createdAt": 1740663081873
}
```

### GameSetting

| Name        | Type    | Description                                    |
| ----------- | ------- | ---------------------------------------------- |
| version     | string  | 리그오브레전드 패치버전 (ex. "14.10.1")        |
| draftType   | string  | "tournament" / "hardFearless" / "softFearless" |
| playerType  | string  | "single" / "1v1" / "5v5"                       |
| matchFormat | string  | "bo1" / "bo3" / "bo5"                          |
| timeLimit   | boolean | true / false                                   |

```json
// example
{
  "version": "14.10.1",
  "draftType": "tournament",
  "playerType": "5v5",
  "matchFormat": "bo3",
  "timeLimit": true
}
```

### GameStatus

| Name          | Type     | Description                                     |
| ------------- | -------- | ----------------------------------------------- |
| phase         | number   | 0~21 사이의 정수 (현재 진행중인 phase)          |
| blueTeamName  | string   | 블루팀 이름 (default: "Blue")                   |
| redTeamName   | string   | 레드팀 이름 (default: "Red")                    |
| lastUpdatedAt | number   | 데이터가 마지막으로 수정된 시점의 nanosecond 값 |
| phaseData     | string[] | 22개의 문자열을 담은 배열 (각 phase별 데이터)   |
| setNumber     | number   | 1~5사이의 정수 (현재 진행중인 세트 번호)        |

```json
// example
{
  "phase": 12,
  "blueTeamName": "T1",
  "redTeamName": "GEN",
  "lastUpdatedAt": 1740663081873,
  "phaseData": [
    "ready", // phase 0: 게임 시작 전 준비상태
    "266", // phase 1: 블루1밴 (아트록스)
    "236", // phase 2: 레드1밴
    "875", // phase 3: 블루2밴
    "875", // phase 4: 레드2밴
    "234", // phase 5: 블루3밴
    "61", // phase 6: 레드3밴
    "122", // phase 7: 블루1픽
    "157", // phase 8: 레드1픽
    "51", // phase 9: 레드2픽
    "51", // phase 10: 블루2픽
    "25", // phase 11: 블루3픽
    "102", // phase 12: 레드3픽
    "", // phase 13: 레드4밴
    "", // phase 14: 블루4밴
    "", // phase 15: 레드5밴
    "", // phase 16: 블루5밴
    "", // phase 17: 레드4픽
    "", // phase 18: 블루4픽
    "", // phase 19: 블루5픽
    "", // phase 20: 레드5픽
    "" // phase 21: 승리 팀
  ],
  "setNumber": 1
}
```

### GameResult

| Name      | Type       | Description                               |
| --------- | ---------- | ----------------------------------------- |
| blueScore | number     | 0~3 사이의 정수 (블루팀의 누적 승리 횟수) |
| redScore  | number     | 0~3 사이의 정수 (레드팀의 누적 승리 횟수) |
| results   | string[][] | 최대 5개의 string List를 담은 2중 배열    |

```json
// example
{
  "blueScore": 2,
  "redScore": 1,
  "results": [
    [
      "ready",
      "266",
      "236",
      // ...생략...
      "blue" // 첫번째 세트 블루팀 승리
    ],
    [
      "ready",
      "122",
      "157",
      // ...생략...
      "red" // 두번째 세트 레드팀 승리
    ],
    [
      "ready",
      "875",
      "234",
      // ...생략...
      "blue" // 세번째 세트 블루팀 승리
    ]
  ]
}
```

<details>
<summary>Phase 상세 설명</summary>

각 phase는 아래 상황을 의미하며, 0에서 21까지 순차적으로 진행됩니다.
bo3이나 bo5에서 다음 세트로 넘어갈 때마다 phase는 21에서 0으로 초기화됩니다.

- phase 0: 게임 세트 시작전 대기상황

  - 1인 모드: "" (대기 상황 없이 바로 시작)
  - 1v1 모드: "xvy" 형식 (x는 블루팀 준비완료 인원, y는 레드팀 준비완료 인원)
    - 예시: "1v0" (블루팀 1명은 준비완료, 레드팀 1명은 대기중)
  - 5v5 모드: "xxxxxvyyyyy" 형식 (x는 블루팀 각 포지션별 준비상태, y는 레드팀 각 포지션별 준비상태)
    - 0: 해당 포지션 플레이어 대기중
    - 1: 해당 포지션 플레이어 준비완료
    - 예시: "01100v00010" (블루팀 2,3번째 플레이어와 레드팀 4번째 플레이어만 준비완료)

- phase 1-6: 1차 밴픽 페이즈 (각 팀 3밴)
  - 1: 블루1밴
  - 2: 레드1밴
  - 3: 블루2밴
  - 4: 레드2밴
  - 5: 블루3밴
  - 6: 레드3밴
- phase 7-12: 1차 픽 페이즈
  - 7: 블루1픽
  - 8: 레드1픽
  - 9: 레드2픽
  - 10: 블루2픽
  - 11: 블루3픽
  - 12: 레드3픽
- phase 13-16: 2차 밴픽 페이즈 (각 팀 2밴)
  - 13: 레드4밴
  - 14: 블루4밴
  - 15: 레드5밴
  - 16: 블루5밴
- phase 17-20: 2차 픽 페이즈
  - 17: 레드4픽
  - 18: 블루4픽
  - 19: 블루5픽
  - 20: 레드5픽
- phase 21: 게임 세트 종료 후 승리 팀 기록 ("blue" 또는 "red")

</details>

<details>
<summary>GameResult 상세 설명</summary>

results 배열의 각 요소는 GameStatus의 phaseData와 동일한 형식을 가지며, 게임 세트가 종료되어 승리 팀이 확정되면 해당 세트의 전체 phase 데이터가 저장됩니다.

예시:

- 3번째 게임 세트가 블루팀의 승리로 확정된 경우
  1. GameStatus의 현재 phaseData를 results[2]에 저장
  2. blueScore 값을 1 증가
  3. 다음 세트 진행을 위해 GameStatus의 phase를 0으로 초기화

</details>

---

### Client

| Name     | Type   | Description                                              |
| -------- | ------ | -------------------------------------------------------- |
| socketId | string | Socket.IO가 생성한 고유 클라이언트 ID                    |
| gameCode | string | 접속한 게임의 코드                                       |
| position | string | 클라이언트의 포지션 ("spectator" / "blue1-5" / "red1-5") |
| joinedAt | number | 게임 접속 시점의 nanosecond값                            |

```json
// example
{
  "socketId": "wYD7MX_3qPxLvxlWAAAB",
  "gameCode": "12345678",
  "position": "blue1",
  "joinedAt": 1740663081873
}
```

<details>
<summary>Position 상세 설명</summary>

position은 다음 값들 중 하나를 가집니다:

- "spectator": 관전자
- "blue1": 블루팀 1번 플레이어
- "blue2": 블루팀 2번 플레이어
- "blue3": 블루팀 3번 플레이어
- "blue4": 블루팀 4번 플레이어
- "blue5": 블루팀 5번 플레이어
- "red1": 레드팀 1번 플레이어
- "red2": 레드팀 2번 플레이어
- "red3": 레드팀 3번 플레이어
- "red4": 레드팀 4번 플레이어
- "red5": 레드팀 5번 플레이어

playerType에 따른 position 제한:

- "single": position은 항상 "all" (블루팀과 레드팀 모두를 담당)
- "1v1": "blue1"과 "red1"만 사용
- "5v5": 모든 포지션 사용 가능

</details>

---

## API Documentation

### Create Game

새로운 게임을 생성하고 초기화합니다.

- **URL**: `/games`
- **Method**: `POST`
- **Request Body**: GameSetting

```json
// Request Body Example
{
  "version": "14.10.1",
  "draftType": "tournament",
  "playerType": "5v5",
  "matchFormat": "bo3",
  "timeLimit": true
}
```

- **Response**: Game

```json
// Response Example (200 OK)
{
  "gameCode": "a1b2c3d4",
  "createdAt": 1740663081873
}
```

- **Error Responses**:
  - `400 Bad Request`: 잘못된 request body 형식
    ```json
    {
      "error": "Invalid request body: matchFormat must be one of: bo1, bo3, bo5"
    }
    ```
  - `500 Internal Server Error`: 서버 오류
    ```json
    {
      "error": "Failed to create game"
    }
    ```

### Get Game Information

게임 코드에 해당하는 게임의 모든 정보를 조회합니다.

- **URL**: `/games/{game_code}`
- **Method**: `GET`
- **URL Parameters**:

  - `game_code`: 8자리 게임 코드

- **Response**: GameInfo

```json
// Response Example (200 OK)
{
  "game": {
    "gameCode": "a1b2c3d4",
    "createdAt": 1740663081873
  },
  "settings": {
    "version": "14.10.1",
    "draftType": "tournament",
    "playerType": "5v5",
    "matchFormat": "bo3",
    "timeLimit": true
  },
  "status": {
    "phase": 0,
    "blueTeamName": "Blue",
    "redTeamName": "Red",
    "lastUpdatedAt": 1740663081873,
    "phaseData": [
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      ""
    ],
    "setNumber": 1
  }
}
```

- **Error Responses**:
  - `404 Not Found`: 게임을 찾을 수 없음
    ```json
    {
      "error": "Game not found: a1b2c3d4"
    }
    ```
  - `500 Internal Server Error`: 서버 오류
    ```json
    {
      "error": "Failed to get game info"
    }
    ```
