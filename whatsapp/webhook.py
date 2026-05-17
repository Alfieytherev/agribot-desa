"""
AgriBot Desa - WhatsApp Webhook
FastAPI server to receive and reply to WhatsApp messages
Author: Alfieytherev
"""

import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from agent.main import process_message

load_dotenv()

app = FastAPI(title="AgriBot Desa - WhatsApp Webhook")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "agribot_verify_token")
WHATSAPP_API_URL = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"


# ── Webhook verification (required by Meta) ────────────────────────────────────
@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Meta requires this GET endpoint to verify webhook ownership.
    Set your Verify Token in .env and match it in Meta Developer Console.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[Webhook] Verification successful!")
        return PlainTextResponse(content=challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


# ── Receive WhatsApp messages ──────────────────────────────────────────────────
@app.post("/webhook")
async def receive_message(request: Request):
    """
    Receive incoming WhatsApp messages and reply with AI farming advice.
    """
    body = await request.json()

    try:
        # Parse WhatsApp Cloud API payload
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Skip if no messages (e.g. delivery receipts)
        if "messages" not in value:
            return {"status": "no_message"}

        message = value["messages"][0]
        user_phone = message["from"]       # farmer's WhatsApp number
        msg_type = message.get("type")

        # Handle text messages
        if msg_type == "text":
            user_text = message["text"]["body"]
            print(f"[AgriBot] Message from {user_phone}: {user_text}")

            # Get AI response
            ai_response = process_message(user_id=user_phone, message=user_text)

            # Send reply back to farmer
            await send_whatsapp_message(phone=user_phone, text=ai_response)

        # Handle image messages (for pest photo identification)
        elif msg_type == "image":
            await send_whatsapp_message(
                phone=user_phone,
                text=(
                    "📸 Foto diterima! Fitur identifikasi hama via foto sedang dalam pengembangan.\n\n"
                    "Sementara ini, coba deskripsikan gejala tanaman Anda dalam teks ya 🌾"
                )
            )

        else:
            await send_whatsapp_message(
                phone=user_phone,
                text="Maaf, saat ini saya hanya bisa memproses pesan teks. Ketik pertanyaan Anda 🌾"
            )

    except (KeyError, IndexError) as e:
        print(f"[AgriBot] Payload parse error: {e}")

    return {"status": "ok"}


# ── Send WhatsApp message ──────────────────────────────────────────────────────
async def send_whatsapp_message(phone: str, text: str) -> None:
    """Send a text message back to farmer via WhatsApp Cloud API."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"[AgriBot] WhatsApp send error: {response.text}")


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/")
async def health_check():
    return {
        "status": "AgriBot Desa is running 🌾",
        "version": "1.0.0",
    }


# ── Run server ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("whatsapp.webhook:app", host="0.0.0.0", port=8000, reload=True)
