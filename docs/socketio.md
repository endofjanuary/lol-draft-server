# Socket.IO 연결 가이드

## 서버 엔드포인트

Socket.IO 서버는 다음 주소에서 실행됩니다:

- 개발 환경: `http://127.0.0.1:8000`
- 프로덕션 환경: `http://<your-domain>`

## 이벤트

### 클라이언트 → 서버 이벤트

| 이벤트 명          | 설명           | 요청 데이터                        | 응답 형식                   |
| ------------------ | -------------- | ---------------------------------- | --------------------------- |
| join_game          | 게임 참가      | { gameCode, nickname, [position] } | { status, message, [data] } |
| change_position    | 포지션 변경    | { position }                       | { status, message }         |
| change_ready_state | 준비 상태 변경 | { isReady }                        | { status, message }         |
| select_champion    | 챔피언 선택    | { champion }                       | { status, message }         |
| confirm_selection  | 선택 확정      | {}                                 | { status, message }         |
| start_draft        | 드래프트 시작  | {}                                 | { status, message }         |
| confirm_result     | 게임 결과 확정 | { winner }                         | { status, message }         |

### 서버 → 클라이언트 이벤트

| 이벤트 명             | 설명            | 데이터 형식                                                                      |
| --------------------- | --------------- | -------------------------------------------------------------------------------- |
| connection_success    | 연결 성공       | { sid }                                                                          |
| client_joined         | 클라이언트 참가 | { nickname, position }                                                           |
| client_left           | 클라이언트 퇴장 | { nickname, position }                                                           |
| position_changed      | 포지션 변경     | { nickname, oldPosition, newPosition }                                           |
| ready_state_changed   | 준비 상태 변경  | { nickname, position, isReady }                                                  |
| draft_started         | 드래프트 시작   | { gameCode, startedBy, timestamp }                                               |
| champion_selected     | 챔피언 선택     | { nickname, position, champion, phase }                                          |
| phase_progressed      | 페이즈 진행     | { gameCode, confirmedBy, fromPhase, toPhase, confirmedChampion, timestamp }      |
| game_result_confirmed | 게임 결과 확정  | { gameCode, confirmedBy, winner, blueScore, redScore, nextSetNumber, timestamp } |

## 전체 워크플로우 예시

### 게임 생성 및 참가

```javascript
// 1. Socket.IO 연결
const socket = io("http://localhost:8000", {
  transports: ["websocket"],
});

// 2. 연결 이벤트 처리
socket.on("connect", () => console.log("Connected"));
socket.on("connection_success", (data) => console.log("Socket ID:", data.sid));

// 3. REST API로 게임 생성
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
  return await response.json();
};

// 4. 게임에 참가
const joinGame = (gameCode, nickname, position = "spectator") => {
  socket.emit(
    "join_game",
    {
      gameCode,
      nickname,
      position,
    },
    (response) => {
      if (response.status === "success") {
        console.log("Successfully joined game");
      }
    }
  );
};

// 5. 포지션 변경
const changePosition = (position) => {
  socket.emit("change_position", { position }, (response) => {
    console.log(response.message);
  });
};

// 6. 준비 상태 변경
const setReady = (isReady = true) => {
  socket.emit("change_ready_state", { isReady }, (response) => {
    console.log(response.message);
  });
};
```

### 드래프트 과정

```javascript
// 1. 드래프트 시작 (호스트만 가능)
const startDraft = () => {
  socket.emit("start_draft", {}, (response) => {
    console.log(response.message);
  });
};

// 2. 챔피언 선택
const selectChampion = (championName) => {
  socket.emit(
    "select_champion",
    {
      champion: championName,
    },
    (response) => {
      console.log(response.message);
    }
  );
};

// 3. 선택 확정
const confirmSelection = () => {
  socket.emit("confirm_selection", {}, (response) => {
    console.log(response.message);
  });
};

// 4. 게임 결과 확정 (호스트만 가능)
const confirmResult = (winner) => {
  // 'blue' or 'red'
  socket.emit("confirm_result", { winner }, (response) => {
    console.log(response.message);
  });
};
```

### 이벤트 수신 처리

````javascript
// 다른 플레이어 참가
socket.on("client_joined", (data) => {
  console.log(`${data.nickname} joined as ${data.position}`);
  // UI 업데이트
});
장
// 포지션 변경
socket.on("position_changed", (data) => {`${data.nickname} left the game (position: ${data.position})`);
  console.log(
    `${data.nickname} changed from ${data.oldPosition} to ${data.newPosition}`
  );
  // UI 업데이트포지션 변경
});socket.on("position_changed", (data) => {
og(
// 준비 상태 변경dPosition} to ${data.newPosition}`
socket.on("ready_state_changed", (data) => {
  console.log(`${data.nickname} ready state: ${data.isReady}`);
  // UI 업데이트
});
경
// 드래프트 시작) => {
socket.on("draft_started", (data) => {isReady}`);
  console.log(`Draft started by ${data.startedBy}`);
  // UI를 드래프트 모드로 변경
});
작
// 챔피언 선택
socket.on("champion_selected", (data) => {`Draft started by ${data.startedBy}`);
  console.log(
    `${data.nickname} selected ${data.champion} in phase ${data.phase}`
  );
  // 챔피언 선택 UI 업데이트챔피언 선택
});socket.on("champion_selected", (data) => {
.log(
// 페이즈 진행mpion} in phase ${data.phase}`
socket.on("phase_progressed", (data) => {
  console.log(`Phase changed from ${data.fromPhase} to ${data.toPhase}`);
  console.log(`Champion confirmed: ${data.confirmedChampion}`);
  // 현재 턴 표시 업데이트
});// 페이즈 진행
phase_progressed", (data) => {
// 게임 결과 확정hase} to ${data.toPhase}`);
socket.on("game_result_confirmed", (data) => {firmedChampion}`);
  console.log(`Game winner: ${data.winner}`);
  console.log(`Score: Blue ${data.blueScore} - ${data.redScore} Red`);
  console.log(`Next set: ${data.nextSetNumber}`);
  // 결과 화면 표시 또는 다음 세트 준비게임 결과 확정
});ket.on("game_result_confirmed", (data) => {
```  console.log(`Game winner: ${data.winner}`);
 ${data.blueScore} - ${data.redScore} Red`);
## Frontend Implementation  console.log(`Next set: ${data.nextSetNumber}`);
면 표시 또는 다음 세트 준비
기본 연결 예시:});

```javascript
import { io } from "socket.io-client";## Frontend Implementation

const socket = io("http://localhost:8000", {
  transports: ["websocket"],
  autoConnect: true,javascript
});import { io } from "socket.io-client";

socket.on("connect", () => {t:8000", {
  console.log("Socket connected");ransports: ["websocket"],
});  autoConnect: true,

socket.on("connection_success", (data) => {
  console.log("Connection successful, sid:", data.sid);ket.on("connect", () => {
});  console.log("Socket connected");

socket.on("disconnect", () => {
  console.log("Disconnected from server");ket.on("connection_success", (data) => {
});onsole.log("Connection successful, sid:", data.sid);
```});

## Error Handlingsocket.on("disconnect", () => {
nected from server");
### Connection Errors});

```javascript
socket.on("connect_error", (error) => {
  console.error("Connection error:", error);
});### Connection Errors

socket.on("connect_timeout", () => {
  console.error("Connection timeout");ket.on("connect_error", (error) => {
});onsole.error("Connection error:", error);
```});

### Event Errorssocket.on("connect_timeout", () => {
or("Connection timeout");
```javascript
socket.on("error", (error) => {
  console.error("Socket error:", error);
}); Event Errors
````

## Reconnection Strategysocket.on("error", (error) => {

error("Socket error:", error);
기본 재연결 설정:});

````javascript
const socket = io("http://localhost:8000", {
  transports: ["websocket"],
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,("http://localhost:8000", {
  timeout: 20000,ransports: ["websocket"],
});econnection: true,
```  reconnectionAttempts: 5,
ionDelay: 1000,
재연결 이벤트 처리:  reconnectionDelayMax: 5000,
000,
```javascript
socket.on("reconnect_attempt", (attemptNumber) => {
  console.log(`Reconnection attempt ${attemptNumber}`);
});재연결 이벤트 처리:

socket.on("reconnect", (attemptNumber) => {
  console.log(`Reconnected after ${attemptNumber} attempts`);ket.on("reconnect_attempt", (attemptNumber) => {
});  console.log(`Reconnection attempt ${attemptNumber}`);

socket.on("reconnect_failed", () => {
  console.error("Failed to reconnect");ket.on("reconnect", (attemptNumber) => {
});onsole.log(`Reconnected after ${attemptNumber} attempts`);
```});

## Installation & Notessocket.on("reconnect_failed", () => {
ct");
프론트엔드에서 Socket.IO 클라이언트 라이브러리를 설치:});

```bash
npm install socket.io-clientnstallation & Notes
# or
yarn add socket.io-client드에서 Socket.IO 클라이언트 라이브러리를 설치:
# or
pnpm add socket.io-clientbash
```npm install socket.io-client

1. 서버는 루트 경로('/')에 마운트되어 있어 별도의 path 설정이 필요하지 않습니다
2. 기본적으로 모든 origin에서의 접근이 허용됩니다 (개발 환경 기준)
3. WebSocket transport를 사용하여 실시간 양방향 통신이 가능합니다
4. 연결 성공 시 `connection_success` 이벤트를 통해 서버에서 socket id를 전달받습니다
5. 프로덕션 환경에서는 보안을 위해 허용된 origin을 명시적으로 설정해야 합니다

1. 서버는 루트 경로('/')에 마운트되어 있어 별도의 path 설정이 필요하지 않습니다
2. 기본적으로 모든 origin에서의 접근이 허용됩니다 (개발 환경 기준)
3. WebSocket transport를 사용하여 실시간 양방향 통신이 가능합니다
4. 연결 성공 시 `connection_success` 이벤트를 통해 서버에서 socket id를 전달받습니다
5. 프로덕션 환경에서는 보안을 위해 허용된 origin을 명시적으로 설정해야 합니다
````
