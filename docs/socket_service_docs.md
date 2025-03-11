# Socket Service Documentation

The Socket Service provides real-time communication for the League of Legends Draft application, enabling clients to join games, select champions, and progress through the draft process collaboratively.

## Connection Events

### Connection and Setup

The server uses Socket.IO to establish connections with clients.

**Server Events:**

- `connect`: Triggered when a client connects to the server
- `connection_success`: Sent by server upon successful connection
- `disconnect`: Triggered when a client disconnects
- `client_left`: Sent by server when a client disconnects from a game

**Example - Client Connection:**

```javascript
// Client-side connection setup
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

// Listen for other clients disconnecting
socket.on("client_left", (data) => {
  console.log(
    `${data.nickname} left the game (was in position: ${data.position})`
  );
  // Update UI to remove the disconnected client
});
```

## Game Participation Features

### Joining a Game

**Event:** `join_game`

Join an existing game by providing a game code, nickname, and optional position.

**Request:**

```javascript
socket.emit(
  "join_game",
  {
    gameCode: "ab12cd34", // Game code to join
    nickname: "SummonerName", // Player nickname
    position: "blue1", // Optional: specific position (defaults to "spectator")
  },
  (response) => {
    console.log(response); // Handle response
  }
);
```

**Response:**

```javascript
{
  status: "success", // or "error"
  message: "Successfully joined the game" // or error message
}
```

**Server Broadcast:** `client_joined`

```javascript
{
  nickname: "SummonerName",
  position: "blue1"
}
```

### Changing Position

**Event:** `change_position`

Change your position within a game (e.g., from spectator to player or between positions).

**Request:**

```javascript
socket.emit(
  "change_position",
  {
    position: "red1", // New position
  },
  (response) => {
    console.log(response);
  }
);
```

**Response:**

```javascript
{
  status: "success", // or "error"
  message: "Position changed successfully" // or error message
}
```

**Server Broadcast:** `position_changed`

```javascript
{
  nickname: "SummonerName",
  oldPosition: "blue1",
  newPosition: "red1"
}
```

### Setting Ready State

**Event:** `change_ready_state`

Set your ready status to indicate you're prepared to start the draft.

**Request:**

```javascript
socket.emit(
  "change_ready_state",
  {
    isReady: true, // Boolean value
  },
  (response) => {
    console.log(response);
  }
);
```

**Response:**

```javascript
{
  status: "success", // or "error"
  message: "Ready state updated successfully" // or error message
}
```

**Server Broadcast:** `ready_state_changed`

```javascript
{
  nickname: "SummonerName",
  position: "blue1",
  isReady: true
}
```

## Draft Features

### Starting the Draft

**Event:** `start_draft`

Initiate the draft process. Only the host (first player who joined) can start the draft.

**Request:**

```javascript
socket.emit("start_draft", {}, (response) => {
  console.log(response);
});
```

**Response:**

```javascript
{
  status: "success", // or "error"
  message: "Draft started successfully" // or error message
}
```

**Server Broadcast:** `draft_started`

```javascript
{
  gameCode: "ab12cd34",
  startedBy: "HostSummoner",
  timestamp: 1668457862000000
}
```

### Champion Selection

**Event:** `select_champion`

Select a champion during your turn in the draft.

**Request:**

```javascript
socket.emit(
  "select_champion",
  {
    champion: "Ahri", // Champion name
  },
  (response) => {
    console.log(response);
  }
);
```

**Response:**

```javascript
{
  status: "success", // or "error"
  message: "Champion selected successfully" // or error message
}
```

**Server Broadcast:** `champion_selected`

```javascript
{
  nickname: "SummonerName",
  position: "blue1",
  champion: "Ahri",
  phase: 7 // Current phase number
}
```

### Confirming Selection

**Event:** `confirm_selection`

Confirm your champion selection and progress to the next phase.

**Request:**

```javascript
socket.emit("confirm_selection", {}, (response) => {
  console.log(response);
});
```

**Response:**

```javascript
{
  status: "success", // or "error"
  message: "Phase progressed successfully" // or error message
}
```

**Server Broadcast:** `phase_progressed`

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

### Confirming Game Result

**Event:** `confirm_result`

Confirm the game result and proceed to the next set (in best-of series).

**Request:**

```javascript
socket.emit(
  "confirm_result",
  {
    winner: "blue", // "blue" or "red"
  },
  (response) => {
    console.log(response);
  }
);
```

**Response:**

```javascript
{
  status: "success", // or "error"
  message: "Game result confirmed successfully" // or error message
}
```

**Server Broadcast:** `game_result_confirmed`

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

## Role-Based Permissions

The Socket Service implements several role-based validations:

### Position Validation

- Positions are validated against the game's player type:
  - **Single mode**: Only "all" position is valid
  - **1v1 mode**: Only "blue1", "red1", and "spectator" are valid
  - **5v5 mode**: "blue1" through "blue5", "red1" through "red5", and "spectator" are valid

### Turn Validation

- During draft phases, only specific players can act based on the current phase:
  - Ban phases: Only team captains (position 1) can ban
  - Pick phases: Only the designated player for that specific phase can pick
  - For 1v1 mode, either player can act when it's their team's turn

### Host Privileges

- Only the host (earliest joined client) can:
  - Start the draft
  - Confirm game results and move to next set

## Draft Phase Details

The draft progresses through 21 distinct phases:

1. **Phase 0**: Preparation phase (waiting for players to ready up)
2. **Phases 1-6**: First ban phase (blue→red→blue→red→blue→red)
3. **Phases 7-12**: First pick phase (blue→red→red→blue→blue→red)
4. **Phases 13-16**: Second ban phase (red→blue→red→blue)
5. **Phases 17-20**: Second pick phase (red→blue→blue→red)
6. **Phase 21**: Game result confirmation

## Complete Flow Example

### Game Creation and Setup

1. Create a game through HTTP API
2. Connect to Socket.IO server
3. Join the game with `join_game` event
4. Change position if needed with `change_position`
5. Set ready status with `change_ready_state`

### Draft Process

1. Host starts draft with `start_draft` event
2. During your turn:
   - Select champion with `select_champion`
   - Confirm selection with `confirm_selection`
3. Wait for other players' turns
4. Draft completes after phase 20

### Game Completion

1. Host confirms result with `confirm_result`
2. For multi-set matches (BO3/BO5), return to preparation phase
3. Repeat draft process for next set

## Multi-Set Matches

For best-of-3 or best-of-5 formats:

- Each set runs through the complete draft process
- After each set, the host confirms the winner
- Game tracks score for both teams
- Game automatically advances to the next set
- Match completes when one team reaches the win threshold
