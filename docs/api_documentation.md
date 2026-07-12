# Khushi AI - API Documentation

The Khushi AI server runs a local FastAPI REST and WebSocket application on port `8000`.

## 1. Authentication
All endpoints (except system `/status`) require Bearer token or Custom Header authentication:
- **Header**: `Authorization: Bearer <secure_api_key>`
- **Custom Header**: `x-api-key: <secure_api_key>`
- **Query Parameter (WS/Stream)**: `?token=<secure_api_key>`

---

## 2. Core API Endpoints

### `GET /status`
- **Description**: Returns local server status and computer resource metrics.
- **Response**:
  ```json
  {
    "status": "online",
    "system_info": {
      "cpu_percent": 12.5,
      "ram_percent": 65.2,
      "battery_percent": 98,
      "uptime_seconds": 3600
    }
  }
  ```

### `POST /chat`
- **Description**: Processes a natural language text query.
- **Request Body**: `{"message": "What relates to UPSC?"}`
- **Response**: `{"response": "Here is how UPSC relates..."}`

### `GET /tasks` / `POST /tasks` / `DELETE /tasks/{key}`
- **Description**: Syncs to-do task categories inside user memories.

---

## 3. Knowledge Graph Endpoints

### `GET /graph`
- **Description**: Exposes the full world model nodes list and connection adjacency map.

### `GET /graph/search`
- **Query Parameters**: `query` (string)
- **Description**: Returns semantically matched nodes based on keyword overlap.

### `GET /graph/explain`
- **Query Parameters**: `entity` (string)
- **Description**: Returns list of direct relationship connection sentences.

---

## 4. Protected Backups Endpoints

### `POST /backup/create`
- **Request Body**: `{"password": "...", "label": "..."}`
- **Description**: Packages active memories into an AES-256 encrypted payload file.

### `GET /backup/list`
- **Description**: Lists historical backup versions, size, and creation times.

### `POST /backup/restore`
- **Request Body**: `{"backup_name": "...", "password": "..."}`

---

## 5. Vehicle diagnostics Endpoints

### `GET /vehicle/scan`
- **Description**: Searches for nearby ELM327 Bluetooth/Serial adapters.

### `GET /vehicle/status`
- **Description**: Returns live OBD-II sensor values (RPM, Speed, Load, Temp).

### `GET /vehicle/diagnostics`
- **Description**: Returns diagnostic trouble codes (DTCs) from ECU.

---

## 6. Real-Time WebSockets

### `WS /chat`
- **Connection**: `ws://localhost:8000/chat?token=<key>`
- **Usage**: Interactive full-duplex chat interface.

### `WS /events`
- **Connection**: `ws://localhost:8000/events?token=<key>`
- **Usage**: Streams background EventBus notifications (memory changes, automations).
