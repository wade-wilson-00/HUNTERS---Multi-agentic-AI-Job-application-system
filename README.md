<div align="center">

```text
██   ██  ██   ██  ███   ██  ████████  ███████   ██████    ███████ 
██   ██  ██   ██  ████  ██     ██     ██        ██   ██   ██      
███████  ██   ██  ██ ██ ██     ██     █████     ██████    ███████ 
██   ██  ██   ██  ██  ████     ██     ██        ██   ██        ██ 
██   ██  ███████  ██   ███     ██     ███████   ██   ██   ███████ 
```

### *Your AI-Powered Career Operating System*

<br>

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-WebSockets-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.1-f55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-STT-FF9900?style=for-the-badge)](https://www.sarvam.ai/)
[![Rich](https://img.shields.io/badge/Rich-CLI_UI-4B0082?style=for-the-badge&logo=gnometerminal&logoColor=white)](https://github.com/Textualize/rich)

<br>

*A hyper-optimized, voice-enabled AI system that listens to you, understands your career goals, and autonomously hunts for job opportunities — like having J.A.R.V.I.S. as your personal career advisor.*

<br>

---

</div>

## 🎯 What is HUNTERS?

**HUNTERS** is an advanced multi-agentic AI career operating system — not a chatbot, not a wrapper, but a fully autonomous pipeline of specialized AI agents that **hunt jobs for you**.

You don't scroll job boards. You don't write cover letters. You don't track applications in spreadsheets. You just **talk**.

Think of it as **J.A.R.V.I.S. meets an elite recruitment agency**, except it works 24/7, never forgets your preferences, and actually submits applications on your behalf.

**The Vision:**
> *"Hunter, find AI Engineering internships in Bangalore, rank them against my profile, draft cover letters for the top 3, and apply to all of them."*

Hunter will listen, understand your intent, delegate tasks across a network of specialized AI agents — Scout, Resume Analyzer, Match, Apply, Outreach, Tracker — orchestrate their work through LangGraph, use MCP tools to interact with real-world systems (browsers, file systems, Notion, Gmail), and speak the results back to you in **real-time**. End-to-end. Fully automated.

---

## ⚡ Real-Time Voice Architecture (New!)

We recently rebuilt Hunter's voice pipeline from the ground up into a highly scalable asynchronous Client-Server architecture to achieve **zero-latency, conversational AI interactions**.

```text
      🎙 You Speak (Voice Mode) / ⌨️ You Type (Text Mode)
            │
            ▼
     ┌──────────────┐
     │ VAD Listener │  ← Silero VAD detects voice & locks out noise
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │  FastAPI WS  │  ← Streams audio bytes over WebSockets
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │  Sarvam STT  │  ← Ultra-fast Speech-to-Text inference
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │   Groq LLM   │  ← Llama 3.1 8B streams SSE text tokens back to client
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │Local Edge TTS│  ← Client chunks text & runs neural TTS locally for zero lag
     └──────┬───────┘
            │
            ▼
       🗣 You Hear Hunter (Real-time concurrent playback!)
```

### 🔥 Key Optimizations & Fixes
- **Client-Side Edge TTS:** TTS generation was moved from the server directly to the client. This cuts out an entire network hop, meaning Hunter starts speaking the very millisecond the first sentence is generated!
- **Asynchronous Concurrent Playback:** Utilizing pure `asyncio` and `miniaudio`, the audio stream buffers and plays chunks concurrently as they download, preventing deadlocks and buffering lag.
- **Groq LLM Acceleration:** Switched to Groq's high-speed inference for Llama 3.1, making the AI's "thought process" nearly instantaneous.
- **VAD Processing Lock:** The microphone now intelligently mutes itself (`is_processing`) while Hunter is processing and speaking, eliminating the dreaded "one-word mid-sentence reset" bug.
- **3D Pixel UI:** Built a gorgeous custom 3D drop-shadow CLI interface natively into Rich, replacing standard fonts.

---

## 🛠️ Tech Stack

<table>
<tr>
<td align="center" width="120">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="48" height="48" alt="Python" />
<br><strong>Python</strong>
<br><sub>3.12+</sub>
</td>
<td align="center" width="120">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" width="48" height="48" alt="FastAPI" />
<br><strong>FastAPI</strong>
<br><sub>WS Server</sub>
</td>
<td align="center" width="120">
<img src="https://avatars.githubusercontent.com/u/126733545?s=48&v=4" width="48" height="48" alt="LangGraph" />
<br><strong>LangGraph</strong>
<br><sub>Agent Orchestration</sub>
</td>
<td align="center" width="120">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlite/sqlite-original.svg" width="48" height="48" alt="SQLite" />
<br><strong>ChromaDB</strong>
<br><sub>Vector Memory</sub>
</td>
</tr>
<tr>
<td align="center" width="120">
<br>🚀
<br><strong>Groq</strong>
<br><sub>Llama 3.1 8B</sub>
</td>
<td align="center" width="120">
<br>🎙️
<br><strong>Sarvam AI</strong>
<br><sub>Ultra-fast STT</sub>
</td>
<td align="center" width="120">
<br>🗣️
<br><strong>Edge TTS</strong>
<br><sub>Streaming Neural TTS</sub>
</td>
<td align="center" width="120">
<br>💻
<br><strong>Rich</strong>
<br><sub>CLI UI</sub>
</td>
</tr>
</table>

---

## 📦 Project Structure

```
hunters/
├── app.py                  # Main CLI entry point (Voice/Text Client)
├── server/
│   ├── voice_server.py     # FastAPI WebSocket Server
│   └── sarvam_stt.py       # Sarvam AI STT client
│
├── agents/
│   ├── llm.py              # LLM inference setup (Groq)
│   ├── hunter.py           # Hunter Agent (Jarvis-style supervisor)
│   ├── scout.py            # 🔜 Job search & opportunity discovery
│   ├── resume_analyzer.py  # 🔜 Resume parsing & strength analysis
│   ├── match.py            # 🔜 Job-resume matching & ranking
│   ├── apply.py            # 🔜 Automated job application agent
│   ├── outreach.py         # 🔜 Recruiter outreach & cold emails
│   ├── tracker.py          # 🔜 Application status tracking
│   └── researcher.py       # 🔜 AI trends & market research
│
├── voice/
│   ├── vad_listener.py     # Silero VAD continuous voice detection
│   ├── stream_tts.py       # Sentence chunker & Edge TTS API
│   └── audio_stream.py     # miniaudio & async PyAudio playback
│
├── graph/                  # 🔜 LangGraph workflow definitions
├── memory/                 # 🔜 ChromaDB vector stores
├── tools/                  # 🔜 MCP tool integrations
├── mcp_servers/            # 🔜 MCP server configs (Browser, FS, Notion, Gmail)
├── prompts/                # 🔜 Agent system prompts library
├── templates/              # 🔜 Resume/cover letter generation templates
├── reports/                # 🔜 Agent-generated evidence reports
├── workspace/              # 🔜 Working directory for agents
├── tests/                  # 🔜 Unit & integration tests
│
├── requirements.txt
├── roadmap.md
├── system_architecure.md
└── .env                    # API keys (not committed)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- A microphone
- Groq API Key
- Sarvam AI API Key

### Installation

```bash
# Clone the repository
git clone https://github.com/wade-wilson-00/HUNTERS---Multi-agentic-AI-Job-application-system.git
cd HUNTERS---Multi-agentic-AI-Job-application-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
# Create a .env file with:
GROQ_API_KEY=your_groq_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here
```

### Run Hunter

```bash
# 1. Start the Voice WebSocket Server
python -m server.voice_server

# 2. Start the Client (in a new terminal)
python app.py
```

The app supports two modes:
- **Voice Mode**: Speak naturally. Hunter uses Silero VAD to know when you've stopped speaking and replies automatically.
- **Text Mode**: Use standard keyboard input if you prefer not to talk, while still getting voice responses.

---

## 📋 Development Progress

### ✅ Week 1 — Hunter Core (Voice Assistant) `COMPLETED`

The foundational voice-to-voice loop is fully operational.

| Feature | Status | Description |
|---------|--------|-------------|
| Voice Server | ✅ Done | FastAPI WebSocket server handling bi-directional audio/text streaming |
| Microphone Listener | ✅ Done | Fast voice activity detection using **Silero VAD** |
| Speech-to-Text | ✅ Done | Rapid cloud transcription using **Sarvam AI** |
| LLM Brain | ✅ Done | Meta Llama 3.1 (8B) via **Groq** with SSE streaming |
| Text-to-Speech | ✅ Done | Ultra-realistic, fast, streaming neural voice using **Edge TTS** |
| CLI Interface | ✅ Done | Beautiful dual-mode (Voice/Text) terminal UI with a **Custom 3D Pixel UI** |
| Zero-Latency Playback | ✅ Done | Client-side TTS with `asyncio` queueing for concurrent downloading & speaking |

---

### 🔨 Week 2 — Hunter Supervisor + LangGraph `IN PROGRESS`

Turning Hunter from a chatbot into a planner with intent detection and task delegation.

| Feature | Status | Description |
|---------|--------|-------------|
| LangGraph Integration | 🔜 Pending | Nodes, edges, state management, routing |
| HunterState | 🔜 Pending | Shared state object (goals, tasks, reports) |
| Intent Detection | 🔜 Pending | Parse natural language into structured intents |
| Planning Layer | 🔜 Pending | Generate multi-step task plans from goals |
| First LangGraph Workflow | 🔜 Pending | Hunter → Planner → Summary pipeline |

---

### 📌 Future Weeks `UPCOMING`
*Week 3: Scout, Resume & Match Agents*
*Week 4: MCP Real-World Tools (Browser, Notion, File System)*
*Week 5: Apply & Outreach Automation*
*Week 6: Fully Autonomous Mode*

---

<div align="center">

**Built with 🤍 and a dream of never manually applying to jobs again.**

*"Good evening, sir. Shall I begin the hunt?"* — Hunter 🏹

</div>
