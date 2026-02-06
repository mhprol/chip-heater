from datetime import datetime, time, timedelta
import asyncio
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, desc

from heater.evolution import EvolutionClient
from heater.models.instance import Instance
from heater.models.message import Message
from heater.warming.behaviors import HumanBehavior
from heater.warming.content import ContentGenerator

class WarmingEngine:
    def __init__(self, evolution: EvolutionClient, db: AsyncSession):
        self.evolution = evolution
        self.db = db

    def is_within_schedule(self, start_str: str, end_str: str) -> bool:
        now = datetime.now().time()
        start = datetime.strptime(start_str, "%H:%M").time()
        end = datetime.strptime(end_str, "%H:%M").time()

        if start <= end:
            return start <= now <= end
        else: # Crosses midnight
            return start <= now or now <= end

    async def _select_peer(self, instance: Instance, peers: list[Instance]) -> Instance:
        """
        Select a peer using weighted selection based on last interaction time.
        Peers not spoken to recently have higher weight.
        """
        if not peers:
            return None

        now = datetime.utcnow()
        weights = []

        for peer in peers:
            # Query last message timestamp between instance and peer
            stmt = select(Message.created_at).where(
                or_(
                    (Message.instance_id == instance.id) & (Message.peer_number == peer.phone_number),
                    (Message.instance_id == peer.id) & (Message.peer_number == instance.phone_number)
                )
            ).order_by(desc(Message.created_at)).limit(1)

            result = await self.db.execute(stmt)
            last_msg_time = result.scalars().first()

            if last_msg_time:
                # Time since last interaction in seconds
                delta = (now - last_msg_time).total_seconds()
                # Weight = delta (longer time = higher weight)
                # Add base weight to avoid 0
                weight = delta + 60
            else:
                # Never interacted: high weight (e.g. 30 days)
                weight = 3600 * 24 * 30

            weights.append(weight)

        # Select peer
        selected = random.choices(peers, weights=weights, k=1)[0]
        return selected

    async def run_warming_cycle(self, instance_id: int):
        """Execute one warming cycle for an instance"""
        # Concurrency: Lock the row
        result = await self.db.execute(select(Instance).where(Instance.id == instance_id).with_for_update())
        instance = result.scalars().first()

        if not instance or not instance.warming_enabled:
            return

        # Check if within allowed hours
        if not self.is_within_schedule(instance.schedule_start, instance.schedule_end):
            return

        # Check daily message limit
        if instance.messages_today >= instance.daily_limit:
            return

        # Check delay
        if instance.last_active_at:
            delta = datetime.utcnow() - instance.last_active_at
            if delta.total_seconds() < instance.private_delay_min:
                return

        # Get available peers (other connected instances)
        peers_result = await self.db.execute(
            select(Instance).where(
                Instance.id != instance_id,
                Instance.status == 'connected',
                Instance.warming_enabled == True
            )
        )
        peers = peers_result.scalars().all()

        if not peers:
            return

        # Pick a peer
        peer = await self._select_peer(instance, peers)

        # Decide activity type
        # tailored for MVP: mostly private messages
        activity = random.choices(
            ["private_message", "reaction"],
            weights=[0.8, 0.2]
        )[0]

        if activity == "private_message":
            await self.send_private_message(instance, peer)
        elif activity == "reaction":
            await self.send_reaction(instance, peer)

        # Update stats
        instance.messages_today += 1
        instance.messages_total += 1
        instance.last_active_at = datetime.utcnow()
        await self.db.commit()

    async def send_private_message(self, sender: Instance, receiver: Instance):
        """Send a private message with human-like behavior"""
        # Show typing indicator
        try:
            await self.evolution.set_presence(sender.name, "composing")
        except:
            pass

        # Generate content
        content = ContentGenerator.casual_message()

        # Wait realistic typing time
        await asyncio.sleep(await HumanBehavior.typing_delay(len(content)))

        external_id = None
        # Send message
        try:
            resp = await self.evolution.send_text(sender.name, receiver.phone_number, content)
            if isinstance(resp, dict):
                # Attempt to extract ID. Structure varies by version but usually in key.
                key = resp.get("key") or resp.get("data", {}).get("key", {})
                external_id = key.get("id")
        except Exception as e:
            print(f"Failed to send message: {e}")
            try:
                await self.evolution.set_presence(sender.name, "available")
            except:
                pass
            return

        # Clear presence
        try:
            await self.evolution.set_presence(sender.name, "available")
        except:
            pass

        # Log
        log_msg = Message(
            instance_id=sender.id,
            peer_number=receiver.phone_number,
            message_type="text",
            content=content,
            external_id=external_id
        )
        self.db.add(log_msg)
        await self.db.commit()

    async def send_reaction(self, sender: Instance, receiver: Instance):
        # Find a recent message to react to (limit 5 recent messages)
        # Priority: Message from peer to sender
        stmt = select(Message).where(
            Message.instance_id == receiver.id,
            Message.peer_number == sender.phone_number,
            Message.external_id != None
        ).order_by(desc(Message.created_at)).limit(5)

        result = await self.db.execute(stmt)
        messages = result.scalars().all()

        target_msg = None
        from_me = False

        if messages:
            target_msg = random.choice(messages)
            from_me = False
        else:
            # Fallback: React to our own message sent to peer
            stmt = select(Message).where(
                Message.instance_id == sender.id,
                Message.peer_number == receiver.phone_number,
                Message.external_id != None
            ).order_by(desc(Message.created_at)).limit(5)
            result = await self.db.execute(stmt)
            messages = result.scalars().all()
            if messages:
                target_msg = random.choice(messages)
                from_me = True

        if not target_msg:
            return

        reaction = random.choice(["👍", "❤️", "😂", "😮", "🙏"])

        key = {
            "remoteJid": f"{receiver.phone_number}@s.whatsapp.net",
            "fromMe": from_me,
            "id": target_msg.external_id
        }

        try:
            await self.evolution.send_reaction(sender.name, key, reaction)

            # Log the reaction
            log_msg = Message(
                instance_id=sender.id,
                peer_number=receiver.phone_number,
                message_type="reaction",
                content=reaction,
                external_id=None
            )
            self.db.add(log_msg)
            await self.db.commit()
        except Exception as e:
            print(f"Failed to send reaction: {e}")
