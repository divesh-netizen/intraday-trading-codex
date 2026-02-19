import httpx

from app.core.config import settings


async def send_telegram_alert(message: str):
    if not settings.telegram_token or not settings.telegram_chat_id:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage"
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(url, json={"chat_id": settings.telegram_chat_id, "text": message})
