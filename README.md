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
