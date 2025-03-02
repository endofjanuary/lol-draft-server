# Socket.IO Connection Guide

## Server Endpoints

Socket.IO 서버는 다음 주소에서 실행됩니다:

- 개발 환경: `http://127.0.0.1:8000`
- 프로덕션 환경: `http://<your-domain>`

## Events

### Connection Events

- `connect`: 소켓 연결 시 자동으로 발생
- `connection_success`: 서버에서 연결 성공 시 발생 (sid 정보 포함)
- `disconnect`: 소켓 연결 해제 시 자동으로 발생

### Game Events

- `join_game`: 게임 참가 요청

  - Request:
    ```typescript
    {
      gameCode: string; // 참가할 게임의 코드
      nickname: string; // 클라이언트의 닉네임
    }
    ```
  - Response:
    ```typescript
    {
      status: "success" | "error";
      message: string;
      data?: {
        position: string;  // 할당된 포지션
        joinedAt: number; // 참가 시점
      }
    }
    ```

- `player_joined`: 새로운 플레이어 참가 알림 (서버 → 클라이언트)
  ```typescript
  {
    nickname: string; // 참가한 플레이어 닉네임
    position: string; // 할당된 포지션
    joinedAt: number; // 참가 시점
  }
  ```

## Frontend Implementation

기본 연결 예시:

```javascript
import { io } from "socket.io-client";

const socket = io("http://localhost:8000", {
  transports: ["websocket"],
  autoConnect: true,
});

socket.on("connect", () => {
  console.log("Socket connected");
});

socket.on("connection_success", (data) => {
  console.log("Connection successful, sid:", data.sid);
});

socket.on("disconnect", () => {
  console.log("Disconnected from server");
});
```

## Error Handling

### Connection Errors

```javascript
socket.on("connect_error", (error) => {
  console.error("Connection error:", error);
});

socket.on("connect_timeout", () => {
  console.error("Connection timeout");
});
```

### Event Errors

```javascript
socket.on("error", (error) => {
  console.error("Socket error:", error);
});
```

## Reconnection Strategy

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

## Installation & Notes

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
