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

## 최근 변경사항

- 클라이언트 식별을 위한 `clientId` 필드 추가
- 재연결 메커니즘 개선 (`join_game` 이벤트에 이전 소켓 ID 전달 가능)
- 클라이언트의 특정 이벤트 응답에 상태 정보 확장
- 챔피언 선택 및 확정 관련 이벤트 개선
- 한글 오류 메시지 지원 추가

## 서버 엔드포인트

Socket.IO 서버는 다음 주소에서 실행됩니다:

- 개발 환경: `http://127.0.0.1:8000`
- 프로덕션 환경: `http://<your-domain>`

## 기본 이벤트

### 클라이언트 → 서버 이벤트

| 이벤트 명          | 설명           | 요청 데이터                                 | 응답 형식                   |
| ------------------ | -------------- | ------------------------------------------- | --------------------------- |
| join_game          | 게임 참가      | { gameCode, nickname, position, socketId? } | { status, message, [data] } |
| change_position    | 포지션 변경    | { position }                                | { status, message }         |
| change_ready_state | 준비 상태 변경 | { isReady }                                 | { status, message }         |
| select_champion    | 챔피언 선택    | { champion }                                | { status, message }         |
| confirm_selection  | 선택 확정      | {}                                          | { status, message }         |
| start_draft        | 드래프트 시작  | {}                                          | { status, message }         |
| confirm_result     | 게임 결과 확정 | { winner }                                  | { status, message }         |

### 서버 → 클라이언트 이벤트

| 이벤트 명             | 설명            | 데이터 형식                                                                      |
| --------------------- | --------------- | -------------------------------------------------------------------------------- |
| connection_success    | 연결 성공       | { sid }                                                                          |
| client_joined         | 클라이언트 참가 | { nickname, position, isHost }                                                   |
| client_left           | 클라이언트 퇴장 | { nickname, position }                                                           |
| position_changed      | 포지션 변경     | { nickname, oldPosition, newPosition }                                           |
| ready_state_changed   | 준비 상태 변경  | { nickname, position, isReady }                                                  |
| draft_started         | 드래프트 시작   | { gameCode, startedBy, timestamp }                                               |
| champion_selected     | 챔피언 선택     | { nickname, position, champion, phase, isConfirmed }                             |
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
  console.log("서버에 연결됨");
});

socket.on("connection_success", (data) => {
  console.log("연결 성공. 소켓 ID:", data.sid);

  // 소켓 ID를 로컬 스토리지에 저장하여 재연결 시 사용
  localStorage.setItem("socketId", data.sid);
});

socket.on("disconnect", () => {
  console.log("서버와 연결 끊김");
});

// 다른 클라이언트 나가는 것 감지
socket.on("client_left", (data) => {
  console.log(
    `${data.nickname}님이 게임을 나갔습니다 (포지션: ${data.position})`
  );
  // 연결 해제된 클라이언트 UI 업데이트
});
```

### 게임 참가

**이벤트:** `join_game`

게임 코드, 닉네임, 선택적 포지션을 제공하여 기존 게임에 참가합니다.

**요청:**

```javascript
// 새로운 연결로 게임 참가
socket.emit(
  "join_game",
  {
    gameCode: "ab12cd34", // 참가할 게임 코드
    nickname: "소환사이름", // 플레이어 닉네임
    position: "blue1", // 선택적: 특정 포지션 (기본값: "spectator")
  },
  (response) => {
    console.log(response); // 응답 처리

    if (response.status === "success") {
      // 클라이언트 ID 저장
      localStorage.setItem("clientId", response.data.clientId);
    }
  }
);

// 재연결 시 이전 소켓 ID 사용
const previousSocketId = localStorage.getItem("socketId");
if (previousSocketId) {
  socket.emit(
    "join_game",
    {
      gameCode: "ab12cd34",
      nickname: "소환사이름",
      position: "blue1",
      socketId: previousSocketId, // 이전 소켓 ID 제공
    },
    (response) => {
      console.log("재연결 응답:", response);
    }
  );
}
```

**응답:**

```javascript
{
  status: "success", // 또는 "error"
  message: "게임에 성공적으로 참가했습니다", // 또는 오류 메시지
  data: {
    position: "blue1",
    isHost: true,
    clientId: "socket-id-123" // 클라이언트 식별자
  }
}
```

**서버 브로드캐스트:** `client_joined`

```javascript
{
  nickname: "소환사이름",
  position: "blue1",
  isHost: true // 호스트 여부
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
  message: "포지션이 성공적으로 변경되었습니다" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `position_changed`

```javascript
{
  nickname: "소환사이름",
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
  message: "준비 상태가 업데이트되었습니다" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `ready_state_changed`

```javascript
{
  nickname: "소환사이름",
  position: "blue1",
  isReady: true
}
```

## 드래프트 기능

### 드래프트 시작

**이벤트:** `start_draft`

호스트만 사용 가능한 이벤트로, 모든 필요한 플레이어가 준비되면 드래프트 프로세스를 시작합니다.

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
  message: "드래프트가 시작되었습니다" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `draft_started`

```javascript
{
  gameCode: "ab12cd34",
  startedBy: "소환사이름", // 드래프트를 시작한 호스트의 닉네임
  timestamp: 1668457862000000
}
```

### 챔피언 선택

**이벤트:** `select_champion`

현재 차례인 플레이어가 챔피언을 선택합니다. 이 선택은 확정되기 전까지 변경 가능합니다.

**요청:**

```javascript
socket.emit(
  "select_champion",
  {
    champion: "Ahri", // 챔피언 ID
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
  message: "챔피언이 선택되었습니다" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `champion_selected`

```javascript
{
  nickname: "소환사이름",
  position: "blue1",
  champion: "Ahri",
  phase: 7, // 현재 페이즈 번호
  isConfirmed: false // 선택이 확정되지 않음
}
```

### 선택 확정

**이벤트:** `confirm_selection`

현재 차례인 플레이어가 선택한 챔피언을 확정하고 다음 페이즈로 진행합니다.

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
  message: "선택이 확정되었습니다" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `phase_progressed`

```javascript
{
  gameCode: "ab12cd34",
  confirmedBy: "소환사이름", // 확정한 플레이어 닉네임
  fromPhase: 7, // 이전 페이즈
  toPhase: 8, // 다음 페이즈
  confirmedChampion: "Ahri", // 확정된 챔피언
  timestamp: 1668457862000000
}
```

## 게임 결과 및 다음 단계

### 게임 결과 확정

**이벤트:** `confirm_result`

호스트가 게임의 승자를 선언하고 점수를 업데이트합니다.

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
  message: "게임 결과가 확정되었습니다" // 또는 오류 메시지
}
```

**서버 브로드캐스트:** `game_result_confirmed`

```javascript
{
  gameCode: "ab12cd34",
  confirmedBy: "소환사이름", // 결과를 확정한 호스트 닉네임
  winner: "blue", // 승리한 팀
  blueScore: 1, // 업데이트된 블루팀 점수
  redScore: 0, // 업데이트된 레드팀 점수
  nextSetNumber: 2, // 다음 세트 번호
  timestamp: 1668457862000000
}
```

## 재연결 전략

### 클라이언트 측 구현

1. 소켓 ID와 클라이언트 ID를 로컬 스토리지에 저장
2. 연결이 끊기면 자동으로 재연결 시도
3. 재연결 시 이전 ID를 사용하여 게임 세션 복구

```javascript
// 연결 상태 관리
let isConnected = false;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

socket.on("connect", () => {
  isConnected = true;
  reconnectAttempts = 0;
  console.log("서버에 연결됨");
});

socket.on("disconnect", () => {
  isConnected = false;
  console.log("연결이 끊어졌습니다. 재연결 시도 중...");

  // 재연결 시도
  attemptReconnect();
});

// 재연결 함수
const attemptReconnect = () => {
  if (reconnectAttempts >= maxReconnectAttempts) {
    console.error("최대 재연결 시도 횟수를 초과했습니다.");
    return;
  }

  reconnectAttempts++;

  setTimeout(() => {
    if (!isConnected) {
      const prevSocketId = localStorage.getItem("socketId");
      const gameCode = localStorage.getItem("gameCode");
      const nickname = localStorage.getItem("nickname");
      const position = localStorage.getItem("position");

      if (gameCode && nickname) {
        // 새 소켓 연결로 게임 재참가
        socket.emit(
          "join_game",
          {
            gameCode: gameCode,
            nickname: nickname,
            position: position || "spectator",
            socketId: prevSocketId,
          },
          (response) => {
            if (response.status === "success") {
              console.log("게임에 성공적으로 재연결되었습니다");
              localStorage.setItem("socketId", response.data.clientId);
            } else {
              console.error("재연결 실패:", response.message);
              attemptReconnect(); // 다시 시도
            }
          }
        );
      }
    }
  }, 1000 * reconnectAttempts); // 지수적 백오프
};
```

### 서버 측 구현

- 클라이언트가 연결 해제되면 일정 시간(예: 2분) 동안 자리 유지
- 같은 닉네임과 이전 소켓 ID로 재연결 시 동일한 상태 복원
- 시간 초과 후 자동으로 클라이언트 제거

## 오류 처리

### 일반적인 오류 유형

| 오류 유형      | 설명                                                 | 해결 방법             |
| -------------- | ---------------------------------------------------- | --------------------- |
| 게임 코드 없음 | 존재하지 않는 게임 코드로 참가 시도                  | 올바른 게임 코드 확인 |
| 닉네임 충돌    | 이미 사용 중인 닉네임으로 참가 시도                  | 다른 닉네임 사용      |
| 포지션 충돌    | 이미 다른 클라이언트가 차지한 포지션                 | 다른 포지션 선택      |
| 권한 오류      | 권한이 없는 작업 시도 (예: 비호스트의 드래프트 시작) | 권한 확인             |
| 잘못된 상태    | 현재 게임 상태에서 허용되지 않는 작업                | 게임 상태 확인        |

### 오류 응답 처리

```javascript
socket.emit("join_game", payload, (response) => {
  if (response.status === "error") {
    // 오류 처리
    console.error("게임 참가 오류:", response.message);

    switch (response.errorCode) {
      case "GAME_NOT_FOUND":
        alert("게임을 찾을 수 없습니다. 게임 코드를 확인해주세요.");
        break;
      case "NICKNAME_TAKEN":
        alert("이미 사용 중인 닉네임입니다. 다른 닉네임을 사용해주세요.");
        break;
      case "POSITION_TAKEN":
        alert(
          "이미 다른 플레이어가 선택한 포지션입니다. 다른 포지션을 선택해주세요."
        );
        break;
      default:
        alert("오류가 발생했습니다: " + response.message);
    }
  } else {
    // 성공 처리
    console.log("게임 참가 성공:", response.data);
  }
});
```

## 설치 및 참고사항

### 클라이언트 설치

```bash
# npm 사용
npm install socket.io-client

# yarn 사용
yarn add socket.io-client
```

### 서버 설치

```bash
# npm 사용
npm install socket.io

# yarn 사용
yarn add socket.io

# pip 사용 (Python)
pip install python-socketio
```

### 보안 고려사항

- 서버는 게임 코드 생성 시 예측 불가능한 방식 사용
- 클라이언트 인증을 위한 토큰 시스템 고려
- CORS 설정으로 허용된 도메인에서만 연결 가능

## 베스트오브 경기

BO3 또는 BO5 형식의 경우:

- 각 세트는 완전한 드래프트 과정을 거칩니다
- 각 세트 후, 호스트가 승자를 확정합니다
- 게임은 두 팀의 점수를 추적합니다
- 게임은 자동으로 다음 세트로 진행됩니다
- 한 팀이 승리 임계값에 도달하면 경기가 완료됩니다
