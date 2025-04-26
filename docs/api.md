# RESTful API 완전 가이드

> 이 문서는 LoL Draft Server의 RESTful API 엔드포인트와 사용 방법을 설명합니다. 게임 생성, 정보 조회, 클라이언트 관리 등의 기능을 HTTP 요청으로 수행하는 방법을 제공합니다.

## 최근 변경사항

- 기본 롤 패치 버전을 `13.24.1`로 업데이트
- 클라이언트 데이터 구조를 `dict` 타입으로 변경하여 유연성 향상
- 응답 형식에 `clientId` 필드 추가하여 세션 관리 개선
- 한글 오류 메시지 지원 추가
- isHost 속성 처리 방식 개선
- HTTP 상태 코드를 사용한 오류 응답 개선

## 1. 게임 생성 (Create Game)

새 게임을 생성하고 게임 코드를 얻습니다.

### 기본 요청 예시:

```javascript
// Using fetch with minimal required fields
const createGame = async () => {
  const response = await fetch("http://localhost:8000/games", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      version: "13.24.1", // 기본 버전 업데이트됨
      draftType: "tournament",
      playerType: "5v5",
      matchFormat: "bo3",
      timeLimit: true,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
};
```

### 추가 옵션 사용 예시:

```javascript
// Using fetch with all optional fields
const createGameWithOptions = async () => {
  const response = await fetch("http://localhost:8000/games", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      // 필수 필드
      version: "13.24.1", // 기본 버전 업데이트됨
      draftType: "tournament",
      playerType: "5v5",
      matchFormat: "bo3",
      timeLimit: true,

      // 추가 필드
      gameName: "롤드컵 결승", // 게임 이름
      teamNames: {
        // 팀 이름
        blue: "T1",
        red: "Gen.G",
      },
      // 또는 직접 팀 이름 지정
      // blueTeamName: "T1",
      // redTeamName: "Gen.G",

      globalBans: ["Yuumi", "Zed"], // 전역 밴 챔피언 목록

      // 배너 이미지 (base64 인코딩된 문자열)
      bannerImage: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
};
```

```javascript
// Using axios
const createGame = async () => {
  try {
    const response = await axios.post("http://localhost:8000/games", {
      version: "13.24.1", // 기본 버전 업데이트됨
      draftType: "tournament",
      playerType: "5v5",
      matchFormat: "bo3",
      timeLimit: true,
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response.data.detail);
  }
};
```

## 2. 게임 정보 조회 (Get Game Info)

게임 코드로 게임 정보를 조회합니다. 응답에는 게임 정보뿐만 아니라 현재 게임에 참여하고 있는 클라이언트들의 정보(닉네임, 포지션)도 함께 포함됩니다.

**요청 예시:**

```javascript
// Using fetch
const getGameInfo = async (gameCode) => {
  const response = await fetch(`http://localhost:8000/games/${gameCode}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`게임을 찾을 수 없습니다: ${gameCode}`);
    }
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
};

// Using axios
const getGameInfo = async (gameCode) => {
  try {
    const response = await axios.get(`http://localhost:8000/games/${gameCode}`);
    return response.data;
  } catch (error) {
    if (error.response.status === 404) {
      throw new Error(`게임을 찾을 수 없습니다: ${gameCode}`);
    }
    throw new Error(error.response.data.detail);
  }
};
```

**응답 구조:**

```javascript
{
  "code": "ab12cd34", // 변경됨: gameCode 필드가 code로 변경
  "settings": {
    "version": "13.24.1",
    "draftType": "tournament",
    "playerType": "5v5",
    "matchFormat": "bo3",
    "timeLimit": true,
    "globalBans": ["Yuumi", "Zed"],
    "bannerImage": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."  // 설정에 저장된 배너 이미지
  },
  "status": {
    "phase": 0,
    "blueTeamName": "Blue",
    "redTeamName": "Red",
    "lastUpdatedAt": 1668457862000000,
    "phaseData": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    "setNumber": 1
  },
  "clients": [
    {
      "nickname": "Player1",
      "position": "blue1",
      "isReady": true,         // 준비 상태 필드
      "isHost": true,          // 호스트 여부 필드 (방장인 경우 true)
      "champion": null,        // 현재 선택한 챔피언
      "isConfirmed": false,    // 챔피언 선택 확정 여부
      "clientId": "socket-id-1" // 클라이언트 식별자로 사용되는 소켓 ID
    },
    {
      "nickname": "Player2",
      "position": "red1",
      "isReady": false,
      "isHost": false,
      "champion": null,
      "isConfirmed": false,
      "clientId": "socket-id-2"
    },
    // ... 기타 접속중인 클라이언트
  ],
  "blueScore": 1,         // 블루팀의 현재 승리 횟수
  "redScore": 0,          // 레드팀의 현재 승리 횟수
  "bannerImage": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."  // 최상위 레벨에서 접근 가능한 배너 이미지
}
```

## 3. 게임 참여자 조회 (Get Game Clients)

게임에 현재 접속한 클라이언트 목록을 조회합니다.

**요청 예시:**

```javascript
// Using fetch
const getGameClients = async (gameCode) => {
  const response = await fetch(
    `http://localhost:8000/games/${gameCode}/clients`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    }
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`게임을 찾을 수 없습니다: ${gameCode}`);
    }
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
};

// Using axios
const getGameClients = async (gameCode) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/games/${gameCode}/clients`
    );
    return response.data;
  } catch (error) {
    if (error.response.status === 404) {
      throw new Error(`게임을 찾을 수 없습니다: ${gameCode}`);
    }
    const errorMsg = error.response.data.detail;
    throw new Error(errorMsg);
  }
};
```

## 오류 처리

서버는 다음과 같은 HTTP 상태 코드를 사용하여 오류를 반환합니다:

- **400 Bad Request**: 요청 형식이 잘못되었거나 필수 필드가 누락된 경우
- **404 Not Found**: 요청한 게임 코드를 찾을 수 없는 경우
- **409 Conflict**: 닉네임이나 포지션이 이미 사용 중인 경우
- **500 Internal Server Error**: 서버 내부 오류가 발생한 경우

**오류 응답 예시:**

```json
{
  "detail": "게임을 찾을 수 없습니다: AB1234",
  "status_code": 404
}
```

## 데이터 모델

### GameSetting

게임 설정을 정의하는 데이터 모델입니다.

```python
class GameSetting(BaseModel):
    version: str = "13.24.1"  # 기본 버전 업데이트됨
    draftType: str = "tournament"
    playerType: str = "1v1"  # "single", "1v1", "5v5"
    matchFormat: str = "bo1"  # "bo1", "bo3", "bo5"
    timeLimit: bool = False
    globalBans: List[str] = []
    bannerImage: Optional[str] = None
```

### GameStatus

게임 상태를 정의하는 데이터 모델입니다.

```python
class GameStatus(BaseModel):
    phase: int = 0  # 0: 로비, 1-6: 밴 페이즈1, 7-12: 픽 페이즈1, 13-16: 밴 페이즈2, 17-20: 픽 페이즈2, 21: 결과 확인
    phaseData: List[str] = []  # 각 페이즈의 선택한 챔피언 이름 저장
    lastUpdatedAt: int = 0
    setNumber: int = 1  # 현재 세트 번호 (bo3에서는 1-3, bo5에서는 1-5)
    blueTeamName: str = "Blue"
    redTeamName: str = "Red"
    blueScore: int = 0  # 블루팀의 세트 스코어
    redScore: int = 0   # 레드팀의 세트 스코어
```

### Client

클라이언트 정보를 저장하는 클래스입니다.

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
    """
    pass
```

## 완전한 프론트엔드 통합 예시

```javascript
// 게임 생성 및 접속 전체 흐름
const startNewGame = async () => {
  try {
    // 1. 게임 생성
    const game = await createGame();
    console.log(`게임이 생성되었습니다. 코드: ${game.gameCode}`);

    // 2. 소켓 연결
    const socket = io("http://localhost:8000", {
      transports: ["websocket"],
    });

    // 3. 연결 성공 시 게임 참가
    socket.on("connection_success", (data) => {
      console.log(`소켓 ID로 연결됨: ${data.sid}`);

      // 4. 게임에 참가 (블루팀 1번 포지션으로)
      socket.emit(
        "join_game",
        {
          gameCode: game.gameCode,
          nickname: "Player1",
          position: "blue1",
        },
        (response) => {
          if (response.status === "success") {
            console.log("게임에 성공적으로 참가했습니다.");
          } else {
            console.error(`게임 참가 오류: ${response.message}`);
          }
        }
      );
    });

    // 필요한 이벤트 핸들러 등록
    // ...
  } catch (error) {
    console.error("오류 발생:", error.message);
  }
};
```
