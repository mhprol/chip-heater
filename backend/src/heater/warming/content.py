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
