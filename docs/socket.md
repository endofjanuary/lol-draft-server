# Socket.IO 가이드

> 이 문서는 LoL Draft Server의 실시간 통신을 위한 Socket.IO 구현에 관한 가이드입니다. 기본 연결 방법부터 이벤트 처리, 고급 기능까지 포괄적으로 다룹니다.

## 목차

- [서버 엔드포인트](#서버-엔드포인트)
- [기본 이벤트](#기본-이벤트)
- [게임 참여 기능](#게임-참여-기능)
- [드래프트 기능](#드래프트-기능)
- [권한 및 역할](#권한-및-역할)
- [예제 코드](#예제-코드)
- [오류 처리](#오류-처리)
- [재연결 전략](#재연결-전략)
- [설치 및 참고사항](#설치-및-참고사항)

## 서버 엔드포인트

Socket.IO 서버는 다음 주소에서 실행됩니다:

- 개발 환경: `http://127.0.0.1:8000`
- 프로덕션 환경: `http://<your-domain>`

## 기본 이벤트

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

## 게임 참여 기능

### 연결 및 설정

서버는 Socket.IO를 사용하여 클라이언트와 연결을 설정합니다.

**연결 이벤트:**

- `connect`: 클라이언트가 서버에 연결될 때 발생
- `connection_success`: 연결 성공 시 서버에서 전송
- `disconnect`: 클라이언트 연결 해제 시 발생
- `client_left`: 클라이언트가 게임에서 나갈 때 서버에서 전송

**클라이언트 연결 예시:**

```javascript
// 클라이언트 측 연결 설정
const socket = io("http://localhost:8000", {
  transports: ["websocket"],
});

socket.on("connect", () => {
  console.log("Connected to server");
});

socket.on("connection_success", (data) => {
  console.log("Connection successful. Socket ID:", data.sid);
});

socket.on("disconnect", () => {
  console.log("Disconnected from server");
});

// 다른 클라이언트 나가는 것 감지
socket.on("client_left", (data) => {
  console.log(
    `${data.nickname} left the game (was in position: ${data.position})`
  );
  // 연결 해제된 클라이언트 UI 업데이트
});
```

### 게임 참가

**이벤트:** `join_game`

게임 코드, 닉네임, 선택적 포지션을 제공하여 기존 게임에 참가합니다.

**요청:**

```javascript
socket.emit(
  "join_game",
  {
    gameCode: "ab12cd34", // 참가할 게임 코드
    nickname: "SummonerName", // 플레이어 닉네임
    position: "blue1", // 선택적: 특정 포지션 (기본값: "spectator")
  },
  (response) => {
    console.log(response); // 응답 처리
  }
);
```

**응답:**

```javascript
{
  status: "success", // 또는 "error"
  message: "Successfully joined the game" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `client_joined`

```javascript
{
  nickname: "SummonerName",
  position: "blue1"
}
```

### 포지션 변경

**이벤트:** `change_position`

게임 내에서 포지션을 변경합니다(예: 관전자에서 플레이어로 또는 포지션 간).

**요청:**

```javascript
socket.emit(
  "change_position",
  {
    position: "red1", // 새 포지션
  },
  (response) => {
    console.log(response);
  }
);
```

**응답:**

```javascript
{
  status: "success", // 또는 "error"
  message: "Position changed successfully" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `position_changed`

```javascript
{
  nickname: "SummonerName",
  oldPosition: "blue1",
  newPosition: "red1"
}
```

### 준비 상태 설정

**이벤트:** `change_ready_state`

드래프트를 시작할 준비가 되었음을 나타내는 준비 상태를 설정합니다.

**요청:**

```javascript
socket.emit(
  "change_ready_state",
  {
    isReady: true, // 불리언 값
  },
  (response) => {
    console.log(response);
  }
);
```

**응답:**

```javascript
{
  status: "success", // 또는 "error"
  message: "Ready state updated successfully" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `ready_state_changed`

```javascript
{
  nickname: "SummonerName",
  position: "blue1",
  isReady: true
}
```

## 드래프트 기능

### 드래프트 시작

**이벤트:** `start_draft`

드래프트 과정을 시작합니다. 호스트(가장 먼저 참가한 플레이어)만 시작할 수 있습니다.

**요청:**

```javascript
socket.emit("start_draft", {}, (response) => {
  console.log(response);
});
```

**응답:**

```javascript
{
  status: "success", // 또는 "error"
  message: "Draft started successfully" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `draft_started`

```javascript
{
  gameCode: "ab12cd34",
  startedBy: "HostSummoner",
  timestamp: 1668457862000000
}
```

### 챔피언 선택

**이벤트:** `select_champion`

드래프트 중 자신의 턴에 챔피언을 선택합니다.

**요청:**

```javascript
socket.emit(
  "select_champion",
  {
    champion: "Ahri", // 챔피언 이름
  },
  (response) => {
    console.log(response);
  }
);
```

**응답:**

```javascript
{
  status: "success", // 또는 "error"
  message: "Champion selected successfully" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `champion_selected`

```javascript
{
  nickname: "SummonerName",
  position: "blue1",
  champion: "Ahri",
  phase: 7 // 현재 페이즈 번호
}
```

### 선택 확정

**이벤트:** `confirm_selection`

챔피언 선택을 확정하고 다음 페이즈로 진행합니다.

**요청:**

```javascript
socket.emit("confirm_selection", {}, (response) => {
  console.log(response);
});
```

**응답:**

```javascript
{
  status: "success", // 또는 "error"
  message: "Phase progressed successfully" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `phase_progressed`

```javascript
{
  gameCode: "ab12cd34",
  confirmedBy: "SummonerName",
  fromPhase: 7,
  toPhase: 8,
  confirmedChampion: "Ahri",
  timestamp: 1668457922000000
}
```

### 게임 결과 확정

**이벤트:** `confirm_result`

게임 결과를 확정하고 다음 세트(베스트오브 시리즈에서)로 진행합니다.

**요청:**

```javascript
socket.emit(
  "confirm_result",
  {
    winner: "blue", // "blue" 또는 "red"
  },
  (response) => {
    console.log(response);
  }
);
```

**응답:**

```javascript
{
  status: "success", // 또는 "error"
  message: "Game result confirmed successfully" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `game_result_confirmed`

```javascript
{
  gameCode: "ab12cd34",
  confirmedBy: "HostSummoner",
  winner: "blue",
  blueScore: 1,
  redScore: 0,
  nextSetNumber: 2,
  timestamp: 1668460000000000
}
```

## 권한 및 역할

Socket 서비스는 여러 역할 기반 검증을 구현합니다:

### 포지션 검증

- 포지션은 게임의 playerType에 따라 검증됩니다:
  - **Single 모드**: "all" 포지션만 유효
  - **1v1 모드**: "blue1", "red1", "spectator"만 유효
  - **5v5 모드**: "blue1"부터 "blue5", "red1"부터 "red5", "spectator"가 유효

### 턴 검증

- 드래프트 페이즈 동안 현재 페이즈에 따라 특정 플레이어만 행동할 수 있습니다:
  - 밴 페이즈: 팀 주장(포지션 1)만 밴 가능
  - 픽 페이즈: 해당 특정 페이즈에 지정된 플레이어만 픽 가능
  - 1v1 모드의 경우, 팀의 턴일 때 해당 팀의 플레이어가 행동 가능

### 호스트 권한

- 호스트(가장 먼저 참가한 클라이언트)만 가능한 작업:
  - 드래프트 시작
  - 게임 결과 확정 및 다음 세트로 이동

## 드래프트 페이즈 상세

드래프트는 21개의 고유한 페이즈로 진행됩니다:

1. **페이즈 0**: 준비 페이즈(플레이어가 준비될 때까지 대기)
2. **페이즈 1-6**: 첫 번째 밴 페이즈(블루→레드→블루→레드→블루→레드)
3. **페이즈 7-12**: 첫 번째 픽 페이즈(블루→레드→레드→블루→블루→레드)
4. **페이즈 13-16**: 두 번째 밴 페이즈(레드→블루→레드→블루)
5. **페이즈 17-20**: 두 번째 픽 페이즈(레드→블루→블루→레드)
6. **페이즈 21**: 게임 결과 확정

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

```javascript
// 다른 플레이어 참가
socket.on("client_joined", (data) => {
  console.log(`${data.nickname} joined as ${data.position}`);
  // UI 업데이트
});

// 다른 플레이어 퇴장
socket.on("client_left", (data) => {
  console.log(`${data.nickname} left the game (position: ${data.position})`);
  // UI 업데이트
});

// 포지션 변경
socket.on("position_changed", (data) => {
  console.log(
    `${data.nickname} changed from ${data.oldPosition} to ${data.newPosition}`
  );
  // UI 업데이트
});

// 준비 상태 변경
socket.on("ready_state_changed", (data) => {
  console.log(`${data.nickname} ready state: ${data.isReady}`);
  // UI 업데이트
});

// 드래프트 시작
socket.on("draft_started", (data) => {
  console.log(`Draft started by ${data.startedBy}`);
  // UI를 드래프트 모드로 변경
});

// 챔피언 선택
socket.on("champion_selected", (data) => {
  console.log(
    `${data.nickname} selected ${data.champion} in phase ${data.phase}`
  );
  // 챔피언 선택 UI 업데이트
});

// 페이즈 진행
socket.on("phase_progressed", (data) => {
  console.log(`Phase changed from ${data.fromPhase} to ${data.toPhase}`);
  console.log(`Champion confirmed: ${data.confirmedChampion}`);
  // 현재 턴 표시 업데이트
});

// 게임 결과 확정
socket.on("game_result_confirmed", (data) => {
  console.log(`Game winner: ${data.winner}`);
  console.log(`Score: Blue ${data.blueScore} - ${data.redScore} Red`);
  console.log(`Next set: ${data.nextSetNumber}`);
  // 결과 화면 표시 또는 다음 세트 준비
});
```

## 오류 처리

### 연결 오류

```javascript
socket.on("connect_error", (error) => {
  console.error("Connection error:", error);
});

socket.on("connect_timeout", () => {
  console.error("Connection timeout");
});
```

### 이벤트 오류

```javascript
socket.on("error", (error) => {
  console.error("Socket error:", error);
});
```

## 재연결 전략

기본 재연결 설정:

```javascript
const socket = io("http://localhost:8000", {
  transports: ["websocket"],
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 20000,
});
```

재연결 이벤트 처리:

```javascript
socket.on("reconnect_attempt", (attemptNumber) => {
  console.log(`Reconnection attempt ${attemptNumber}`);
});

socket.on("reconnect", (attemptNumber) => {
  console.log(`Reconnected after ${attemptNumber} attempts`);
});

socket.on("reconnect_failed", () => {
  console.error("Failed to reconnect");
});
```

## 설치 및 참고사항

프론트엔드에서 Socket.IO 클라이언트 라이브러리를 설치:

```bash
npm install socket.io-client
# or
yarn add socket.io-client
# or
pnpm add socket.io-client
```

1. 서버는 루트 경로('/')에 마운트되어 있어 별도의 path 설정이 필요하지 않습니다
2. 기본적으로 모든 origin에서의 접근이 허용됩니다 (개발 환경 기준)
3. WebSocket transport를 사용하여 실시간 양방향 통신이 가능합니다
4. 연결 성공 시 `connection_success` 이벤트를 통해 서버에서 socket id를 전달받습니다
5. 프로덕션 환경에서는 보안을 위해 허용된 origin을 명시적으로 설정해야 합니다

## 베스트오브 경기

BO3 또는 BO5 형식의 경우:

- 각 세트는 완전한 드래프트 과정을 거칩니다
- 각 세트 후, 호스트가 승자를 확정합니다
- 게임은 두 팀의 점수를 추적합니다
- 게임은 자동으로 다음 세트로 진행됩니다
- 한 팀이 승리 임계값에 도달하면 경기가 완료됩니다
