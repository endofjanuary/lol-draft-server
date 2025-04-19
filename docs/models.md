# Data Models

> 이 문서는 LoL Draft Server에서 사용되는 데이터 모델과 구조를 설명합니다. 각 모델의 필드, 제약조건 및 유효성 검사 규칙을 제공합니다.

## 최근 변경사항

- `version` 기본값이 "13.24.1"로 변경됨
- `Client` 모델을 딕셔너리 기반 클래스로 변경하여 유연성 향상
- `Client` 모델에 `champion`, `isConfirmed`, `clientId` 필드 추가
- 응답 형식에서 `gameCode` 필드가 `code`로 변경됨
- 오류 응답에 한글 메시지 추가

## Game

| Name      | Type   | Description                           |
| --------- | ------ | ------------------------------------- |
| code      | string | 6자의 알파벳과 숫자로 이루어진 문자열 |
| createdAt | number | 생성된 시점의 timestamp 값            |
| gameName  | string | 게임 이름 (기본값: "New Game")        |

## GameSetting

| Name        | Type         | Description                                         |
| ----------- | ------------ | --------------------------------------------------- |
| version     | string       | 리그오브레전드 패치버전 (default: "13.24.1")        |
| draftType   | string       | "tournament" / "hardFearless" / "softFearless"      |
| playerType  | string       | "single" / "1v1" / "5v5"                            |
| matchFormat | string       | "bo1" / "bo3" / "bo5"                               |
| timeLimit   | boolean      | true / false                                        |
| globalBans  | string array | 게임 전체에서 사용 불가능한 챔피언 목록 (선택 사항) |
| bannerImage | string       | base64로 인코딩된 배너 이미지 (선택 사항)           |

## GameStatus

| Name          | Type     | Description                                    |
| ------------- | -------- | ---------------------------------------------- |
| phase         | number   | 0~21 사이의 정수 (현재 진행중인 phase)         |
| blueTeamName  | string   | 블루팀 이름 (default: "Blue")                  |
| redTeamName   | string   | 레드팀 이름 (default: "Red")                   |
| lastUpdatedAt | number   | 데이터가 마지막으로 수정된 시점의 timestamp 값 |
| phaseData     | string[] | 22개의 문자열을 담은 배열 (각 phase별 데이터)  |
| setNumber     | number   | 1~5사이의 정수 (현재 진행중인 세트 번호)       |

## GameResult

| Name      | Type       | Description                               |
| --------- | ---------- | ----------------------------------------- |
| blueScore | number     | 0~3 사이의 정수 (블루팀의 누적 승리 횟수) |
| redScore  | number     | 0~3 사이의 정수 (레드팀의 누적 승리 횟수) |
| results   | string[][] | 최대 5개의 string List를 담은 2중 배열    |

## Client

| Name        | Type    | Description                                              |
| ----------- | ------- | -------------------------------------------------------- |
| clientId    | string  | 클라이언트 식별을 위한 고유 ID (소켓 ID와 동일)          |
| gameCode    | string  | 접속한 게임의 코드                                       |
| position    | string  | 클라이언트의 포지션 ("spectator" / "blue1-5" / "red1-5") |
| joinedAt    | number  | 게임 접속 시점의 timestamp 값                            |
| nickname    | string  | 클라이언트의 닉네임                                      |
| isReady     | boolean | 클라이언트의 준비 상태 (true: 준비완료, false: 대기중)   |
| isHost      | boolean | 호스트 여부 (첫 번째 참가자가 호스트가 됨)               |
| champion    | string  | 현재 선택한 챔피언 ID (null인 경우 선택하지 않음)        |
| isConfirmed | boolean | 챔피언 선택 확정 여부                                    |

## 클라이언트 응답 모델

### Game 생성 응답

```json
{
  "code": "AB12CD",
  "createdAt": 1668457862000
}
```

### Game 정보 응답

```json
{
  "code": "AB12CD",
  "settings": {
    "version": "13.24.1",
    "draftType": "tournament",
    "playerType": "5v5",
    "matchFormat": "bo3",
    "timeLimit": true,
    "globalBans": ["Yuumi", "Zed"],
    "bannerImage": "data:image/png;base64,..."
  },
  "status": {
    "phase": 0,
    "blueTeamName": "블루팀",
    "redTeamName": "레드팀",
    "lastUpdatedAt": 1668457862000,
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
  },
  "clients": [
    {
      "nickname": "Player1",
      "position": "blue1",
      "isReady": true,
      "isHost": true,
      "champion": null,
      "isConfirmed": false,
      "clientId": "socket-id-1"
    }
  ],
  "blueScore": 0,
  "redScore": 0
}
```

### 오류 응답

```json
{
  "detail": "게임을 찾을 수 없습니다: AB1234",
  "status_code": 404
}
```

## Phase 상세 설명

Phase는 0에서 21까지 순차적으로 진행되며, 각 단계는 다음을 의미합니다:

### Phase 0: 게임 세트 시작전 대기상황

- 1인 모드: "" (대기 상황 없이 바로 시작)
- 1v1 모드: "xvy" 형식
- 5v5 모드: "xxxxxvyyyyy" 형식

### Phase 1-6: 1차 밴픽 페이즈 (각 팀 3밴)

1. 블루1밴
2. 레드1밴
3. 블루2밴
4. 레드2밴
5. 블루3밴
6. 레드3밴

### Phase 7-12: 1차 픽 페이즈

7. 블루1픽
8. 레드1픽
9. 레드2픽
10. 블루2픽
11. 블루3픽
12. 레드3픽

### Phase 13-16: 2차 밴픽 페이즈 (각 팀 2밴)

13. 레드4밴
14. 블루4밴
15. 레드5밴
16. 블루5밴

### Phase 17-20: 2차 픽 페이즈

17. 레드4픽
18. 블루4픽
19. 블루5픽
20. 레드5픽

### Phase 21: 게임 세트 종료

- "blue" 또는 "red" 값으로 승리 팀 기록

## Validation Rules

### GameSetting

- version: 형식 "xx.xx.xx" (예: "13.24.1")
- draftType: "tournament", "hardFearless", "softFearless" 중 하나
- playerType: "single", "1v1", "5v5" 중 하나
- matchFormat: "bo1", "bo3", "bo5" 중 하나
- timeLimit: boolean

### GameStatus

- phase: 0-21 사이의 정수
- blueTeamName, redTeamName: 최대 20자
- phaseData: 정확히 22개의 요소를 가진 배열
- setNumber: 1-5 사이의 정수

### Position Rules

playerType에 따른 유효한 position 값:

1. single 모드

   - 유효값: "all"

2. 1v1 모드

   - 유효값: "blue1", "red1", "spectator"

3. 5v5 모드
   - 블루팀: "blue1" ~ "blue5"
   - 레드팀: "red1" ~ "red5"
   - 관전자: "spectator"

## Examples

### 토너먼트 모드 5v5 게임

```json
{
  "version": "13.24.1",
  "draftType": "tournament",
  "playerType": "5v5",
  "matchFormat": "bo3",
  "timeLimit": true
}
```

### 1v1 게임

```json
{
  "version": "13.24.1",
  "draftType": "hardFearless",
  "playerType": "1v1",
  "matchFormat": "bo1",
  "timeLimit": false
}
```

## 코드 구현

### GameSetting 클래스

```python
class GameSetting(BaseModel):
    version: str = "13.24.1"
    draftType: str = "tournament"
    playerType: str = "1v1"  # "single", "1v1", "5v5"
    matchFormat: str = "bo1"  # "bo1", "bo3", "bo5"
    timeLimit: bool = False
    globalBans: List[str] = []
    bannerImage: Optional[str] = None
```

### GameStatus 클래스

```python
class GameStatus(BaseModel):
    phase: int = 0
    phaseData: List[str] = []
    lastUpdatedAt: int = 0
    setNumber: int = 1
    blueTeamName: str = "Blue"
    redTeamName: str = "Red"
    blueScore: int = 0
    redScore: int = 0
```

### Client 클래스

```python
class Client(dict):
    """
    클라이언트 정보를 저장하는 딕셔너리 클래스

    속성:
    - nickname: 클라이언트 닉네임
    - position: 게임 내 포지션 (blue1, red3, spectator 등)
    - isReady: 준비 상태
    - isHost: 호스트 여부
    - champion: 현재 선택한 챔피언
    - isConfirmed: 챔피언 선택 확정 여부
    - clientId: 클라이언트 식별자
    - gameCode: 접속한 게임 코드
    - joinedAt: 게임 접속 시점
    """
    pass
```
