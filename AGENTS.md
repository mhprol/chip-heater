# AGENTS.md — Chip Heater (WhatsApp Warming Platform)

## Project Overview

Build a WhatsApp chip maturing/warming platform that prepares cold numbers for marketing campaigns by simulating organic human behavior. Users connect their WhatsApp via QR code, and the platform orchestrates natural conversations between connected chips.

**Benchmark**: MaturaGo (maturago.com.br)
**Base**: Evolution API (open source, Baileys-based, Docker-ready)

## Core Concept

The platform works as a **collaborative community** where all connected chips warm each other:
- Chips send messages to each other (PV)
- Chips join shared groups and interact
- Simulate human behavior: typing indicators, reactions, read receipts, presence
- Gradual activity increase to avoid detection
- Goal: Make cold numbers appear "organic" before marketing use

## Architecture

```
chip-heater/
├── docker-compose.yml           # Full stack orchestration
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/
│       └── heater/
│           ├── __init__.py
│           ├── main.py              # FastAPI app
│           ├── config.py            # Settings
│           ├── database.py          # SQLAlchemy models
│           ├── evolution.py         # Evolution API client
│           ├── scheduler.py         # APScheduler for warming jobs
│           ├── warming/
│           │   ├── __init__.py
│           │   ├── engine.py        # Warming orchestration
│           │   ├── behaviors.py     # Human behavior simulation
│           │   ├── content.py       # Message content generation
│           │   └── groups.py        # Group management
│           ├── api/
│           │   ├── __init__.py
│           │   ├── auth.py          # JWT authentication
│           │   ├── instances.py     # WhatsApp instance management
│           │   ├── dashboard.py     # Stats and monitoring
│           │   └── webhooks.py      # Evolution API webhooks
│           └── models/
│               ├── __init__.py
│               ├── user.py
│               ├── instance.py
│               ├── message.py
│               └── warming_session.py
├── frontend/
│   ├── Dockerfile
│   └── src/                     # React/Next.js dashboard
│       ├── pages/
│       │   ├── login.tsx
│       │   ├── dashboard.tsx
│       │   ├── instances.tsx
│       │   └── settings.tsx
│       └── components/
│           ├── QRCodeScanner.tsx
│           ├── InstanceCard.tsx
│           ├── StatsChart.tsx
│           └── WarmingProgress.tsx
├── evolution/                   # Evolution API config
│   └── docker-compose.override.yml
└── docs/
    └── API.md
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Queue**: Redis + Celery (or APScheduler for simpler setup)
- **WhatsApp**: Evolution API (Docker container)
- **Auth**: JWT tokens

### Frontend
- **Framework**: Next.js 14 + React
- **UI**: Tailwind CSS + shadcn/ui
- **State**: React Query
- **Charts**: Recharts

### Infrastructure
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Traefik or Nginx
- **Storage**: Local or S3 for media

## Evolution API Integration

Evolution API provides the WhatsApp connectivity:

```python
# evolution.py
import httpx

class EvolutionClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"apikey": api_key}
        )
    
    async def create_instance(self, name: str) -> dict:
        return (await self.client.post("/instance/create", json={
            "instanceName": name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        })).json()
    
    async def get_qrcode(self, instance: str) -> str:
        resp = await self.client.get(f"/instance/connect/{instance}")
        return resp.json().get("qrcode", {}).get("base64")
    
    async def send_text(self, instance: str, number: str, text: str):
        return (await self.client.post(f"/message/sendText/{instance}", json={
            "number": number,
            "text": text
        })).json()
    
    async def send_audio(self, instance: str, number: str, audio_url: str):
        return (await self.client.post(f"/message/sendWhatsAppAudio/{instance}", json={
            "number": number,
            "audio": audio_url,
            "encoding": True  # Send as PTT (voice note)
        })).json()
    
    async def send_reaction(self, instance: str, key: dict, emoji: str):
        return (await self.client.post(f"/message/sendReaction/{instance}", json={
            "key": key,
            "reaction": emoji
        })).json()
    
    async def set_presence(self, instance: str, presence: str):
        # composing, recording, available, unavailable
        return (await self.client.post(f"/chat/updatePresence/{instance}", json={
            "presence": presence
        })).json()
```

## Warming Engine

### Behavior Simulation

```python
# warming/behaviors.py
import random
import asyncio

class HumanBehavior:
    """Simulate human-like WhatsApp behavior"""
    
    @staticmethod
    async def typing_delay(message_length: int) -> float:
        """Calculate realistic typing time based on message length"""
        # Average typing speed: 40 WPM = ~200 chars/min = ~3.3 chars/sec
        base_time = message_length / 3.3
        # Add human variance (+/- 30%)
        variance = random.uniform(0.7, 1.3)
        return base_time * variance
    
    @staticmethod
    async def reading_delay(message_length: int) -> float:
        """Time to 'read' a message before responding"""
        # Average reading speed: 250 WPM = ~1250 chars/min
        base_time = message_length / 20
        return max(1.0, base_time * random.uniform(0.8, 1.5))
    
    @staticmethod
    async def reaction_probability() -> bool:
        """30% chance to react to a message"""
        return random.random() < 0.30
    
    @staticmethod
    def random_emoji() -> str:
        """Pick a random reaction emoji"""
        emojis = ["👍", "❤️", "😂", "😮", "😢", "🙏", "🔥", "👏"]
        return random.choice(emojis)
    
    @staticmethod
    async def between_messages_delay() -> float:
        """Delay between sending messages in a conversation"""
        # 2-10 seconds between messages
        return random.uniform(2, 10)
    
    @staticmethod
    async def between_conversations_delay() -> float:
        """Delay between different conversations"""
        # 5-30 minutes between conversations
        return random.uniform(300, 1800)
```

### Content Generation

```python
# warming/content.py
import random

class ContentGenerator:
    """Generate varied content for warming"""
    
    GREETINGS = [
        "Oi, tudo bem?", "E aí, beleza?", "Opa!", "Fala!", 
        "Bom dia!", "Boa tarde!", "Boa noite!", "Olá!"
    ]
    
    CASUAL_MESSAGES = [
        "Viu o jogo ontem?", "Como tá o tempo aí?",
        "Trabalhando muito?", "Já almoçou?",
        "Que semana corrida!", "Finalmente sexta!",
        "Bora tomar um café?", "Saudade de vocês!"
    ]
    
    REACTIONS = ["👍", "❤️", "😂", "😮", "🔥", "👏", "🙌", "💯"]
    
    STICKERS = [
        # URLs to common sticker packs (or local files)
    ]
    
    MEMES = [
        # URLs to meme images
    ]
    
    @classmethod
    def greeting(cls) -> str:
        return random.choice(cls.GREETINGS)
    
    @classmethod
    def casual_message(cls) -> str:
        return random.choice(cls.CASUAL_MESSAGES)
    
    @classmethod
    def reaction(cls) -> str:
        return random.choice(cls.REACTIONS)
    
    @classmethod
    def audio_message(cls) -> str:
        """Return path to a random short audio clip"""
        # Pre-recorded casual audio messages
        audios = [
            "/assets/audio/oi.ogg",
            "/assets/audio/tudo_bem.ogg",
            "/assets/audio/beleza.ogg"
        ]
        return random.choice(audios)
```

### Warming Session

```python
# warming/engine.py
from datetime import datetime, time
import asyncio

class WarmingEngine:
    def __init__(self, evolution: EvolutionClient, db: Database):
        self.evolution = evolution
        self.db = db
    
    async def run_warming_cycle(self, instance_id: str):
        """Execute one warming cycle for an instance"""
        instance = await self.db.get_instance(instance_id)
        
        # Check if within allowed hours
        if not self.is_within_schedule(instance.schedule):
            return
        
        # Check daily message limit
        if instance.messages_today >= instance.daily_limit:
            return
        
        # Get available peers (other connected instances)
        peers = await self.db.get_available_peers(exclude=instance_id)
        
        if not peers:
            return
        
        # Pick a random peer
        peer = random.choice(peers)
        
        # Decide activity type
        activity = random.choices(
            ["private_message", "group_message", "reaction", "story_view"],
            weights=[0.5, 0.3, 0.15, 0.05]
        )[0]
        
        if activity == "private_message":
            await self.send_private_message(instance, peer)
        elif activity == "group_message":
            await self.send_group_message(instance)
        elif activity == "reaction":
            await self.send_reaction(instance, peer)
        elif activity == "story_view":
            await self.view_story(instance)
        
        # Update stats
        await self.db.increment_message_count(instance_id)
    
    async def send_private_message(self, sender, receiver):
        """Send a private message with human-like behavior"""
        # Show typing indicator
        await self.evolution.set_presence(sender.name, "composing")
        
        # Generate content
        content = ContentGenerator.casual_message()
        
        # Wait realistic typing time
        await asyncio.sleep(await HumanBehavior.typing_delay(len(content)))
        
        # Send message
        await self.evolution.send_text(sender.name, receiver.number, content)
        
        # Clear presence
        await self.evolution.set_presence(sender.name, "available")
        
        # Log
        await self.db.log_message(sender.id, receiver.id, "text", content)
```

## Database Models

```python
# models/instance.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, unique=True)  # Evolution instance name
    phone_number = Column(String)
    status = Column(String, default="disconnected")  # connected, disconnected, warming
    
    # Warming config
    warming_enabled = Column(Boolean, default=False)
    daily_limit = Column(Integer, default=50)
    private_delay_min = Column(Integer, default=300)   # seconds
    private_delay_max = Column(Integer, default=1800)
    group_delay_min = Column(Integer, default=600)
    group_delay_max = Column(Integer, default=3600)
    schedule_start = Column(String, default="08:00")
    schedule_end = Column(String, default="22:00")
    
    # Stats
    messages_today = Column(Integer, default=0)
    messages_total = Column(Integer, default=0)
    warming_started_at = Column(DateTime)
    
    # Proxy (optional)
    proxy_url = Column(String, nullable=True)
    
    user = relationship("User", back_populates="instances")
    messages = relationship("Message", back_populates="instance")
```

## API Endpoints

```python
# api/instances.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/instances", tags=["instances"])

@router.post("/")
async def create_instance(name: str, user = Depends(get_current_user)):
    """Create new WhatsApp instance"""
    instance = await evolution.create_instance(name)
    db_instance = await db.create_instance(user.id, name)
    return db_instance

@router.get("/{instance_id}/qrcode")
async def get_qrcode(instance_id: int, user = Depends(get_current_user)):
    """Get QR code for WhatsApp connection"""
    instance = await db.get_instance(instance_id)
    qr = await evolution.get_qrcode(instance.name)
    return {"qrcode": qr}

@router.post("/{instance_id}/warming/start")
async def start_warming(instance_id: int, user = Depends(get_current_user)):
    """Start warming for an instance"""
    await db.update_instance(instance_id, warming_enabled=True)
    return {"status": "warming started"}

@router.post("/{instance_id}/warming/stop")
async def stop_warming(instance_id: int, user = Depends(get_current_user)):
    """Stop warming for an instance"""
    await db.update_instance(instance_id, warming_enabled=False)
    return {"status": "warming stopped"}

@router.get("/{instance_id}/stats")
async def get_stats(instance_id: int, user = Depends(get_current_user)):
    """Get warming statistics"""
    stats = await db.get_instance_stats(instance_id)
    return stats
```

## Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  evolution:
    image: evoapicloud/evolution-api:latest
    ports:
      - "8080:8080"
    environment:
      - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
      - DATABASE_CONNECTION_URI=postgresql://postgres:password@postgres:5432/evolution
      - DATABASE_PROVIDER=postgresql
    depends_on:
      - postgres
      - redis
    volumes:
      - evolution_instances:/evolution/instances

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/heater
      - EVOLUTION_URL=http://evolution:8080
      - EVOLUTION_API_KEY=${EVOLUTION_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - evolution

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  evolution_instances:
  postgres_data:
  redis_data:
```

## Features Checklist

### Core (MVP)
- [ ] User auth (register, login, JWT)
- [ ] Instance management (create, connect via QR, disconnect)
- [ ] Evolution API integration
- [ ] Basic warming engine (private messages)
- [ ] Dashboard with stats

### Warming Features
- [ ] Private messages between chips
- [ ] Group participation and messaging
- [ ] Emoji reactions
- [ ] Audio messages (PTT)
- [ ] Media sharing (images, GIFs)
- [ ] Stickers
- [ ] Story/status posting
- [ ] Story viewing
- [ ] Typing indicators
- [ ] Read receipts
- [ ] Online/offline presence

### Configuration
- [ ] Custom delay ranges (private, group)
- [ ] Schedule (start/end hours)
- [ ] Daily message limits
- [ ] Proxy support per instance
- [ ] Content customization

### Dashboard
- [ ] Real-time connection status
- [ ] Messages sent/received counters
- [ ] Warming progress visualization
- [ ] Activity logs

## Priority Order

1. Docker setup with Evolution API
2. Backend skeleton (FastAPI + DB)
3. Instance management + QR connection
4. Basic warming engine (text messages)
5. Frontend dashboard
6. Advanced content (audio, images, reactions)
7. Groups support
8. Stories/status
9. Proxy support
10. Analytics and reporting

## Notes

- Use Evolution API's webhook system for real-time events
- Implement rate limiting to avoid WhatsApp detection
- Gradually increase activity over days (true "warming")
- Store media assets locally for faster access
- Consider multi-tenant architecture for SaaS deployment
