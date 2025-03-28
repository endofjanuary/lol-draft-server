# RESTful API 완전 가이드

> 이 문서는 LoL Draft Server의 RESTful API 엔드포인트와 사용 방법을 설명합니다. 게임 생성, 정보 조회, 클라이언트 관리 등의 기능을 HTTP 요청으로 수행하는 방법을 제공합니다.

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
      version: "14.10.1",
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
      version: "14.10.1",
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
      version: "14.10.1",
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
      throw new Error(`Game not found: ${gameCode}`);
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
      throw new Error(`Game not found: ${gameCode}`);
    }
    throw new Error(error.response.data.detail);
  }
};
```

**응답 구조:**

```javascript
{
  "game": {
    "gameCode": "ab12cd34",
    "createdAt": 1668457862000000,
    "gameName": "롤드컵 결승"
  },
  "settings": {
    "version": "14.10.1",
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
    "phaseData": ["", "", "..."],
    "setNumber": 1
  },
  "clients": [
    {
      "nickname": "Player1",
      "position": "blue1",
      "isReady": true,    // 준비 상태 필드
      "isHost": true      // 호스트 여부 필드 (방장인 경우 true)
    },
    {
      "nickname": "Player2",
      "position": "red1",
      "isReady": false,   // 준비 상태 필드
      "isHost": false     // 호스트 여부 필드 (방장이 아닌 경우 false)
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
      throw new Error(`Game not found: ${gameCode}`);
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
      throw new Error(`Game not found: ${gameCode}`);
    }
    const errorMsg = error.response.data.detail;
    throw new Error(errorMsg);
  }
};
```

## 완전한 프론트엔드 통합 예시

```javascript
// 게임 생성 및 접속 전체 흐름
const startNewGame = async () => {
  try {
    // 1. 게임 생성
    const game = await createGame();
    console.log(`Game created with code: ${game.gameCode}`);

    // 2. 소켓 연결
    const socket = io("http://localhost:8000", {
      transports: ["websocket"],
    });

    // 3. 연결 성공 시 게임 참가
    socket.on("connection_success", (data) => {
      console.log(`Connected with socket ID: ${data.sid}`);

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
            console.log("Successfully joined game as blue1");

            // 5. 준비 완료 상태로 설정
            socket.emit("change_ready_state", { isReady: true });
          }
        }
      );
    });

    // 6. 다른 플레이어 참가 감지
    socket.on("client_joined", (data) => {
      console.log(`${data.nickname} joined as ${data.position}`);
    });

    // 7. 게임 정보 주기적으로 확인
    setInterval(async () => {
      try {
        const gameInfo = await getGameInfo(game.gameCode);
        console.log("Current phase:", gameInfo.status.phase);

        // 필요에 따라 UI 업데이트
      } catch (error) {
        console.error("Error fetching game info:", error);
      }
    }, 5000);

    return { game, socket };
  } catch (error) {
    console.error("Error starting game:", error);
    throw error;
  }
};
```
