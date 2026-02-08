# Chip Heater AI Manual

**Purpose**: This manual is designed for AI agents to understand how to interact with, configure, and extend the Chip Heater platform.

**Design Principle**: Progressive Disclosure. Read Level 1 for quick actions. Read Level 2 for detailed implementation. Read Level 3 for architectural patterns.

---

## Level 1 - Quick Reference

**Base URL**: `http://localhost:8000` (API), `http://localhost:3000` (Dashboard)
**Auth**: Bearer Token (JWT)

| INTENT | ENDPOINT / COMMAND | MINIMAL EXAMPLE (cURL) |
| :--- | :--- | :--- |
| **Login** | `POST /auth/token` | `curl -X POST /auth/token -d "username=user@example.com&password=pass"` |
| **Create Instance** | `POST /instances/` | `curl -X POST /instances/ -H "Authorization: Bearer $TOKEN" -d '{"name": "chip_01", "proxy_url": "http://user:pass@ip:port"}'` |
| **Get QR Code** | `GET /instances/{id}/qrcode` | `curl /instances/1/qrcode -H "Authorization: Bearer $TOKEN"` |
| **Start Warming** | `POST /instances/{id}/warming/start` | `curl -X POST /instances/1/warming/start -H "Authorization: Bearer $TOKEN"` |
| **Stop Warming** | `POST /instances/{id}/warming/stop` | `curl -X POST /instances/1/warming/stop -H "Authorization: Bearer $TOKEN"` |
| **List Instances** | `GET /instances/` | `curl /instances/ -H "Authorization: Bearer $TOKEN"` |
| **Check Stats** | `GET /instances/{id}/stats` | `curl /instances/1/stats -H "Authorization: Bearer $TOKEN"` |
| **Webhook Event** | `POST /webhooks/evolution` | `curl -X POST /webhooks/evolution -d '{"event": "connection.update", "instance": "chip_01", "data": {"state": "open"}}'` |

**Key Files**:
- `backend/src/heater/main.py`: App entry point.
- `backend/src/heater/api/instances.py`: Instance management routes.
- `docker-compose.yml`: Service orchestration.

---

## Level 2 - Detailed Usage

### 1. Instance Management (`api/instances.py`)

The platform manages WhatsApp instances via the Evolution API.

- **Create**: `POST /instances/` - Creates an instance in Evolution API and a record in the local DB.
  - Payload:
    ```json
    {
      "name": "unique_name",
      "proxy_url": "http://user:pass@host:port" // Optional: Assign unique IP
    }
    ```
- **Connect**: `GET /instances/{id}/qrcode` - Retrieves the base64 QR code from Evolution API.
  - **Flow**: Create Instance -> Get QR -> Scan with WhatsApp Mobile App -> Status becomes `connected`.
- **Status**: Updated via Webhook (`api/webhooks.py`).
  - `connected`: Ready for warming.
  - `disconnected`: Needs reconnection.
  - `warming`: Currently active in the warming engine.

### 2. Warming Engine (`warming/`)

The core logic simulates human behavior.

- **Engine (`warming/engine.py`)**:
  - Runs per instance.
  - Selects a peer instance (another connected chip) based on **weighted randomness** (favors peers not spoken to recently).
  - Executes an activity: `private_message` (80%) or `reaction` (20%).
  - **Concurrency**: Uses row-level locking (`SELECT ... FOR UPDATE`) on the `Instance` table to prevent race conditions.

- **Behaviors (`warming/behaviors.py`)**:
  - `typing_delay(len)`: Calculates realistic typing time (approx 40 WPM +/- 30%).
  - `reaction_probability()`: 30% chance to react to a received message.
  - `random_emoji()`: Selects from a set of common reactions (👍, ❤️, 😂, etc.).

- **Content (`warming/content.py`)**:
  - Generates content for messages.
  - `greeting()`: "Oi, tudo bem?", "E aí?"
  - `casual_message()`: "Viu o jogo?", "Bora café?"
  - `audio_message()`: Returns path to pre-recorded audio files.

### 3. Scheduler (`scheduler.py`)

- **Frequency**: Runs every **1 minute**.
- **Job**: Iterates through all instances with `warming_enabled=True`.
- **Checks**:
  1. **Schedule**: Is current time within `schedule_start` and `schedule_end`?
  2. **Daily Limit**: Has `messages_today` exceeded `daily_limit`?
  3. **Delays**: (Implemented in `engine.py`) Checks `last_active_at` against `private_delay_min`.

### 4. Authentication (`api/auth.py`)

- **Method**: OAuth2 with Password Flow (Bearer Token).
- **Token**: JWT (HS256).
- **Endpoints**:
  - `POST /auth/register`: Create a new user account.
  - `POST /auth/token`: Login and receive access token.

### 5. Database Models (`models/`)

- **Instance (`models/instance.py`)**:
  - `name`: Unique identifier in Evolution API.
  - `status`: `connected`, `disconnected`.
  - `warming_enabled`: Boolean toggle.
  - `daily_limit`: Max messages per day (default 50).
  - `schedule_start`/`end`: "08:00" - "22:00".
  - `messages_today`: Counter reset daily (via external cron or logic).
  - `proxy_url`: Stores proxy configuration string.

- **Message (`models/message.py`)**:
  - Logs all actions.
  - `message_type`: `text`, `reaction`, `audio`.
  - `external_id`: ID from WhatsApp/Evolution (used for reactions).

---

## Level 3 - Patterns and Combinations

### 1. Full Warming Cycle

1.  **Connect Phase**:
    - User scans QR code for 5-10 chips.
    - Instances marked as `connected`.
2.  **Configuration Phase**:
    - Set `daily_limit` low (e.g., 20) for new chips.
    - Set `schedule` to business hours (08:00 - 18:00) to mimic human behavior.
3.  **Warming Phase**:
    - Enable `warming_enabled` on all chips.
    - **Peer Discovery**: Chips automatically find other `connected` & `warming_enabled` instances in the database.
    - **Interaction**:
        - Chip A sends "Oi, tudo bem?" to Chip B.
        - Chip B records the message.
        - Later, Chip B might react "👍" to Chip A's message.
4.  **Graduation Phase**:
    - After X days (e.g., 7 days), increase `daily_limit` incrementally (20 -> 50 -> 100).
    - Once "mature", the chip is ready for marketing campaigns.

### 2. Multi-Chip Peer Warming Topology

- **Mesh Network**: Every chip can talk to every other chip.
- **Selection Logic**: The engine prefers peers with the "oldest" last interaction time.
  - *Effect*: Ensures even distribution of conversations across the pool.
- **Isolation**: Messages are strictly peer-to-peer within the controlled environment.

### 3. Proxy Rotation per Instance

**Problem**: WhatsApp bans accounts associated with flagged IP addresses (e.g., datacenter IPs).
**Solution**:
- Assign a unique Residential or 4G Mobile Proxy to every instance via `proxy_url`.
- Evolution API routes all traffic for that instance through the specified proxy.
- **Pattern**:
  - Chip 1 -> Proxy A (Brazil Mobile) -> WhatsApp
  - Chip 2 -> Proxy B (Brazil Residential) -> WhatsApp
- **Result**: To WhatsApp, these look like distinct users on different networks.

### 4. Scaling Strategies

- **Vertical Scaling**: Increase `backend` and `evolution` resources.
  - *Bottleneck*: Evolution API instance memory usage (Chrome/Baileys instances).
- **Horizontal Scaling**:
  - Run multiple `evolution` containers behind a load balancer.
  - Run multiple `backend` workers (FastAPI) - stateless.
  - **Database**: PostgreSQL handles concurrency via row locking.

### 5. Integration with Zaptos (Conceptual)

*Zaptos is the target platform for marketing campaigns.*

- **Trigger**: When a chip reaches `messages_total` > Threshold (e.g., 500).
- **Action**:
    1.  `POST /instances/{id}/warming/stop` to freeze warming.
    2.  Export session data (Token/Auth) from Evolution API.
    3.  Import into Zaptos as a "Sender".
    4.  The chip graduates from "Warming Pool" to "Production Pool".

### 6. Monitoring Health

- **Dashboard (`frontend/`)**:
    - **Green**: Connected & Warming.
    - **Yellow**: Connected & Idle (Waiting for schedule/delay).
    - **Red**: Disconnected.
- **Metrics**:
    - `messages_today` vs `daily_limit`.
    - `last_active_at`: If > 2 hours during schedule, something is wrong.
