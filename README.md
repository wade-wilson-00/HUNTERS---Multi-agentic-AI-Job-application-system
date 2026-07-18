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
[![FastMCP](https://img.shields.io/badge/FastMCP-Tooling-blue?style=for-the-badge)](https://github.com/jlowin/fastmcp)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Loop-green?style=for-the-badge)](https://langchain.com)

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
     │ Hunter Graph │  ← LangGraph ReAct Loop (Planner ↔ Tools)
     │ (ChatGroq)   │  ← FastMCP tools: read_resume, search_web
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

## 🧠 Hunter's LangGraph Architecture (New!)

We've upgraded Hunter's brain from a simple LLM chat into a **ReAct (Reason + Act)** Agent using LangGraph. Hunter can now autonomously decide when to search the web, read your files, and execute tasks via MCP tools.

```mermaid
graph TD
    User([🗣️ User Voice Input]) --> Intent
    
    subgraph HunterState [LangGraph: HunterState Memory]
        Intent[1. Intent Node] --> Planner
        
        Planner[2. Planner Node <br/> Llama 3.1 8B] -- Tool Required --> ToolNode
        ToolNode[3. Tool Execution Node] -- Returns Data --> Planner
        
        Planner -- Text Ready --> Summary
        Summary[4. Summary Node <br/> Post-Processor]
    end
    
    subgraph FastMCPServer [Central FastMCP Server]
        ToolNode -. stdio .-> read_resume
        ToolNode -. stdio .-> search_web
    end
    
    Summary --> Out([🗣️ Voice Output])
    
    classDef llm fill:#f55036,stroke:#fff,stroke-width:2px,color:#fff;
    classDef state fill:#009688,stroke:#fff,stroke-width:2px,color:#fff;
    classDef mcp fill:#3776AB,stroke:#fff,stroke-width:2px,color:#fff;
    
    class Planner,Summary llm;
    class Intent,ToolNode state;
    class read_resume,search_web mcp;
```

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
<img src="https://raw.githubusercontent.com/langchain-ai/langchain/master/docs/static/img/langchain.png" width="48" height="48" alt="LangGraph" />
<br><strong>LangGraph</strong>
<br><sub>Agent Orchestration</sub>
</td>
<td align="center" width="120">
<img src="https://raw.githubusercontent.com/jlowin/fastmcp/main/docs/logo.png" onerror="this.src='https://avatars.githubusercontent.com/u/76800726?s=48&v=4'" width="48" height="48" alt="FastMCP" />
<br><strong>FastMCP</strong>
<br><sub>Stdio Tool Server</sub>
</td>
</tr>
<tr>
<td align="center" width="120">
<img src="https://groq.com/wp-content/uploads/2024/03/PBG-mark1-color.svg" width="48" height="48" alt="Groq" />
<br><strong>Groq</strong>
<br><sub>Llama 3.1 8B</sub>
</td>
<td align="center" width="120">
<img src="https://cdn.prod.website-files.com/6571a067edc1e95690b27b9a/6571a8f906f3630f57635697_sarvam-logo-dark.svg" onerror="this.src='https://avatars.githubusercontent.com/u/148766774?s=48&v=4'" width="48" height="48" alt="Sarvam AI" />
<br><strong>Sarvam AI</strong>
<br><sub>Ultra-fast STT</sub>
</td>
<td align="center" width="120">
<img src="https://upload.wikimedia.org/wikipedia/commons/9/98/Microsoft_Edge_logo_%282019%29.svg" width="48" height="48" alt="Microsoft Edge" />
<br><strong>Edge TTS</strong>
<br><sub>Streaming Neural TTS</sub>
</td>
<td align="center" width="120">
<img src="https://raw.githubusercontent.com/Textualize/rich/master/imgs/logo.svg" width="48" height="48" alt="Textualize Rich" />
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

### ✅ Week 2 — Hunter Supervisor + LangGraph `COMPLETED`

Turning Hunter from a chatbot into a dynamic ReAct planner with intent detection and tool delegation.

| Feature | Status | Description |
|---------|--------|-------------|
| FastMCP Server | ✅ Done | Centralized stdio server exposing filesystem and web tools. |
| Tool 1: read_resume | ✅ Done | Reads user profiles/resumes from PDF, DOCX, and MD files. |
| Tool 2: search_web | ✅ Done | Uses Tavily API to fetch live internet results and news. |
| LangGraph Core | ✅ Done | Replaced raw LLM streaming with a full `StateGraph` workflow. |
| HunterState | ✅ Done | TypedDict memory tracking message history and final responses. |
| Planner Node | ✅ Done | `ChatGroq` bound to MCP tools, handling reasoning and task planning. |
| Summary Node | ✅ Done | Post-processing node to translate raw markdown/data into conversational speech. |

---

### 📌 Future Weeks `UPCOMING`
*Week 3: Human-In-The-Loop (HITL) & Sub-Agent Orchestration (Scout, Match)*
*Week 4: MCP Advanced Real-World Tools (Browser, Notion, File System)*
*Week 5: Apply & Outreach Automation*
*Week 6: Fully Autonomous Mode*

---

<div align="center">

**Built with 🤍 and a dream of never manually applying to jobs again.**

*"Good evening, sir. Shall I begin the hunt?"* — Hunter 🏹

</div>
