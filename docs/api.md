# REST API Documentation

## Create Game

새로운 게임을 생성하고 초기화합니다.

- **URL**: `/games`
- **Method**: `POST`
- **Request Body**: GameSetting

```json
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
{
  "gameCode": "a1b2c3d4",
  "createdAt": 1740663081873
}
```

## Get Game Information

게임 코드에 해당하는 게임의 모든 정보를 조회합니다.

- **URL**: `/games/{game_code}`
- **Method**: `GET`
- **URL Parameters**:

  - `game_code`: 8자리 게임 코드

- **Response**: GameInfo

```json
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
    "phaseData": ["", "", "..."],
    "setNumber": 1
  }
}
```

## Get Game Clients

특정 게임에 접속해 있는 모든 클라이언트의 정보를 조회합니다.

- **URL**: `/games/{game_code}/clients`
- **Method**: `GET`
- **URL Parameters**:

  - `game_code`: 8자리 게임 코드

- **Response**: GameClients

```json
{
  "clients": [
    {
      "nickname": "Hide on bush",
      "position": "blue1"
    },
    {
      "nickname": "Faker",
      "position": "red1"
    }
  ]
}
```

## Common Headers

### Request Headers

```http
Content-Type: application/json
```

### Response Headers

```http
Content-Type: application/json
Access-Control-Allow-Origin: *
```

## Error Responses

모든 API는 다음과 같은 에러 응답을 반환할 수 있습니다:

### 400 Bad Request

잘못된 요청 형식이나 유효하지 않은 파라미터

```json
{
  "detail": "Invalid request body: matchFormat must be one of: bo1, bo3, bo5"
}
```

### 404 Not Found

요청한 리소스를 찾을 수 없음

```json
{
  "detail": "Game not found: a1b2c3d4"
}
```

### 500 Internal Server Error

서버 내부 오류

```json
{
  "detail": "Failed to process request"
}
```
