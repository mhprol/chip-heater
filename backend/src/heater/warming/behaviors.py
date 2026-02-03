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
