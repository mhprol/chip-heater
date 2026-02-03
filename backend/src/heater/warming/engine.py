from datetime import datetime, time
import asyncio
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

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

    async def run_warming_cycle(self, instance_id: int):
        """Execute one warming cycle for an instance"""
        result = await self.db.execute(select(Instance).where(Instance.id == instance_id))
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
        # Assuming we can only chat with other instances in the DB for now
        # Also ensure they are 'connected' (status check omitted for brevity or need to check actual status)
        peers_result = await self.db.execute(
            select(Instance).where(
                Instance.id != instance_id,
                Instance.status == 'connected', # Assuming we update this status via webhook
                Instance.warming_enabled == True # Maybe we only warm with other warming instances
            )
        )
        peers = peers_result.scalars().all()

        if not peers:
            return

        # Pick a random peer
        peer = random.choice(peers)

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

        # Send message
        # Receiver number might need formatting (Evolution API expects number with country code)
        # Assuming phone_number is stored correctly or sender name is sufficient?
        # send_text(instance_name, number, text)
        try:
            await self.evolution.send_text(sender.name, receiver.phone_number, content)
        except Exception as e:
            print(f"Failed to send message: {e}")
            # Clear presence
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
            content=content
        )
        self.db.add(log_msg)
        await self.db.commit()

    async def send_reaction(self, sender: Instance, receiver: Instance):
        # Implementation for reaction requires message ID to react to.
        # This is complex without history.
        # For now, skip or pick a random recent message if we tracked it.
        pass
