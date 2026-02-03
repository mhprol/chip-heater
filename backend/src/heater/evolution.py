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
