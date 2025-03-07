# RESTful API 완전 가이드

## 1. 게임 생성 (Create Game)

새 게임을 생성하고 게임 코드를 얻습니다.

**요청 예시:**

```javascript
// Using fetch
const createGame = async () => {
  const response = await fetch("http://localhost:8000/games", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      version: "14.10.1",
      draftType: "tournament", // "tournament", "hardFearless", "softFearless"
      playerType: "5v5", // "single", "1v1", "5v5"
      matchFormat: "bo3", // "bo1", "bo3", "bo5"
      timeLimit: true,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
};

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

게임 코드로 게임 정보를 조회합니다.

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
