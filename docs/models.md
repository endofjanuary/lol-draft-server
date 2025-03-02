# Data Models

## Game

| Name      | Type   | Description                    |
| --------- | ------ | ------------------------------ |
| gameCode  | string | 8개의 16진수로 이루어진 문자열 |
| createdAt | number | 생성된 시점의 nanosecond값     |

## GameSetting

| Name        | Type    | Description                                    |
| ----------- | ------- | ---------------------------------------------- |
| version     | string  | 리그오브레전드 패치버전 (ex. "14.10.1")        |
| draftType   | string  | "tournament" / "hardFearless" / "softFearless" |
| playerType  | string  | "single" / "1v1" / "5v5"                       |
| matchFormat | string  | "bo1" / "bo3" / "bo5"                          |
| timeLimit   | boolean | true / false                                   |

## GameStatus

| Name          | Type     | Description                                     |
| ------------- | -------- | ----------------------------------------------- |
| phase         | number   | 0~21 사이의 정수 (현재 진행중인 phase)          |
| blueTeamName  | string   | 블루팀 이름 (default: "Blue")                   |
| redTeamName   | string   | 레드팀 이름 (default: "Red")                    |
| lastUpdatedAt | number   | 데이터가 마지막으로 수정된 시점의 nanosecond 값 |
| phaseData     | string[] | 22개의 문자열을 담은 배열 (각 phase별 데이터)   |
| setNumber     | number   | 1~5사이의 정수 (현재 진행중인 세트 번호)        |

## GameResult

| Name      | Type       | Description                               |
| --------- | ---------- | ----------------------------------------- |
| blueScore | number     | 0~3 사이의 정수 (블루팀의 누적 승리 횟수) |
| redScore  | number     | 0~3 사이의 정수 (레드팀의 누적 승리 횟수) |
| results   | string[][] | 최대 5개의 string List를 담은 2중 배열    |

## Client

| Name     | Type   | Description                                              |
| -------- | ------ | -------------------------------------------------------- |
| socketId | string | Socket.IO가 생성한 고유 클라이언트 ID                    |
| gameCode | string | 접속한 게임의 코드                                       |
| position | string | 클라이언트의 포지션 ("spectator" / "blue1-5" / "red1-5") |
| joinedAt | number | 게임 접속 시점의 nanosecond값                            |
| nickname | string | 클라이언트의 닉네임                                      |

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

- version: 형식 "xx.xx.xx" (예: "14.10.1")
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
  "version": "14.10.1",
  "draftType": "tournament",
  "playerType": "5v5",
  "matchFormat": "bo3",
  "timeLimit": true
}
```

### 1v1 게임

```json
{
  "version": "14.10.1",
  "draftType": "hardFearless",
  "playerType": "1v1",
  "matchFormat": "bo1",
  "timeLimit": false
}
```
