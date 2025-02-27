# League of Legends Draft Webpage - Server

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

#### Phase 상세 설명

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
