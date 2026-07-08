# The Evolution of Hunter's Voice Pipeline

Over the course of development, we have significantly upgraded Hunter's voice pipeline to achieve human-like responsiveness. Here is a detailed breakdown of the 3 iterations of our architecture.

---

## 🟢 Version 1: The Legacy Synchronous Pipeline
*The initial prototype focused on getting a working proof-of-concept using basic Python libraries.*

### Architecture
- **Synchronous Loop:** A simple `while True` loop that blocked the thread at every step.
- **Microphone (Input):** Used `PyAudio` to record fixed-length audio chunks and saved them to disk as a `.wav` file.
- **STT:** Used the basic `SpeechRecognition` wrapper to parse the local `.wav` file.
- **LLM:** Sent the entire transcript to the LLM and waited for the full response before proceeding.
- **TTS:** Used `pyttsx3` (Windows SAPI5) for voice output.

### Limitations
- **High Latency:** Every step had to finish before the next could begin. You had to wait several seconds between speaking and hearing a response.
- **Robotic Voice:** `pyttsx3` relies on legacy Windows offline voices, which sound very unnatural.
- **No Interruptions:** Because `pyttsx3` blocked the main thread, the microphone was completely turned off while Hunter was speaking. You could not interrupt him.

---

## 🟡 Version 2: The Async Queue & Stream Pipeline
*The second iteration aimed to fix the "sluggish" latency and robotic voice by moving to asynchronous queues and better models.*

### Architecture
- **Async Workers:** Replaced the synchronous loop with `asyncio` tasks. 
- **Microphone (Input):** Kept `PyAudio` but implemented a manual Voice Activity Detection (VAD) energy threshold to detect when the user stopped speaking.
- **STT:** Upgraded to `faster-whisper` for highly accurate, fast local transcription.
- **LLM:** Implemented Server-Sent Events (SSE) / streaming generation. As soon as the LLM generated a few words, it pushed them forward.
- **TTS:** Upgraded to **Microsoft Edge TTS** for high-quality, neural, natural-sounding voices. 
- **The "TTS Worker" Fix:** We added a background queue (`tts_worker`). Instead of waiting for Edge TTS to finish speaking a sentence (which blocked the LLM stream), we offloaded synthesis to a background worker so the LLM could keep generating text uninterrupted.

### Limitations
- **The "Chunking" Problem:** Even though we were queuing sentences, Edge TTS still had to download entire `.mp3` chunks and play them sequentially. It was faster, but not instantaneous.
- **VAD Issues:** Manual energy thresholds for VAD were unreliable. Background noise could trigger the agent, or it would cut the user off too early.
- **Poor Interruptibility:** Trying to force `PyAudio` to stop playing an Edge TTS audio file midway through was notoriously buggy and difficult to manage.

---

## 🟣 Version 3: The LiveKit WebRTC Pipeline (Current)
*The final state-of-the-art iteration. We abandoned manual file handling and chunking in favor of true, continuous streaming.*

### Architecture
- **WebRTC Streaming:** The entire pipeline now lives inside a LiveKit `VoicePipelineAgent`.
- **Microphone (Input):** Audio is continuously streamed directly from the client (web or terminal) over a WebRTC track.
- **VAD:** Uses `livekit-plugins-silero`. This is a highly optimized neural network that runs at the edge. It perfectly filters out background noise and precisely identifies speech.
- **STT (Custom Plugin):** Silero passes continuous raw PCM audio frames in memory directly to our local `faster-whisper` engine via our custom plugin. **Zero file I/O operations**.
- **LLM (OpenAI Plugin):** We use LiveKit's OpenAI plugin, but we route it to HuggingFace (`meta-llama/Llama-3.1-8B-Instruct`). This gives us advanced tool-calling and context management natively, **for free**.
- **TTS (Custom Plugin):** We kept Edge TTS, but we now stream the HTTP chunks, decode them instantly to raw PCM using `miniaudio`, and push the raw frames directly back down the WebRTC track.

### Benefits Unlocked
- **Ultra-Low Latency:** Because audio is decoded and streamed as raw frames, playback begins the millisecond the first bytes are ready. No waiting for `.mp3` files to finish downloading.
- **Native Interruptibility:** The moment you start speaking, Silero VAD detects it instantly and cuts off the WebRTC TTS track. Hunter gracefully stops talking mid-sentence and listens to your new input.
- **Professional Stability:** We no longer manage fragile PyAudio streams, file locks (`WinError 32`), or manual concurrency loops. LiveKit handles the orchestration cleanly.
