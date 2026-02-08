# Chip Heater 🔥

[📘 **AI Manual**](docs/AI-MANUAL.md)

WhatsApp chip maturing/warming platform — Prepares cold numbers for marketing campaigns by simulating organic human behavior.

## Project Overview

Chip Heater is a collaborative community where connected WhatsApp chips warm each other through natural interactions. The goal is to make cold numbers appear "organic" before using them for marketing campaigns, thus reducing the risk of bans.

**Key Features:**
- 💬 **Private Messages**: Chips send casual messages to each other.
- 👥 **Group Interactions**: Chips join shared groups and interact.
- 😀 **Reactions**: 30% chance to react to messages with emojis.
- 🎤 **Audio Messages**: Sends pre-recorded audio as PTT (voice notes).
- ⌨️ **Human Behavior**: Simulates typing indicators, reading delays, and presence.
- 🌐 **Proxy Support**: Assign unique IPs per instance to avoid flagging.

**Benchmark**: Inspired by [MaturaGo](https://maturago.com.br).

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/mhprol/chip-heater.git
   cd chip-heater
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (API keys, database creds, etc.)
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Access the Platform**
   - **Dashboard**: [http://localhost:3000](http://localhost:3000)
   - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Evolution API**: [http://localhost:8080](http://localhost:8080)

## Architecture

The system follows a microservices architecture orchestrated by Docker Compose:

| Service | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | FastAPI (Python) | Core logic, warming engine, scheduler, API. |
| **Frontend** | Next.js 14 + Tailwind | User interface for management and monitoring. |
| **Evolution API** | Node.js (Baileys) | WhatsApp connection handling (Open Source). |
| **Database** | PostgreSQL | Stores instances, messages, and configurations. |
| **Queue/Cache** | Redis | Caching and task queues. |

### Warming Engine Logic
- **Scheduler**: Runs every minute to check eligible instances.
- **Peer Discovery**: Finds other connected chips to interact with.
- **Behavior Simulation**:
  - Calculates typing time based on message length (approx. 40 WPM).
  - Adds random delays between actions.
  - Varies content (text, audio, reactions) to look natural.

## Configuration

Configuration is managed via environment variables (in `.env`) and per-instance settings in the database.

### Environment Variables (`.env`)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `EVOLUTION_URL` | Evolution API Base URL | `http://evolution:8080` |
| `EVOLUTION_API_KEY` | Key for Evolution API auth | `secret-api-key` |
| `JWT_SECRET` | Secret for frontend auth tokens | `change-me` |
| `NEXT_PUBLIC_API_URL` | API URL for frontend | `http://localhost:8000` |

### Warming Behavior Config (Per Instance)

- **Schedule**: Start/End hours (e.g., 08:00 - 22:00).
- **Daily Limit**: Max messages per day (start low, e.g., 20, and scale up).
- **Delays**:
  - `private_delay_min/max`: Seconds between private messages.
  - `group_delay_min/max`: Seconds between group messages.

## Instance Management

1. **Create Instance**: Use the dashboard or API to create a new instance record.
   - *Optional*: Provide a `proxy_url` (e.g., `http://user:pass@ip:port`) to isolate the connection.
2. **Connect**: Click "Connect" to generate a QR code. Scan it with the WhatsApp mobile app.
3. **Start Warming**: Enable "Warming" toggle. The chip will enter the pool.
4. **Monitor**: Watch the "Status" (Connected/Disconnected) and "Messages Today" count.

## CLI & API Guide

You can interact with the platform directly via HTTP requests. See [docs/AI-MANUAL.md](docs/AI-MANUAL.md) for detailed examples.

**Common Operations:**

- **List Instances**
  ```bash
  curl http://localhost:8000/instances/ \
    -H "Authorization: Bearer $TOKEN"
  ```

- **Start Warming**
  ```bash
  curl -X POST http://localhost:8000/instances/{id}/warming/start \
    -H "Authorization: Bearer $TOKEN"
  ```

- **Get QR Code**
  ```bash
  curl http://localhost:8000/instances/{id}/qrcode \
    -H "Authorization: Bearer $TOKEN"
  ```

## Monitoring & Debugging

- **Dashboard**: Real-time status of all chips. Green = Warming, Red = Disconnected.
- **Logs**:
  - Backend logs: `docker-compose logs -f backend`
  - Evolution logs: `docker-compose logs -f evolution`
- **Health Checks**:
  - Check `last_active_at` timestamp in API response. If > 2 hours during active schedule, the instance may be stuck.

## Scaling Strategies

### Multi-Chip Peer Warming
The system uses a **Mesh Network** topology where every chip can talk to every other chip. The engine prefers peers with the "oldest" last interaction time to ensure even distribution.

### Vertical & Horizontal Scaling
- **Evolution API**: This is the heaviest component (Headless Chrome/Baileys). Scale by running multiple Evolution containers behind a load balancer if managing > 100 chips.
- **Backend**: Stateless FastAPI workers can be scaled horizontally.
- **Database**: Uses row-level locking (`SELECT ... FOR UPDATE`) to safely handle concurrency across multiple workers.

## Integration with Zaptos

*Zaptos is the target platform for marketing campaigns.*

**Concept**:
1. Chip starts in **Chip Heater** pool with low limits.
2. Over 7-14 days, limits are increased (20 -> 50 -> 100 messages/day).
3. Once "mature" (e.g., > 500 total messages), the chip is:
   - Stopped in Chip Heater.
   - Session exported from Evolution API.
   - Imported into Zaptos as a "Sender" for active campaigns.

## Contributing

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

**Development**:
- Follow `AGENTS.md` guidelines.
- Use `pre-commit` hooks for linting.

## License

Distributed under the MIT License. See `LICENSE` for more information.
