"""
HUNTERS — Voice Server v3

Lightweight WebSocket server: handles STT (Sarvam AI) + LLM (Groq) only.
TTS runs on the client side to eliminate server-to-client audio latency.

Message Protocol (server → client):
  {"type": "status",      "text": "..."}         — status indicator update
  {"type": "stt_result",  "text": "..."}         — transcript from STT
  {"type": "llm_token",   "text": "..."}         — single LLM token (SSE-style)
  {"type": "llm_done"}                           — LLM stream complete
  {"type": "error",       "text": "..."}         — pipeline error

Message Protocol (client → server):
  {"type": "audio"}  then <raw WAV bytes>       — user's voice recording
"""

import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from server.sarvam_stt import SarvamSTT
from agents.hunter import HunterAgent

app = FastAPI()
stt_client = SarvamSTT()
hunter_agent = HunterAgent()


@app.websocket("/voice")
async def voice_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[Server] Client connected.")

    try:
        while True:
            # ── 1. Receive metadata + audio bytes ──────────────────
            msg_text = await websocket.receive_text()
            meta = json.loads(msg_text)

            if meta.get("type") != "audio":
                continue

            wav_bytes = await websocket.receive_bytes()
            print(f"[Server] Received {len(wav_bytes)} bytes of audio.")

            # ── 2. STT (Sarvam AI) ─────────────────────────────────
            await websocket.send_text(json.dumps({"type": "status", "text": "Transcribing..."}))
            transcript = await stt_client.transcribe(wav_bytes)

            if not transcript or not transcript.strip():
                print("[Server] Empty transcript, skipping.")
                await websocket.send_text(json.dumps({"type": "llm_done"}))
                continue

            print(f"[Server] Transcript: {transcript}")
            await websocket.send_text(json.dumps({"type": "stt_result", "text": transcript}))

            # ── 3. LLM Stream (Groq, SSE) ──────────────────────────
            await websocket.send_text(json.dumps({"type": "status", "text": "Thinking..."}))
            print("[Server] Streaming LLM tokens...")

            try:
                async for token in hunter_agent.respond_stream(transcript):
                    await websocket.send_text(json.dumps({"type": "llm_token", "text": token}))
            except Exception as llm_err:
                print(f"[Server] LLM error: {llm_err}")
                await websocket.send_text(json.dumps({"type": "error", "text": str(llm_err)}))
            finally:
                # Always signal end so client TTS pipeline can flush
                await websocket.send_text(json.dumps({"type": "llm_done"}))
                print("[Server] LLM done.")

    except WebSocketDisconnect:
        print("[Server] Client disconnected.")
    except Exception as e:
        print(f"[Server] Unexpected error: {e}")


if __name__ == "__main__":
    uvicorn.run("server.voice_server:app", host="127.0.0.1", port=8000, reload=False)
