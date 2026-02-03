# Chip Heater 🔥

WhatsApp chip maturing/warming platform — Prepares cold numbers for marketing campaigns by simulating organic human behavior.

## Concept

A collaborative community where connected WhatsApp chips warm each other through:
- 💬 Private messages
- 👥 Group interactions  
- 😀 Emoji reactions
- 🎤 Audio messages (PTT)
- 📸 Media sharing
- 📱 Story posting/viewing
- ⌨️ Typing indicators & presence

## Tech Stack

- **WhatsApp**: Evolution API (Baileys-based, open source)
- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: Next.js + Tailwind
- **Infrastructure**: Docker Compose

## Quick Start

```bash
# Clone
git clone https://github.com/mhprol/chip-heater.git
cd chip-heater

# Configure
cp .env.example .env
# Edit .env with your settings

# Start
docker-compose up -d

# Access
# Dashboard: http://localhost:3000
# API: http://localhost:8000
# Evolution: http://localhost:8080
```

## Features

- 🔌 Multi-instance management
- 📱 QR code connection
- ⚙️ Configurable warming schedules
- 📊 Real-time dashboard
- 🔄 Automatic peer-to-peer warming
- 🌐 Proxy support per instance

## Benchmark

Inspired by [MaturaGo](https://maturago.com.br) with enhancements.

## License

MIT
